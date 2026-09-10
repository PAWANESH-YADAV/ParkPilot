'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  User,
  Mail,
  Phone,
  MapPin,
  Edit2,
  Save
} from 'lucide-react';
import { useAuth } from '@/lib/auth-context';

export default function ProfilePage() {
  const { user } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [profile, setProfile] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    address: '',
  });

  useEffect(() => {
    if (user) {
      setProfile({
        firstName: user.firstName,
        lastName: user.lastName,
        email: user.email,
        phone: user.phone,
        address: '', // Address not in initial user, but keep for UI
      });
    }
  }, [user]);

  if (!user) return null;

  const getInitials = () => {
    return `${user.firstName[0]}${user.lastName[0]}`.toUpperCase();
  };

  const handleSave = () => {
    // Update in localStorage
    const users = JSON.parse(localStorage.getItem('parkpilot_users') || '[]');
    const updatedUsers = users.map((u: any) => {
      if (u.id === user.id) {
        return { ...u, ...profile };
      }
      return u;
    });
    localStorage.setItem('parkpilot_users', JSON.stringify(updatedUsers));

    // Update current user in state
    const { password: _, ...updatedUser } = updatedUsers.find((u: any) => u.id === user.id);
    localStorage.setItem('parkpilot_user', JSON.stringify(updatedUser));
    setIsEditing(false);
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">My Profile</h1>
          <p className="text-slate-400">Manage your personal information</p>
        </div>
        <Button onClick={isEditing ? handleSave : () => setIsEditing(true)}>
          {isEditing ? (
            <>
              <Save className="h-4 w-4 mr-2" />
              Save Changes
            </>
          ) : (
            <>
              <Edit2 className="h-4 w-4 mr-2" />
              Edit Profile
            </>
          )}
        </Button>
      </div>

      {/* Profile Card */}
      <Card className="bg-slate-800 border-slate-700">
        <CardContent className="p-8">
          <div className="flex flex-col md:flex-row gap-8 items-center md:items-start">
            {/* Avatar */}
            <div className="w-32 h-32 bg-blue-600 rounded-full flex items-center justify-center">
              <span className="text-4xl font-bold text-white">{getInitials()}</span>
            </div>

            {/* Info */}
            <div className="flex-1 space-y-4 w-full">
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-slate-400 text-sm">First Name</label>
                  {isEditing ? (
                    <Input
                      value={profile.firstName}
                      onChange={(e) => setProfile({...profile, firstName: e.target.value})}
                      className="bg-slate-700 border-slate-600 text-white"
                    />
                  ) : (
                    <p className="text-white font-medium">{profile.firstName}</p>
                  )}
                </div>
                <div className="space-y-1">
                  <label className="text-slate-400 text-sm">Last Name</label>
                  {isEditing ? (
                    <Input
                      value={profile.lastName}
                      onChange={(e) => setProfile({...profile, lastName: e.target.value})}
                      className="bg-slate-700 border-slate-600 text-white"
                    />
                  ) : (
                    <p className="text-white font-medium">{profile.lastName}</p>
                  )}
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 text-sm flex items-center gap-2">
                  <Mail className="h-4 w-4" />
                  Email
                </label>
                {isEditing ? (
                  <Input
                    type="email"
                    value={profile.email}
                    onChange={(e) => setProfile({...profile, email: e.target.value})}
                    className="bg-slate-700 border-slate-600 text-white"
                  />
                ) : (
                  <p className="text-white font-medium">{profile.email}</p>
                )}
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 text-sm flex items-center gap-2">
                  <Phone className="h-4 w-4" />
                  Phone
                </label>
                {isEditing ? (
                  <Input
                    value={profile.phone}
                    onChange={(e) => setProfile({...profile, phone: e.target.value})}
                    className="bg-slate-700 border-slate-600 text-white"
                  />
                ) : (
                  <p className="text-white font-medium">{profile.phone}</p>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
