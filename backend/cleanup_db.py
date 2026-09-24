from app.database.database import SessionLocal
from app.models.risk import Risk
from app.models.prediction import Prediction
from app.models.recommendation import Recommendation
from sqlalchemy import func

db = SessionLocal()

print("Counting original risks...")
# Keep the oldest risk for each event_id
subq = db.query(
    Risk.event_id,
    func.min(Risk.id).label('min_id')
).group_by(Risk.event_id).subquery()

risks_to_keep = db.query(subq.c.min_id).all()
keep_ids = [r[0] for r in risks_to_keep]

print(f"Keeping {len(keep_ids)} risks. Deleting the rest...")

# Find all predictions and recommendations that belong to risks we are NOT keeping
bad_risks = db.query(Risk.id).filter(~Risk.id.in_(keep_ids)).all()
bad_risk_ids = [r[0] for r in bad_risks]

if bad_risk_ids:
    bad_preds = db.query(Prediction.id).filter(Prediction.risk_id.in_(bad_risk_ids)).all()
    bad_pred_ids = [p[0] for p in bad_preds]
    
    if bad_pred_ids:
        deleted_recs = db.query(Recommendation).filter(Recommendation.prediction_id.in_(bad_pred_ids)).delete(synchronize_session=False)
        print(f"Deleted {deleted_recs} duplicate recommendations.")
        
    deleted_preds = db.query(Prediction).filter(Prediction.risk_id.in_(bad_risk_ids)).delete(synchronize_session=False)
    print(f"Deleted {deleted_preds} duplicate predictions.")

    deleted_risks = db.query(Risk).filter(Risk.id.in_(bad_risk_ids)).delete(synchronize_session=False)
    print(f"Deleted {deleted_risks} duplicate risks.")

db.commit()
db.close()
print("Cleanup complete.")
