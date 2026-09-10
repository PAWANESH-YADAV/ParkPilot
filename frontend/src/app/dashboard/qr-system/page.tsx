"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { QrCode, ScanLine, CheckCircle, XCircle, Clock, Ticket, Plus } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const tickets = [
  { id: "PP98123", plate: "MH12AB3456", slot: "A-01", type: "session", status: "active", entry: "14:00", expiry: "16:30" },
  { id: "PP45678", plate: "KA05CD7890", slot: "EV-02", type: "visitor", status: "active", entry: "13:15", expiry: "17:15" },
  { id: "PP11234", plate: "DL9CA5678", slot: "B-03", type: "session", status: "used", entry: "10:00", expiry: "12:00" },
  { id: "PP77890", plate: "TN09RS7890", slot: "C-12", type: "monthly", status: "active", entry: "08:00", expiry: "08:00 (Mon)" },
  { id: "PP22456", plate: "AP02MN3456", slot: "A-07", type: "session", status: "expired", entry: "08:30", expiry: "10:30" },
];

const statusStyle: Record<string, string> = {
  active: "text-green-400 bg-green-500/10 border-green-500/30",
  used: "text-blue-400 bg-blue-500/10 border-blue-500/30",
  expired: "text-slate-400 bg-slate-500/10 border-slate-500/30",
};

const typeStyle: Record<string, string> = {
  session: "bg-blue-500/10 text-blue-400",
  visitor: "bg-purple-500/10 text-purple-400",
  monthly: "bg-yellow-500/10 text-yellow-400",
  prepaid: "bg-green-500/10 text-green-400",
};

