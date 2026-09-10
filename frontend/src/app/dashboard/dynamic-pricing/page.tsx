"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, TrendingDown, DollarSign, Activity, Sliders, RefreshCw } from "lucide-react";
import { motion } from "framer-motion";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";

const pricingHistory = [
  { time: "00:00", rate: 30, occupancy: 18 },
  { time: "04:00", rate: 25, occupancy: 8 },
  { time: "06:00", rate: 30, occupancy: 22 },
  { time: "08:00", rate: 42, occupancy: 68 },
  { time: "10:00", rate: 36, occupancy: 55 },
  { time: "12:00", rate: 45, occupancy: 75 },
  { time: "14:00", rate: 38, occupancy: 60 },
  { time: "16:00", rate: 48, occupancy: 82 },
  { time: "18:00", rate: 52, occupancy: 91 },
  { time: "20:00", rate: 42, occupancy: 70 },
  { time: "22:00", rate: 32, occupancy: 35 },
];

const lots = [
  { id: 1, name: "ParkPilot Central", base: 30, current: 52, surge: 1.73, occupancy: 91, weather: 1.0, event: 1.2 },
  { id: 2, name: "ParkPilot North", base: 35, current: 35, surge: 1.0, occupancy: 45, weather: 1.0, event: 1.0 },
];

