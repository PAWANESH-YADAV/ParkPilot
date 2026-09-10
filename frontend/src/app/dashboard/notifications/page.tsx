"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Bell, Send, Users, Mail } from "lucide-react";

export default function NotificationsPage() {
  const [notificationText, setNotificationText] = useState("");
  const [notificationType, setNotificationType] = useState("all");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Notification Management</h1>
        <p className="text-slate-400">Send announcements and manage notifications</p>
      </div>

      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">Send Broadcast</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-slate-300 text-sm">Recipients</label>
            <select className="w-full bg-slate-700 border border-slate-600 rounded-md px-3 py-2 text-white">
              <option value="all">All Users</option>
              <option value="active">Active Users Only</option>
              <option value="new">New Users</option>
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-slate-300 text-sm">Message</label>
            <textarea
              placeholder="Enter your message here..."
              value={notificationText}
              onChange={(e) => setNotificationText(e.target.value)}
              className="w-full h-32 bg-slate-700 border border-slate-600 rounded-md px-3 py-2 text-white placeholder:text-slate-500 resize-none"
            />
          </div>
          <div className="flex gap-3">
            <Button className="flex-1">
              <Bell className="h-4 w-4 mr-2" />
              Send as In-app Notification
            </Button>
            <Button variant="outline" className="flex-1">
              <Mail className="h-4 w-4 mr-2" />
              Send as Email
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">Notification History</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {[
            { date: "2024-12-20", message: "New parking lot opened at Waterfront!", sent: 142 },
            { date: "2024-12-18", message: "Holiday discount: 20% off on all bookings!", sent: 130 },
            { date: "2024-12-15", message: "System maintenance scheduled on Dec 25th", sent: 150 },
          ].map((item, idx) => (
            <div key={idx} className="p-4 bg-slate-700/50 rounded-lg">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-white font-medium">{item.message}</p>
                  <p className="text-slate-400 text-sm mt-1">{item.date}</p>
                </div>
                <span className="text-slate-400 text-sm">{item.sent} sent</span>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