export default function QRSystemPage() {
  const [scanInput, setScanInput] = useState("");
  const [scanResult, setScanResult] = useState<{ valid: boolean; message: string; details?: string } | null>(null);
  const [scanning, setScanning] = useState(false);
  const [generatePlate, setGeneratePlate] = useState("");
  const [generateDuration, setGenerateDuration] = useState("2");
  const [generateType, setGenerateType] = useState("session");
  const [generatedTicket, setGeneratedTicket] = useState<string | null>(null);

  const handleScan = async () => {
    if (!scanInput.trim()) return;
    setScanning(true);
    await new Promise((r) => setTimeout(r, 800));
    const found = tickets.find((t) => t.id === scanInput.trim().toUpperCase());
    if (found) {
      if (found.status === "active") {
        setScanResult({ valid: true, message: "✅ Valid ticket!", details: `Slot ${found.slot} · ${found.plate} · Valid until ${found.expiry}` });
      } else if (found.status === "used") {
        setScanResult({ valid: false, message: "❌ Ticket already used", details: `Plate: ${found.plate}` });
      } else {
        setScanResult({ valid: false, message: "⏰ Ticket expired", details: `Expired at ${found.expiry}` });
      }
    } else {
      setScanResult({ valid: false, message: "❌ QR code not found", details: "Please check the ticket ID" });
    }
    setScanning(false);
  };

  const handleGenerate = async () => {
    if (!generatePlate.trim()) return;
    await new Promise((r) => setTimeout(r, 600));
    const hash = `PP${Math.floor(Math.random() * 90000 + 10000)}`;
    setGeneratedTicket(hash);
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">QR Code System</h1>
        <p className="text-slate-400">Module 8 — Ticket generation, scanning, NFC support, and visitor passes</p>
      </div>

      {/* Stats */}
      <div className="grid md:grid-cols-4 gap-6">
        {[
          { label: "Active Tickets", value: tickets.filter(t => t.status === "active").length, icon: <Ticket className="h-5 w-5 text-green-400" />, color: "text-green-400" },
          { label: "Used Today", value: tickets.filter(t => t.status === "used").length, icon: <CheckCircle className="h-5 w-5 text-blue-400" />, color: "text-blue-400" },
          { label: "Expired", value: tickets.filter(t => t.status === "expired").length, icon: <Clock className="h-5 w-5 text-slate-400" />, color: "text-slate-400" },
          { label: "Total Issued", value: tickets.length, icon: <QrCode className="h-5 w-5 text-purple-400" />, color: "text-purple-400" },
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

      <div className="grid lg:grid-cols-2 gap-6">
        {/* QR Scanner */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2"><ScanLine className="h-5 w-5 text-blue-400" />Validate QR Ticket</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-3">
              <input
                type="text"
                value={scanInput}
                onChange={(e) => { setScanInput(e.target.value); setScanResult(null); }}
                placeholder="Enter ticket ID (e.g. PP98123)"
                className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-blue-500 transition-colors"
                onKeyDown={(e) => e.key === "Enter" && handleScan()}
              />
              <button
                onClick={handleScan}
                disabled={scanning}
                className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-sm transition-colors disabled:opacity-50"
              >
                {scanning ? "Scanning..." : "Scan"}
              </button>
            </div>

            <AnimatePresence>
              {scanResult && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className={`p-4 rounded-xl border ${scanResult.valid ? "bg-green-500/10 border-green-500/30" : "bg-red-500/10 border-red-500/30"}`}
                >
                  <div className={`font-medium ${scanResult.valid ? "text-green-400" : "text-red-400"}`}>
                    {scanResult.message}
                  </div>
                  {scanResult.details && <div className="text-slate-400 text-sm mt-1">{scanResult.details}</div>}
                </motion.div>
              )}
            </AnimatePresence>

            <p className="text-slate-500 text-xs">Try ticket IDs: PP98123 (active), PP11234 (used), PP22456 (expired)</p>
          </CardContent>
        </Card>

        {/* Generate QR */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2"><Plus className="h-5 w-5 text-green-400" />Generate QR Ticket</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-slate-400 text-xs mb-1 block">License Plate</label>
              <input
                type="text"
                value={generatePlate}
                onChange={(e) => { setGeneratePlate(e.target.value.toUpperCase()); setGeneratedTicket(null); }}
                placeholder="e.g. MH12AB3456"
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-green-500 transition-colors"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-slate-400 text-xs mb-1 block">Duration (hrs)</label>
                <select value={generateDuration} onChange={(e) => setGenerateDuration(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-green-500">
                  {[1, 2, 4, 8, 24].map((h) => <option key={h} value={h}>{h}h</option>)}
                </select>
              </div>
              <div>
                <label className="text-slate-400 text-xs mb-1 block">Type</label>
                <select value={generateType} onChange={(e) => setGenerateType(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-green-500">
                  {["session", "visitor", "prepaid", "monthly"].map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
            </div>
            <button onClick={handleGenerate} className="w-full py-2.5 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium text-sm transition-colors">
              Generate QR Ticket
            </button>
            <AnimatePresence>
              {generatedTicket && (
                <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="p-4 bg-green-500/10 border border-green-500/30 rounded-xl text-center">
                  <QrCode className="h-10 w-10 text-green-400 mx-auto mb-2" />
                  <div className="text-green-400 font-bold text-lg">{generatedTicket}</div>
                  <div className="text-slate-400 text-xs mt-1">{generatePlate} · {generateDuration}h · {generateType}</div>
                </motion.div>
              )}
            </AnimatePresence>
          </CardContent>
        </Card>
      </div>

      {/* Ticket Table */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">Recent Tickets</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700">
                  {["Ticket ID", "Plate", "Slot", "Type", "Entry", "Expiry", "Status"].map((h) => (
                    <th key={h} className="text-left text-slate-400 font-medium pb-3 pr-4">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {tickets.map((t) => (
                  <tr key={t.id} className="border-b border-slate-800 hover:bg-slate-700/30 transition-colors">
                    <td className="py-3 pr-4 text-blue-400 font-mono font-medium">{t.id}</td>
                    <td className="py-3 pr-4 text-white">{t.plate}</td>
                    <td className="py-3 pr-4 text-slate-300">{t.slot}</td>
                    <td className="py-3 pr-4"><span className={`px-2 py-0.5 rounded text-xs font-medium ${typeStyle[t.type]}`}>{t.type}</span></td>
                    <td className="py-3 pr-4 text-slate-400">{t.entry}</td>
                    <td className="py-3 pr-4 text-slate-400">{t.expiry}</td>
                    <td className="py-3 pr-4"><span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${statusStyle[t.status]}`}>{t.status}</span></td>
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
