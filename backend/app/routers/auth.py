from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.crud.user import create_user, get_user_by_email
from app.schemas.user import UserCreate, UserResponse, UserProfileUpdate, UserPasswordChange
from app.core.security import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_password_hash
from app.api.deps import get_current_user
from app.models.user import User
import uuid
import os
import re
from fastapi import UploadFile, File

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    user = get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists."
        )
    return create_user(db, user_in)

@router.post("/login")
def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/profile", response_model=UserResponse)
def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if profile_data.email and profile_data.email != current_user.email:
        existing_user = get_user_by_email(db, email=profile_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email is already in use by another account.")
        current_user.email = profile_data.email
    
    if profile_data.full_name is not None:
        current_user.full_name = profile_data.full_name
        
    db.commit()
    db.refresh(current_user)
    return current_user

@router.put("/change-password")
def change_password(
    password_data: UserPasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(password_data.current_password, current_user.password):
        raise HTTPException(status_code=400, detail="Incorrect current password.")
    
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match.")
        
    if len(password_data.new_password) < 8 or not re.search(r'[A-Za-z]', password_data.new_password) or not re.search(r'[0-9]', password_data.new_password):
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long and contain both a letter and a number.")
        
    current_user.password = get_password_hash(password_data.new_password)
    db.commit()
    return {"message": "Password updated successfully"}

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_FILE_SIZE = 2 * 1024 * 1024 # 2MB

@router.post("/profile-image")
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ext = file.filename.split(".")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPG, PNG, and WEBP are allowed.")
        
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 2MB.")
        
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join("uploads", filename)
    
    with open(file_path, "wb") as f:
        f.write(content)
        
    current_user.profile_image = f"/uploads/{filename}"
    db.commit()
    db.refresh(current_user)
    
    return {"profile_image": current_user.profile_image}

