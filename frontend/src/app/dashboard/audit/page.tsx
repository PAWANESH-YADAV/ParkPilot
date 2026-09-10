"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Shield, Eye, User, Clock } from "lucide-react";

interface LogEntry {
  id: string;
  timestamp: string;
  user: string;
  action: string;
  ip: string;
  status: "success" | "failure";
}

export default function AuditPage() {
  const logs: LogEntry[] = [
    { id: "1", timestamp: "2024-12-20 14:30:00", user: "Admin", action: "Login", ip: "192.168.1.1", status: "success" },
    { id: "2", timestamp: "2024-12-20 14:25:00", user: "John Doe", action: "Update Profile", ip: "10.0.0.5", status: "success" },
    { id: "3", timestamp: "2024-12-20 14:20:00", user: "Unknown", action: "Login Attempt", ip: "203.0.113.50", status: "failure" },
    { id: "4", timestamp: "2024-12-20 14:15:00", user: "Admin", action: "Modify Pricing", ip: "192.168.1.1", status: "success" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Audit & Security</h1>
        <p className="text-slate-400">View system logs and security events</p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-6">
            <p className="text-slate-400 text-sm mb-2">Total Events</p>
            <p className="text-3xl font-bold text-white">1,245</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-6">
            <p className="text-slate-400 text-sm mb-2">Successful Actions</p>
            <p className="text-3xl font-bold text-green-400">1,230</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-6">
            <p className="text-slate-400 text-sm mb-2">Security Alerts</p>
            <p className="text-3xl font-bold text-red-400">15</p>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-slate-800 border-slate-700">
        <CardContent className="p-6">
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="pb-3 text-slate-400 font-medium">Timestamp</th>
                  <th className="pb-3 text-slate-400 font-medium">User</th>
                  <th className="pb-3 text-slate-400 font-medium">Action</th>
                  <th className="pb-3 text-slate-400 font-medium">IP Address</th>
                  <th className="pb-3 text-slate-400 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} className="border-b border-slate-700/50">
                    <td className="py-4 text-slate-300">{log.timestamp}</td>
                    <td className="py-4 text-white">{log.user}</td>
                    <td className="py-4 text-slate-300">{log.action}</td>
                    <td className="py-4 text-slate-400 font-mono">{log.ip}</td>
                    <td className="py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        log.status === "success" ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
                      }`}>
                        {log.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
