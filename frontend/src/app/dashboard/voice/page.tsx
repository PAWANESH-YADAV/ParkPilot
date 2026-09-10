"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Mic, MicOff, Send, Volume2, MessageSquare, BarChart3, Zap } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

const sampleCommands = [
  "Check available parking slots",
  "Book a slot for 2 hours",
  "Navigate to my parking slot",
  "What is the current parking fee?",
  "Show EV charging availability",
];

const INTENTS: Record<string, { color: string; response: string }> = {
  check_availability: { color: "#10b981", response: "Currently 23 slots available at ParkPilot Central and 8 at ParkPilot North." },
  book_parking: { color: "#2563eb", response: "I'll help you book a parking slot. Please tell me your preferred lot and duration." },
  navigate: { color: "#8b5cf6", response: "Starting indoor navigation. Follow the green LED path to your slot." },
  payment_inquiry: { color: "#f59e0b", response: "Your current session fee is ₹75. Would you like to pay now?" },
  ev_status: { color: "#06b6d4", response: "EV Charger EV-01 is available at Level 1. Rate: ₹12/kWh." },
  greeting: { color: "#ec4899", response: "Hello! I'm ParkPilot Assistant. I can help you book, navigate, or pay for parking." },
  unknown: { color: "#64748b", response: "I didn't understand that. Try: 'book parking', 'check availability', or 'pay'." },
};

function detectIntent(text: string): string {
  const t = text.toLowerCase();
  if (t.includes("available") || t.includes("free") || t.includes("slot")) return "check_availability";
  if (t.includes("book") || t.includes("reserve")) return "book_parking";
  if (t.includes("navigate") || t.includes("where") || t.includes("direction")) return "navigate";
  if (t.includes("pay") || t.includes("fee") || t.includes("billing")) return "payment_inquiry";
  if (t.includes("ev") || t.includes("electric") || t.includes("charging")) return "ev_status";
  if (t.includes("hello") || t.includes("hi") || t.includes("help")) return "greeting";
  return "unknown";
}

interface Message { id: number; text: string; isUser: boolean; intent?: string; response?: string; confidence?: number; }

const intentData = [
  { name: "check_availability", value: 34, color: "#10b981" },
  { name: "book_parking", value: 28, color: "#2563eb" },
  { name: "navigate", value: 18, color: "#8b5cf6" },
  { name: "payment_inquiry", value: 12, color: "#f59e0b" },
  { name: "ev_status", value: 8, color: "#06b6d4" },
];

const recentHistory = [
  { text: "Book a parking slot near exit", intent: "book_parking", confidence: 0.95, time: "2 min ago", success: true },
  { text: "Navigate to slot B-07", intent: "navigate", confidence: 0.88, time: "15 min ago", success: true },
  { text: "Check EV chargers", intent: "ev_status", confidence: 0.92, time: "32 min ago", success: true },
  { text: "XYZ random words", intent: "unknown", confidence: 0.0, time: "1 hr ago", success: false },
];

