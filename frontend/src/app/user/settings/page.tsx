'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Bell,
  Lock,
  Globe,
  HelpCircle,
  LogOut,
  ChevronRight,
} from 'lucide-react';

export default function SettingsPage() {
  const [notifications, setNotifications] = useState({
    push: true,
    email: true,
    sms: false,
  });

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-3xl font-bold mb-2 text-slate-900 dark:text-white">Settings</h1>
        <p className="text-slate-500 dark:text-slate-400">Manage your app preferences</p>
      </div>

      {/* Notifications */}
      <Card className="bg-white dark:bg-slate-850 dark:bg-slate-800/90 border-slate-200 dark:border-slate-700">
        <CardHeader>
          <CardTitle className="text-slate-900 dark:text-white flex items-center gap-2">
            <Bell className="h-5 w-5 text-blue-600 dark:text-blue-500" />
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
                <p className="text-slate-900 dark:text-white font-medium text-sm">{item.label}</p>
                <p className="text-slate-500 dark:text-slate-400 text-xs">{item.desc}</p>
              </div>
              <button
                type="button"
                onClick={() => setNotifications({
                  ...notifications,
                  [item.key]: !notifications[item.key as keyof typeof notifications]
                })}
                className={`relative w-11 h-6 rounded-full transition-colors cursor-pointer ${
                  notifications[item.key as keyof typeof notifications] ? 'bg-blue-600' : 'bg-slate-300 dark:bg-slate-700'
                }`}
              >
                <span
                  className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow-xs transition-all ${
                    notifications[item.key as keyof typeof notifications] ? 'left-5.5' : 'left-0.5'
                  }`}
                />
              </button>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Account Settings */}
      <Card className="bg-white dark:bg-slate-850 dark:bg-slate-800/90 border-slate-200 dark:border-slate-700">
        <CardHeader>
          <CardTitle className="text-slate-900 dark:text-white flex items-center gap-2">
            <Lock className="h-5 w-5 text-emerald-600 dark:text-emerald-500" />
            Account
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-1">
          {[
            { icon: Lock, label: 'Change Password', desc: 'Update your password' },
            { icon: Globe, label: 'Language', desc: 'Choose your preferred language' },
            { icon: HelpCircle, label: 'Help & Support', desc: 'Get help and contact support' },
          ].map((item, idx) => (
            <button key={idx} className="w-full flex justify-between items-center py-3 text-left rounded-xl px-3 -mx-3 transition-colors hover:bg-slate-100 dark:hover:bg-slate-800">
              <div className="flex items-center gap-3">
                <item.icon className="h-5 w-5 text-slate-500 dark:text-slate-400" />
                <div>
                  <p className="text-slate-900 dark:text-white font-medium text-sm">{item.label}</p>
                  <p className="text-slate-500 dark:text-slate-400 text-xs">{item.desc}</p>
                </div>
              </div>
              <ChevronRight className="h-5 w-5 text-slate-400" />
            </button>
          ))}
        </CardContent>
      </Card>

      {/* Danger Zone */}
      <Card className="bg-white dark:bg-slate-850 dark:bg-slate-800/90 border-red-200 dark:border-red-500/30">
        <CardHeader>
          <CardTitle className="text-red-600 dark:text-red-400">Danger Zone</CardTitle>
        </CardHeader>
        <CardContent>
          <Button variant="outline" className="border-red-300 dark:border-red-500 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10">
            <LogOut className="h-4 w-4 mr-2" />
            Sign out
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
