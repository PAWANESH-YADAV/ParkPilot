'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Bell,
  Lock,
  Globe,
  Palette,
  HelpCircle,
  LogOut,
  ChevronRight
} from 'lucide-react';

export default function SettingsPage() {
  const [notifications, setNotifications] = useState({
    push: true,
    email: true,
    sms: false,
  });

  const [darkMode, setDarkMode] = useState(true);

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Settings</h1>
        <p className="text-slate-400">Manage your app preferences</p>
      </div>

      {/* Notifications */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Bell className="h-5 w-5 text-blue-500" />
            Notifications
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {[
            { key: 'push', label: 'Push Notifications', desc: 'Receive alerts on your device' },
            { key: 'email', label: 'Email Notifications', desc: 'Get updates via email' },
            { key: 'sms', label: 'SMS Notifications', desc: 'Receive text messages' },
          ].map((item) => (
            <div key={item.key} className="flex justify-between items-center py-2">
              <div>
                <p className="text-white">{item.label}</p>
                <p className="text-slate-400 text-sm">{item.desc}</p>
              </div>
              <button
                onClick={() => setNotifications({
                  ...notifications,
                  [item.key]: !notifications[item.key as keyof typeof notifications]
                })}
                className={`w-12 h-6 rounded-full transition-colors ${
                  notifications[item.key as keyof typeof notifications] ? 'bg-blue-600' : 'bg-slate-600'
                }`}
              >
                <div className={`w-5 h-5 bg-white rounded-full m-0.5 transition-transform ${
                  notifications[item.key as keyof typeof notifications] ? 'translate-x-6' : ''
                }`} />
              </button>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Appearance */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Palette className="h-5 w-5 text-purple-500" />
            Appearance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex justify-between items-center py-2">
            <div>
              <p className="text-white">Dark Mode</p>
              <p className="text-slate-400 text-sm">Use dark theme</p>
            </div>
            <button
              onClick={() => setDarkMode(!darkMode)}
              className={`w-12 h-6 rounded-full transition-colors ${
                darkMode ? 'bg-blue-600' : 'bg-slate-600'
              }`}
            >
              <div className={`w-5 h-5 bg-white rounded-full m-0.5 transition-transform ${
                darkMode ? 'translate-x-6' : ''
              }`} />
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Account Settings */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Lock className="h-5 w-5 text-green-500" />
            Account
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {[
            { icon: Lock, label: 'Change Password', desc: 'Update your password' },
            { icon: Globe, label: 'Language', desc: 'Choose your preferred language' },
            { icon: HelpCircle, label: 'Help & Support', desc: 'Get help and contact support' },
          ].map((item, idx) => (
            <button key={idx} className="w-full flex justify-between items-center py-3 text-left hover:bg-slate-700 rounded px-2 -mx-2">
              <div className="flex items-center gap-3">
                <item.icon className="h-5 w-5 text-slate-400" />
                <div>
                  <p className="text-white">{item.label}</p>
                  <p className="text-slate-400 text-sm">{item.desc}</p>
                </div>
              </div>
              <ChevronRight className="h-5 w-5 text-slate-500" />
            </button>
          ))}
        </CardContent>
      </Card>

      {/* Danger Zone */}
      <Card className="bg-slate-800 border-red-500/30">
        <CardHeader>
          <CardTitle className="text-red-400">Danger Zone</CardTitle>
        </CardHeader>
        <CardContent>
          <Button variant="outline" className="border-red-500 text-red-500 hover:bg-red-500/10">
            <LogOut className="h-4 w-4 mr-2" />
            Log Out
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