export default function DynamicPricingPage() {
  const [selectedLot, setSelectedLot] = useState(lots[0]);
  const [occupancy, setOccupancy] = useState(selectedLot.occupancy);
  const [weatherFactor, setWeatherFactor] = useState(1.0);
  const [eventFactor, setEventFactor] = useState(selectedLot.event);
  const [calculating, setCalculating] = useState(false);
  const [calculatedRate, setCalculatedRate] = useState<number | null>(null);

  const getSurge = (occ: number, wf: number, ef: number) => {
    const occMult = occ < 50 ? 0.9 : occ < 80 ? 1.0 : occ < 90 ? 1.3 : 1.6;
    return Math.max(0.5, Math.min(3.0, occMult * wf * ef));
  };

  const handleCalculate = async () => {
    setCalculating(true);
    await new Promise((r) => setTimeout(r, 700));
    const surge = getSurge(occupancy, weatherFactor, eventFactor);
    setCalculatedRate(Math.round(selectedLot.base * surge));
    setCalculating(false);
  };

  const surgeColor = (s: number) => s > 1.3 ? "text-red-400" : s > 1.0 ? "text-yellow-400" : "text-green-400";
  const surgeLabel = (s: number) => s > 1.3 ? "🔴 Peak Surge" : s > 1.0 ? "🟡 Moderate" : "🟢 Discount";

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Dynamic Pricing Engine</h1>
        <p className="text-slate-400">Module 12 — AI-driven surge pricing based on occupancy, weather, and events</p>
      </div>

      {/* Lot Cards */}
      <div className="grid md:grid-cols-2 gap-6">
        {lots.map((lot, i) => (
          <motion.div key={lot.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}>
            <Card
              className={`border cursor-pointer transition-all ${selectedLot.id === lot.id ? "bg-slate-700 border-blue-500" : "bg-slate-800 border-slate-700 hover:border-slate-500"}`}
              onClick={() => { setSelectedLot(lot); setOccupancy(lot.occupancy); setEventFactor(lot.event); setCalculatedRate(null); }}
            >
              <CardContent className="pt-5">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <div className="text-white font-bold text-lg">{lot.name}</div>
                    <div className="text-slate-400 text-sm">Base: ₹{lot.base}/hr</div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-blue-400">₹{lot.current}</div>
                    <div className={`text-sm font-medium ${surgeColor(lot.surge)}`}>{surgeLabel(lot.surge)}</div>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div className="text-center p-2 bg-slate-900 rounded-lg">
                    <div className="text-white font-bold">{lot.occupancy}%</div>
                    <div className="text-slate-500 text-xs">Occupancy</div>
                  </div>
                  <div className="text-center p-2 bg-slate-900 rounded-lg">
                    <div className="text-white font-bold">{lot.surge}x</div>
                    <div className="text-slate-500 text-xs">Surge</div>
                  </div>
                  <div className="text-center p-2 bg-slate-900 rounded-lg">
                    <div className="text-white font-bold">{lot.event}x</div>
                    <div className="text-slate-500 text-xs">Event</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Chart + Simulator */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Price History */}
        <div className="lg:col-span-2">
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">24h Price & Occupancy — {selectedLot.name}</CardTitle>
              <p className="text-sm text-slate-400">Dynamic rate adjustments vs occupancy throughout the day</p>
            </CardHeader>
            <CardContent>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={pricingHistory}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="time" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                    <YAxis yAxisId="rate" stroke="#94a3b8" tick={{ fontSize: 11 }} domain={[20, 60]} />
                    <YAxis yAxisId="occ" orientation="right" stroke="#94a3b8" tick={{ fontSize: 11 }} domain={[0, 100]} />
                    <Tooltip contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155" }} labelStyle={{ color: "#f1f5f9" }} />
                    <ReferenceLine yAxisId="rate" y={selectedLot.base} stroke="#475569" strokeDasharray="4 4" label={{ value: "Base", fill: "#64748b", fontSize: 10 }} />
                    <Line yAxisId="rate" type="monotone" dataKey="rate" stroke="#2563eb" strokeWidth={2.5} dot={{ fill: "#2563eb", r: 3 }} name="Rate (₹)" />
                    <Line yAxisId="occ" type="monotone" dataKey="occupancy" stroke="#f59e0b" strokeWidth={1.5} strokeDasharray="4 4" dot={false} name="Occupancy %" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Pricing Simulator */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2"><Sliders className="h-5 w-5 text-purple-400" />Price Simulator</CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <div>
              <div className="flex justify-between mb-1">
                <label className="text-slate-400 text-xs">Occupancy</label>
                <span className="text-white text-xs font-bold">{occupancy}%</span>
              </div>
              <input type="range" min={0} max={100} value={occupancy} onChange={(e) => { setOccupancy(+e.target.value); setCalculatedRate(null); }} className="w-full accent-blue-500" />
            </div>
            <div>
              <div className="flex justify-between mb-1">
                <label className="text-slate-400 text-xs">Weather Factor</label>
                <span className="text-white text-xs font-bold">{weatherFactor.toFixed(1)}x</span>
              </div>
              <input type="range" min={0.8} max={1.5} step={0.1} value={weatherFactor} onChange={(e) => { setWeatherFactor(+e.target.value); setCalculatedRate(null); }} className="w-full accent-blue-500" />
            </div>
            <div>
              <div className="flex justify-between mb-1">
                <label className="text-slate-400 text-xs">Event Factor</label>
                <span className="text-white text-xs font-bold">{eventFactor.toFixed(1)}x</span>
              </div>
              <input type="range" min={1.0} max={2.5} step={0.1} value={eventFactor} onChange={(e) => { setEventFactor(+e.target.value); setCalculatedRate(null); }} className="w-full accent-blue-500" />
            </div>

            <button onClick={handleCalculate} disabled={calculating} className="w-full py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium text-sm transition-colors disabled:opacity-50 flex items-center justify-center gap-2">
              <RefreshCw className={`h-4 w-4 ${calculating ? "animate-spin" : ""}`} />
              {calculating ? "Calculating..." : "Calculate Price"}
            </button>

            {calculatedRate !== null && (
              <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="p-4 bg-slate-900 rounded-xl border border-slate-700 text-center">
                <div className="text-slate-400 text-xs mb-1">Recommended Rate</div>
                <div className="text-3xl font-bold text-blue-400">₹{calculatedRate}/hr</div>
                <div className={`text-sm font-medium mt-1 ${surgeColor(getSurge(occupancy, weatherFactor, eventFactor))}`}>
                  {surgeLabel(getSurge(occupancy, weatherFactor, eventFactor))} · {getSurge(occupancy, weatherFactor, eventFactor).toFixed(2)}x
                </div>
                <div className="text-slate-500 text-xs mt-2">Base ₹{selectedLot.base} × {getSurge(occupancy, weatherFactor, eventFactor).toFixed(2)}</div>
              </motion.div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
