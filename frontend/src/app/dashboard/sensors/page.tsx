"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Zap, Wifi, AlertTriangle, CheckCircle2, Wrench } from "lucide-react";

interface Sensor {
  id: string;
  type: "occupancy" | "gate" | "camera";
  location: string;
  status: "online" | "offline" | "maintenance";
  lastSeen: string;
}

export default function SensorsPage() {
  const [sensors, setSensors] = useState<Sensor[]>([
    { id: "S-001", type: "occupancy", location: "Downtown Garage - A-01", status: "online", lastSeen: "2 min ago" },
    { id: "S-002", type: "occupancy", location: "Downtown Garage - A-02", status: "online", lastSeen: "5 min ago" },
    { id: "S-003", type: "gate", location: "Downtown Garage - Entry", status: "online", lastSeen: "1 min ago" },
    { id: "S-004", type: "camera", location: "Downtown Garage - Entrance", status: "maintenance", lastSeen: "1 hour ago" },
    { id: "S-005", type: "occupancy", location: "City Center - X-01", status: "offline", lastSeen: "2 hours ago" },
  ]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "online": return "bg-green-500/20 text-green-400 border-green-500/30";
      case "offline": return "bg-red-500/20 text-red-400 border-red-500/30";
      case "maintenance": return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
      default: return "";
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Sensor & Device Monitoring</h1>
        <p className="text-slate-400">Monitor all IoT devices</p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-6">
            <p className="text-slate-400 text-sm mb-2">Online Devices</p>
            <p className="text-3xl font-bold text-green-400">3</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-6">
            <p className="text-slate-400 text-sm mb-2">Offline Devices</p>
            <p className="text-3xl font-bold text-red-400">1</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-6">
            <p className="text-slate-400 text-sm mb-2">Maintenance</p>
            <p className="text-3xl font-bold text-yellow-400">1</p>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-slate-800 border-slate-700">
        <CardContent className="p-6">
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="pb-3 text-slate-400 font-medium">Device ID</th>
                  <th className="pb-3 text-slate-400 font-medium">Type</th>
                  <th className="pb-3 text-slate-400 font-medium">Location</th>
                  <th className="pb-3 text-slate-400 font-medium">Status</th>
                  <th className="pb-3 text-slate-400 font-medium">Last Seen</th>
                </tr>
              </thead>
              <tbody>
                {sensors.map((sensor) => (
                  <tr key={sensor.id} className="border-b border-slate-700/50">
                    <td className="py-4 text-white font-medium">{sensor.id}</td>
                    <td className="py-4 text-slate-300">{sensor.type}</td>
                    <td className="py-4 text-slate-300">{sensor.location}</td>
                    <td className="py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 w-fit ${getStatusColor(sensor.status)}`}>
                        {sensor.status === "online" ? <CheckCircle2 className="h-3 w-3" /> :
                         sensor.status === "offline" ? <AlertTriangle className="h-3 w-3" /> :
                         <Wrench className="h-3 w-3" />}
                        {sensor.status}
                      </span>
                    </td>
                    <td className="py-4 text-slate-400">{sensor.lastSeen}</td>
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
