import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import api from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { UserCircle, Mail, Shield, CheckCircle2, AlertTriangle, Eye, EyeOff, Loader2, Calendar, ShieldCheck, User } from 'lucide-react';
import { format } from 'date-fns';

export default function Profile() {
  const { user, fetchUser } = useAuth();
  
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [email, setEmail] = useState(user?.email || '');
  
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false);
  const [profileMessage, setProfileMessage] = useState('');
  const [profileError, setProfileError] = useState('');

  const [isUpdatingPassword, setIsUpdatingPassword] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState('');
  const [passwordError, setPasswordError] = useState('');

  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    setProfileError('');
    setProfileMessage('');
    setIsUpdatingProfile(true);
    try {
      await api.put('/auth/profile', { full_name: fullName, email });
      await fetchUser();
      setProfileMessage('Profile updated successfully.');
    } catch (err) {
      setProfileError(err.response?.data?.detail || 'Failed to update profile. Please try again.');
    } finally {
      setIsUpdatingProfile(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordMessage('');
    
    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match.');
      return;
    }

    setIsUpdatingPassword(true);
    try {
      await api.put('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      setPasswordMessage('Password changed successfully.');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setPasswordError(err.response?.data?.detail || 'Failed to change password. Please check your current password.');
    } finally {
      setIsUpdatingPassword(false);
    }
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // Safe rendering values
  const safeFullName = user.full_name || 'Not provided';
  const safeUsername = user.username || 'Unavailable';
  const safeEmail = user.email || 'Unavailable';
  const safeRole = user.role || 'user';
  
  let formattedDate = 'Unavailable';
  if (user.created_at) {
    try {
      formattedDate = format(new Date(user.created_at), 'MMMM d, yyyy');
    } catch {
      formattedDate = 'Unknown date';
    }
  }

  // Fallback Initials
  const initials = (user.full_name || user.username || '?').substring(0, 2).toUpperCase();

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <UserCircle className="h-8 w-8 text-primary" />
            Profile Settings
          </h2>
          <p className="text-muted-foreground mt-1">Manage your account information, security settings, and platform preferences.</p>
        </div>
      </div>

      <div className="grid md:grid-cols-12 gap-6">
        {/* Profile Overview Sidebar */}
        <div className="md:col-span-4 space-y-6">
          <Card className="overflow-hidden">
            <CardHeader className="text-center pb-4 bg-muted/10 border-b border-border/50">
              <div className="mx-auto h-28 w-28 rounded-full bg-primary/10 flex items-center justify-center mb-5 overflow-hidden border-4 border-background shadow-md relative">
                {user.profile_image ? (
                  <img src={`http://localhost:8000${user.profile_image}`} alt="Profile" className="h-full w-full object-cover" />
                ) : (
                  <span className="text-3xl font-bold text-primary tracking-widest">{initials}</span>
                )}
              </div>
              <CardTitle className="text-xl">{safeFullName}</CardTitle>
              <CardDescription className="mt-1">@{safeUsername}</CardDescription>
              <div className="mt-4 flex justify-center">
                <Badge variant={safeRole.toLowerCase() === 'admin' ? 'default' : 'secondary'} className="uppercase tracking-wider px-3 py-1 text-xs">
                  {safeRole} Account
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-6 space-y-4">
              <div className="flex flex-col gap-1">
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5"><Mail className="h-3.5 w-3.5" /> Email Address</span>
                <span className="text-sm font-medium">{safeEmail}</span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5"><ShieldCheck className="h-3.5 w-3.5" /> Security Status</span>
                <span className="text-sm font-medium text-green-500 flex items-center gap-1.5"><CheckCircle2 className="h-4 w-4" /> Account Secured</span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5"><Calendar className="h-3.5 w-3.5" /> Member Since</span>
                <span className="text-sm font-medium text-muted-foreground">{formattedDate}</span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Forms Container */}
        <div className="md:col-span-8 space-y-6">
          
          {/* Account Information */}
          <Card>
            <CardHeader className="border-b border-border/50 pb-4 bg-muted/5">
              <CardTitle className="text-lg flex items-center gap-2"><User className="h-5 w-5 text-muted-foreground" /> Account Information</CardTitle>
              <CardDescription>Update your personal details and contact information.</CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              {profileError && (
                <div className="mb-6 p-3 bg-destructive/10 border border-destructive/20 text-destructive text-sm rounded-lg flex items-start gap-2">
                  <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" /> 
                  <p>{profileError}</p>
                </div>
              )}
              {profileMessage && (
                <div className="mb-6 p-3 bg-green-500/10 border border-green-500/20 text-green-600 dark:text-green-400 text-sm rounded-lg flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 mt-0.5 shrink-0" /> 
                  <p>{profileMessage}</p>
                </div>
              )}

              <form onSubmit={handleProfileUpdate} className="space-y-5">
                <div className="grid md:grid-cols-2 gap-5">
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Full Name</label>
                    <Input 
                      value={fullName} 
                      onChange={e => setFullName(e.target.value)} 
                      placeholder="Enter your full name"
                      className="bg-background/50"
                      disabled={isUpdatingProfile}
                    />
                    <p className="text-[10px] text-muted-foreground">Your real name may be visible to other analysts in your workspace.</p>
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Email Address</label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                      <Input 
                        type="email"
                        value={email} 
                        onChange={e => setEmail(e.target.value)} 
                        placeholder="name@company.com"
                        className="pl-9 bg-background/50"
                        disabled={isUpdatingProfile}
                      />
                    </div>
                  </div>
                </div>
                <div className="pt-2 border-t border-border/50 flex justify-end">
                  <Button type="submit" disabled={isUpdatingProfile || (!fullName && !email)}>
                    {isUpdatingProfile ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving...</> : 'Save Profile Changes'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Security Settings */}
          <Card>
            <CardHeader className="border-b border-border/50 pb-4 bg-muted/5">
              <CardTitle className="text-lg flex items-center gap-2"><Shield className="h-5 w-5 text-muted-foreground" /> Security Settings</CardTitle>
              <CardDescription>Update your authentication credentials securely.</CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              {passwordError && (
                <div className="mb-6 p-3 bg-destructive/10 border border-destructive/20 text-destructive text-sm rounded-lg flex items-start gap-2">
                  <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" /> 
                  <p>{passwordError}</p>
                </div>
              )}
              {passwordMessage && (
                <div className="mb-6 p-3 bg-green-500/10 border border-green-500/20 text-green-600 dark:text-green-400 text-sm rounded-lg flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 mt-0.5 shrink-0" /> 
                  <p>{passwordMessage}</p>
                </div>
              )}

              <form onSubmit={handlePasswordChange} className="space-y-5">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Current Password</label>
                  <div className="relative max-w-md">
                    <Shield className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input 
                      type={showCurrentPassword ? "text" : "password"}
                      value={currentPassword} 
                      onChange={e => setCurrentPassword(e.target.value)} 
                      placeholder="Enter current password"
                      className="pl-9 pr-10 bg-background/50"
                      required
                      disabled={isUpdatingPassword}
                    />
                    <button 
                      type="button" 
                      onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                      className="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground transition-colors focus:outline-none"
                    >
                      {showCurrentPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>
                
                <div className="grid md:grid-cols-2 gap-5 pt-2">
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">New Password</label>
                    <div className="relative">
                      <Input 
                        type={showNewPassword ? "text" : "password"}
                        value={newPassword} 
                        onChange={e => setNewPassword(e.target.value)} 
                        placeholder="Create new password"
                        className="pr-10 bg-background/50"
                        required
                        disabled={isUpdatingPassword}
                      />
                      <button 
                        type="button" 
                        onClick={() => setShowNewPassword(!showNewPassword)}
                        className="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground transition-colors focus:outline-none"
                      >
                        {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Confirm New Password</label>
                    <div className="relative">
                      <Input 
                        type={showConfirmPassword ? "text" : "password"}
                        value={confirmPassword} 
                        onChange={e => setConfirmPassword(e.target.value)} 
                        placeholder="Confirm new password"
                        className="pr-10 bg-background/50"
                        required
                        disabled={isUpdatingPassword}
                      />
                      <button 
                        type="button" 
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground transition-colors focus:outline-none"
                      >
                        {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>
                </div>
                
                <div className="pt-4 border-t border-border/50 flex justify-end">
                  <Button type="submit" variant="secondary" disabled={isUpdatingPassword || !currentPassword || !newPassword || !confirmPassword}>
                    {isUpdatingPassword ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Updating...</> : 'Update Security Credentials'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
          
        </div>
      </div>
    </div>
  );
}
