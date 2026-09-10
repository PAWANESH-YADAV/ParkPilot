"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Shield, AlertTriangle, Camera, CheckCircle, Clock, Eye } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const events = [
  { id: 1, type: "loitering", zone: "Zone A — Entry Gate", camera: "CAM-01", time: "14:32", resolved: false, severity: "medium", hasClip: true },
  { id: 2, type: "vandalism", zone: "Zone B — Level 2", camera: "CAM-05", time: "13:18", resolved: false, severity: "high", hasClip: true },
  { id: 3, type: "unauthorized", zone: "EV Charging Area", camera: "CAM-03", time: "12:05", resolved: true, severity: "high", hasClip: true },
  { id: 4, type: "loitering", zone: "Zone C — Stairwell", camera: "CAM-07", time: "11:44", resolved: true, severity: "low", hasClip: false },
  { id: 5, type: "accident", zone: "Zone A — Bay 12", camera: "CAM-02", time: "09:20", resolved: true, severity: "high", hasClip: true },
];

const cameras = [
  { id: "CAM-01", location: "Entry Gate", status: "online" },
  { id: "CAM-02", location: "Zone A — Level 1", status: "online" },
  { id: "CAM-03", location: "EV Area", status: "online" },
  { id: "CAM-04", location: "Zone B — Level 2", status: "offline" },
  { id: "CAM-05", location: "Zone B — Level 3", status: "online" },
  { id: "CAM-06", location: "Exit Gate", status: "online" },
  { id: "CAM-07", location: "Stairwell", status: "online" },
  { id: "CAM-08", location: "Rooftop", status: "fault" },
];

const severityConfig: Record<string, string> = {
  high: "text-red-400 bg-red-500/10 border-red-500/30",
  medium: "text-yellow-400 bg-yellow-500/10 border-yellow-500/30",
  low: "text-blue-400 bg-blue-500/10 border-blue-500/30",
};

const typeLabels: Record<string, string> = {
  loitering: "🚶 Loitering",
  vandalism: "⚠️ Vandalism",
  unauthorized: "🚫 Unauthorized",
  accident: "💥 Accident",
  other: "❓ Other",
};

export default function SurveillancePage() {
  const [resolvedMap, setResolvedMap] = useState<Record<number, boolean>>(
    Object.fromEntries(events.map((e) => [e.id, e.resolved]))
  );
  const [filter, setFilter] = useState("all");

  const toggleResolve = (id: number) => setResolvedMap((prev) => ({ ...prev, [id]: !prev[id] }));

  const unresolved = events.filter((e) => !resolvedMap[e.id]).length;
  const filtered = events.filter((e) => {
    if (filter === "unresolved") return !resolvedMap[e.id];
    if (filter === "high") return e.severity === "high";
    return true;
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Surveillance & Security</h1>
        <p className="text-slate-400">Module 3 — Activity monitoring, loitering detection, and alert management</p>
      </div>

      {/* Summary */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { label: "Unresolved Alerts", value: unresolved, color: "text-red-400", icon: <AlertTriangle className="h-5 w-5 text-red-400" /> },
          { label: "Total Events Today", value: events.length, color: "text-white", icon: <Shield className="h-5 w-5 text-blue-400" /> },
          { label: "Cameras Online", value: `${cameras.filter(c => c.status === "online").length}/${cameras.length}`, color: "text-green-400", icon: <Camera className="h-5 w-5 text-green-400" /> },
          { label: "Resolved Today", value: events.filter((e) => resolvedMap[e.id]).length, color: "text-slate-300", icon: <CheckCircle className="h-5 w-5 text-emerald-400" /> },
        ].map((s, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}>
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm text-slate-400">{s.label}</CardTitle>
                {s.icon}
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Events Feed */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">Security Events</h2>
            <div className="flex gap-2">
              {["all", "unresolved", "high"].map((f) => (
                <button key={f} onClick={() => setFilter(f)} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${filter === f ? "bg-blue-600 text-white" : "bg-slate-700 text-slate-400 hover:text-white"}`}>
                  {f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>
          </div>
          <div className="space-y-3">
            <AnimatePresence>
              {filtered.map((event) => {
                const isResolved = resolvedMap[event.id];
                return (
                  <motion.div key={event.id} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }}>
                    <Card className={`border transition-all ${isResolved ? "bg-slate-900 border-slate-800 opacity-60" : "bg-slate-800 border-slate-700"}`}>
                      <CardContent className="pt-4">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="text-white font-medium">{typeLabels[event.type]}</span>
                              <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${severityConfig[event.severity]}`}>
                                {event.severity.toUpperCase()}
                              </span>
                              {isResolved && <span className="text-xs text-green-400 flex items-center gap-1"><CheckCircle className="h-3 w-3" />Resolved</span>}
                            </div>
                            <p className="text-slate-400 text-sm mt-1">{event.zone}</p>
                            <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                              <span className="flex items-center gap-1"><Camera className="h-3 w-3" />{event.camera}</span>
                              <span className="flex items-center gap-1"><Clock className="h-3 w-3" />Today {event.time}</span>
                              {event.hasClip && <span className="flex items-center gap-1 text-blue-400"><Eye className="h-3 w-3" />Clip saved</span>}
                            </div>
                          </div>
                          <button
                            onClick={() => toggleResolve(event.id)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap ${isResolved ? "bg-slate-700 text-slate-400 hover:bg-slate-600" : "bg-green-600 text-white hover:bg-green-700"}`}
                          >
                            {isResolved ? "Reopen" : "Resolve"}
                          </button>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        </div>

        {/* Camera Grid */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-white">Camera Status</h2>
          <div className="grid grid-cols-2 gap-3">
            {cameras.map((cam) => (
              <div key={cam.id} className={`p-3 rounded-xl border transition-colors ${cam.status === "offline" ? "border-red-500/30 bg-red-500/5" : cam.status === "fault" ? "border-yellow-500/30 bg-yellow-500/5" : "border-slate-700 bg-slate-800"}`}>
                <div className="flex items-center gap-1.5 mb-1">
                  <span className={`w-2 h-2 rounded-full ${cam.status === "online" ? "bg-green-400" : cam.status === "fault" ? "bg-yellow-400" : "bg-red-400"}`} />
                  <span className="text-white text-xs font-bold">{cam.id}</span>
                </div>
                <p className="text-slate-500 text-xs">{cam.location}</p>
                <p className={`text-xs font-medium mt-1 ${cam.status === "online" ? "text-green-400" : cam.status === "fault" ? "text-yellow-400" : "text-red-400"}`}>
                  {cam.status.charAt(0).toUpperCase() + cam.status.slice(1)}
                </p>
              </div>
            ))}
          </div>

          {/* Event Breakdown */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader><CardTitle className="text-white text-sm">Event Breakdown</CardTitle></CardHeader>
            <CardContent>
              {Object.entries(typeLabels).slice(0, 4).map(([type, label]) => {
                const count = events.filter((e) => e.type === type).length;
                if (!count) return null;
                return (
                  <div key={type} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0">
                    <span className="text-slate-400 text-sm">{label}</span>
                    <span className="text-white font-bold text-sm">{count}</span>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
