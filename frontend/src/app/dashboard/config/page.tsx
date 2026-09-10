"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Settings, Shield, Bell, Database } from "lucide-react";

export default function ConfigPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">System Configuration</h1>
        <p className="text-slate-400">Manage application settings</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Settings className="h-5 w-5 text-blue-500" />
              General Settings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              "Site Name & Branding",
              "Time Zone Configuration",
              "Date & Time Format",
              "Language Settings",
            ].map((setting, idx) => (
              <div key={idx} className="flex justify-between items-center p-3 bg-slate-700/50 rounded-lg">
                <span className="text-white">{setting}</span>
                <Button variant="ghost" size="sm">Configure</Button>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Shield className="h-5 w-5 text-green-500" />
              Security Settings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              "Password Policy",
              "Two-Factor Authentication",
              "Session Timeout",
              "IP Whitelisting",
            ].map((setting, idx) => (
              <div key={idx} className="flex justify-between items-center p-3 bg-slate-700/50 rounded-lg">
                <span className="text-white">{setting}</span>
                <Button variant="ghost" size="sm">Configure</Button>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Bell className="h-5 w-5 text-yellow-500" />
              Notification Settings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              "Email Templates",
              "SMS Templates",
              "Push Notification Preferences",
              "Alert Thresholds",
            ].map((setting, idx) => (
              <div key={idx} className="flex justify-between items-center p-3 bg-slate-700/50 rounded-lg">
                <span className="text-white">{setting}</span>
                <Button variant="ghost" size="sm">Configure</Button>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Database className="h-5 w-5 text-purple-500" />
              Integration Settings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              "Payment Gateway Integration",
              "SMS API Configuration",
              "Email Service Setup",
              "Analytics Integration",
            ].map((setting, idx) => (
              <div key={idx} className="flex justify-between items-center p-3 bg-slate-700/50 rounded-lg">
                <span className="text-white">{setting}</span>
                <Button variant="ghost" size="sm">Configure</Button>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
