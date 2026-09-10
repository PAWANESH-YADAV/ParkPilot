"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Zap, Activity, Clock, DollarSign, Plus, ChevronRight, AlertCircle } from "lucide-react";
import { motion } from "framer-motion";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const chargers = [
  { id: "EV-01", location: "Level 1 — Bay A", type: "CCS2 (50kW)", status: "available", rate: 12, kwh: 0, fee: 0, queue: 0 },
  { id: "EV-02", location: "Level 1 — Bay B", type: "Type 2 (22kW)", status: "occupied", rate: 8, kwh: 18.5, fee: 148, queue: 2, plate: "MH12AB3456", minutes: 45 },
  { id: "EV-03", location: "Level 2 — Bay A", type: "CCS2 (50kW)", status: "available", rate: 12, kwh: 0, fee: 0, queue: 0 },
  { id: "EV-04", location: "ParkPilot North", type: "Type 1 (7.4kW)", status: "fault", rate: 6, kwh: 0, fee: 0, queue: 0 },
  { id: "EV-05", location: "Level 2 — Bay B", type: "Type 2 (22kW)", status: "occupied", rate: 8, kwh: 9.2, fee: 73.6, queue: 1, plate: "DL9CA5678", minutes: 22 },
];

const sessionData = [
  { day: "Mon", sessions: 12, kwh: 180 },
  { day: "Tue", sessions: 18, kwh: 270 },
  { day: "Wed", sessions: 15, kwh: 225 },
  { day: "Thu", sessions: 22, kwh: 330 },
  { day: "Fri", sessions: 28, kwh: 420 },
  { day: "Sat", sessions: 35, kwh: 525 },
  { day: "Sun", sessions: 20, kwh: 300 },
];

const statusConfig: Record<string, { color: string; label: string; dot: string }> = {
  available: { color: "text-green-400", label: "Available", dot: "bg-green-400" },
  occupied: { color: "text-yellow-400", label: "Occupied", dot: "bg-yellow-400" },
  fault: { color: "text-red-400", label: "Fault", dot: "bg-red-400" },
};

export default function EVChargingPage() {
  const [activeCharger, setActiveCharger] = useState<string | null>(null);

  const available = chargers.filter((c) => c.status === "available").length;
  const occupied = chargers.filter((c) => c.status === "occupied").length;
  const totalKwh = chargers.reduce((s, c) => s + c.kwh, 0);
  const totalRevenue = chargers.reduce((s, c) => s + c.fee, 0);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">EV Charging Management</h1>
        <p className="text-slate-400">Module 6 — Real-time charger monitoring, sessions, and smart queue</p>
      </div>

      {/* Stats */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { title: "Available Chargers", value: available, icon: <Zap className="h-5 w-5 text-green-400" />, color: "text-green-400" },
          { title: "Active Sessions", value: occupied, icon: <Activity className="h-5 w-5 text-yellow-400" />, color: "text-yellow-400" },
          { title: "kWh Dispensed Today", value: `${totalKwh.toFixed(1)} kWh`, icon: <Zap className="h-5 w-5 text-blue-400" />, color: "text-blue-400" },
          { title: "Revenue Today", value: `₹${totalRevenue.toFixed(0)}`, icon: <DollarSign className="h-5 w-5 text-purple-400" />, color: "text-purple-400" },
        ].map((stat, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}>
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-slate-400">{stat.title}</CardTitle>
                {stat.icon}
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Charger Cards + Chart */}
      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-lg font-semibold text-white">Charging Stations</h2>
          {chargers.map((charger, i) => {
            const cfg = statusConfig[charger.status];
            return (
              <motion.div key={charger.id} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.08 }}>
                <Card className="bg-slate-800 border-slate-700 hover:border-slate-500 transition-colors cursor-pointer" onClick={() => setActiveCharger(activeCharger === charger.id ? null : charger.id)}>
                  <CardContent className="pt-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${charger.status === "fault" ? "bg-red-500/10" : charger.status === "occupied" ? "bg-yellow-500/10" : "bg-green-500/10"}`}>
                          <Zap className={`h-5 w-5 ${cfg.color}`} />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-white">{charger.id}</span>
                            <span className={`text-xs font-medium ${cfg.color} flex items-center gap-1`}>
                              <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
                              {cfg.label}
                            </span>
                          </div>
                          <p className="text-slate-400 text-sm">{charger.location}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-slate-300 text-sm font-medium">{charger.type}</div>
                        <div className="text-blue-400 text-sm">₹{charger.rate}/kWh</div>
                      </div>
                    </div>

                    {charger.status === "occupied" && activeCharger === charger.id && (
                      <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} className="mt-4 pt-4 border-t border-slate-700 grid grid-cols-3 gap-4">
                        <div className="text-center">
                          <div className="text-yellow-400 font-bold text-lg">{charger.kwh} kWh</div>
                          <div className="text-slate-500 text-xs">Energy Used</div>
                        </div>
                        <div className="text-center">
                          <div className="text-white font-bold text-lg">{charger.minutes} min</div>
                          <div className="text-slate-500 text-xs">Duration</div>
                        </div>
                        <div className="text-center">
                          <div className="text-green-400 font-bold text-lg">₹{charger.fee}</div>
                          <div className="text-slate-500 text-xs">Current Fee</div>
                        </div>
                        {charger.queue > 0 && (
                          <div className="col-span-3 flex items-center gap-2 text-slate-400 text-sm">
                            <Clock className="h-4 w-4" />
                            {charger.queue} vehicle(s) in queue — est. {charger.queue * 20} min wait
                          </div>
                        )}
                      </motion.div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </div>

        {/* Weekly Chart */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-white">Weekly Sessions</h2>
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="pt-4">
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={sessionData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="day" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
                    <Tooltip contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155" }} labelStyle={{ color: "#f1f5f9" }} />
                    <Bar dataKey="sessions" fill="#10b981" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Queue Management */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white text-sm">EV Queue</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {[{ plate: "KA05MN9012", type: "CCS2", wait: "20 min", pos: 1 }, { plate: "MH02PQ3456", type: "Type 2", wait: "40 min", pos: 2 }, { plate: "TN09RS7890", type: "Type 2", wait: "20 min", pos: 3 }].map((q) => (
                  <div key={q.pos} className="flex items-center justify-between py-2 border-b border-slate-700">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-blue-600 text-white text-xs flex items-center justify-center font-bold">{q.pos}</span>
                      <div>
                        <div className="text-white text-sm font-medium">{q.plate}</div>
                        <div className="text-slate-500 text-xs">{q.type}</div>
                      </div>
                    </div>
                    <div className="text-yellow-400 text-xs font-medium">{q.wait}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