export default function VoiceAssistantPage() {
  const [messages, setMessages] = useState<Message[]>([
    { id: 0, text: "Hello! I'm ParkPilot Voice Assistant. Type or say a command!", isUser: false },
  ]);
  const [input, setInput] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [processing, setProcessing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const sendMessage = async (text?: string) => {
    const msg = text || input.trim();
    if (!msg) return;
    setInput("");
    const userMsg: Message = { id: Date.now(), text: msg, isUser: true };
    setMessages((prev) => [...prev, userMsg]);
    setProcessing(true);
    await new Promise((r) => setTimeout(r, 600));
    const intent = detectIntent(msg);
    const intentCfg = INTENTS[intent];
    const confidence = intent === "unknown" ? 0.0 : 0.7 + Math.random() * 0.28;
    const botMsg: Message = {
      id: Date.now() + 1,
      text: intentCfg.response,
      isUser: false,
      intent,
      confidence: Math.round(confidence * 100) / 100,
    };
    setMessages((prev) => [...prev, botMsg]);
    setProcessing(false);
  };

  const toggleListening = () => {
    setIsListening((v) => !v);
    if (!isListening) {
      setTimeout(() => {
        setIsListening(false);
        sendMessage("Check available parking slots");
      }, 2000);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Voice Assistant</h1>
        <p className="text-slate-400">Module 11 — Whisper STT, NLP intent detection, gTTS output, kiosk integration</p>
      </div>

      {/* Stats */}
      <div className="grid md:grid-cols-4 gap-6">
        {[
          { label: "Commands Today", value: "247", icon: <MessageSquare className="h-5 w-5 text-blue-400" />, color: "text-blue-400" },
          { label: "Success Rate", value: "91.3%", icon: <Zap className="h-5 w-5 text-green-400" />, color: "text-green-400" },
          { label: "Intents Detected", value: "6", icon: <BarChart3 className="h-5 w-5 text-purple-400" />, color: "text-purple-400" },
          { label: "Avg Confidence", value: "0.87", icon: <Volume2 className="h-5 w-5 text-yellow-400" />, color: "text-yellow-400" },
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
        {/* Kiosk Simulator */}
        <div className="lg:col-span-2">
          <Card className="bg-slate-800 border-slate-700 h-full flex flex-col">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Mic className="h-5 w-5 text-blue-400" />
                Kiosk Simulator
              </CardTitle>
              <p className="text-sm text-slate-400">Simulate voice commands via text input</p>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col">
              {/* Sample commands */}
              <div className="flex flex-wrap gap-2 mb-4">
                {sampleCommands.map((cmd) => (
                  <button key={cmd} onClick={() => sendMessage(cmd)} className="text-xs px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-full transition-colors">
                    {cmd}
                  </button>
                ))}
              </div>

              {/* Messages */}
              <div className="flex-1 min-h-64 max-h-80 overflow-y-auto space-y-3 mb-4 pr-1">
                <AnimatePresence>
                  {messages.map((msg) => (
                    <motion.div key={msg.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className={`flex ${msg.isUser ? "justify-end" : "justify-start"}`}>
                      <div className={`max-w-xs lg:max-w-md px-4 py-2.5 rounded-2xl text-sm ${msg.isUser ? "bg-blue-600 text-white rounded-br-sm" : "bg-slate-700 text-slate-100 rounded-bl-sm"}`}>
                        <div>{msg.text}</div>
                        {msg.intent && msg.intent !== "unknown" && (
                          <div className="mt-1.5 flex items-center gap-2">
                            <span className="text-xs opacity-70">Intent: {msg.intent}</span>
                            <span className="text-xs opacity-70">· {(msg.confidence! * 100).toFixed(0)}%</span>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
                {processing && (
                  <div className="flex justify-start">
                    <div className="bg-slate-700 px-4 py-2.5 rounded-2xl rounded-bl-sm">
                      <div className="flex gap-1">
                        {[0, 1, 2].map((i) => <span key={i} className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />)}
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="flex gap-3">
                <button
                  onClick={toggleListening}
                  className={`p-3 rounded-xl transition-all ${isListening ? "bg-red-600 text-white animate-pulse" : "bg-slate-700 text-slate-300 hover:bg-slate-600"}`}
                >
                  {isListening ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
                </button>
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                  placeholder={isListening ? "Listening..." : "Type a command..."}
                  disabled={isListening}
                  className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500 transition-colors disabled:opacity-50"
                />
                <button onClick={() => sendMessage()} disabled={!input.trim() || processing} className="px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-colors disabled:opacity-50">
                  <Send className="h-5 w-5" />
                </button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Analytics */}
        <div className="space-y-4">
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader><CardTitle className="text-white text-sm">Intent Distribution</CardTitle></CardHeader>
            <CardContent>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={intentData} dataKey="value" cx="50%" cy="50%" innerRadius={45} outerRadius={72}>
                      {intentData.map((d, i) => <Cell key={i} fill={d.color} />)}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155" }} formatter={(v) => [`${v}%`]} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-1.5 mt-2">
                {intentData.map((d, i) => (
                  <div key={i} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }} /><span className="text-slate-400">{d.name.replace(/_/g, " ")}</span></div>
                    <span className="text-slate-300 font-medium">{d.value}%</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800 border-slate-700">
            <CardHeader><CardTitle className="text-white text-sm">Recent Commands</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentHistory.map((h, i) => (
                  <div key={i} className="border-b border-slate-700 pb-3 last:border-0 last:pb-0">
                    <div className="flex items-center justify-between mb-1">
                      <div className={`text-xs font-medium px-2 py-0.5 rounded-full ${h.success ? "bg-green-500/10 text-green-400" : "bg-red-500/10 text-red-400"}`}>
                        {h.intent.replace(/_/g, " ")}
                      </div>
                      <span className="text-slate-500 text-xs">{h.time}</span>
                    </div>
                    <p className="text-slate-300 text-xs truncate">{h.text}</p>
                    {h.confidence > 0 && <p className="text-slate-500 text-xs">{(h.confidence * 100).toFixed(0)}% confidence</p>}
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
