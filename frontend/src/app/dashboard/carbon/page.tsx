"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Leaf, Award, TrendingUp, Users, TreePine } from "lucide-react";
import { motion } from "framer-motion";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";

const monthlyData = [
  { month: "Jan", co2: 1200, trees: 5.5 },
  { month: "Feb", co2: 1850, trees: 8.4 },
  { month: "Mar", co2: 2100, trees: 9.5 },
  { month: "Apr", co2: 1700, trees: 7.7 },
  { month: "May", co2: 2400, trees: 10.9 },
  { month: "Jun", co2: 3100, trees: 14.1 },
];

const leaderboard = [
  { rank: 1, name: "Arjun Sharma", plate: "MH12AB3456", co2: "23.4 kg", badge: "🏆 Eco Warrior", sessions: 47 },
  { rank: 2, name: "Priya Nair", plate: "KA05CD7890", co2: "18.9 kg", badge: "🌍 Carbon Saver", sessions: 38 },
  { rank: 3, name: "Rahul Gupta", plate: "DL9CA5678", co2: "14.2 kg", badge: "🌍 Carbon Saver", sessions: 29 },
  { rank: 4, name: "Sunita Verma", plate: "TN09RS7890", co2: "9.1 kg", badge: "⚡ EV Champion", sessions: 21 },
  { rank: 5, name: "Anand Reddy", plate: "AP02MN3456", co2: "6.8 kg", badge: "🌱 Green Starter", sessions: 15 },
];

const badges = [
  { name: "Green Starter", icon: "🌱", threshold: "100g", users: 142, color: "#10b981" },
  { name: "EV Champion", icon: "⚡", threshold: "500g", users: 89, color: "#3b82f6" },
  { name: "Carbon Saver", icon: "🌍", threshold: "1 kg", users: 54, color: "#8b5cf6" },
  { name: "Eco Warrior", icon: "🏆", threshold: "5 kg", users: 23, color: "#f59e0b" },
  { name: "Planet Hero", icon: "🚀", threshold: "10 kg", users: 8, color: "#ef4444" },
  { name: "Zero Emission", icon: "♻️", threshold: "25 kg", users: 2, color: "#06b6d4" },
];

const COLORS = ["#10b981", "#3b82f6", "#8b5cf6", "#f59e0b", "#ef4444", "#06b6d4"];

export default function CarbonTrackerPage() {
  const totalCO2 = 12.4; // tonnes saved this month
  const treesEquiv = Math.round(totalCO2 * 1000 / 22);
  const activeUsers = 318;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Carbon Footprint Tracker</h1>
        <p className="text-slate-400">Module 10 — CO₂ savings, eco badges, and green city reporting</p>
      </div>

      {/* Hero Stats */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { title: "CO₂ Saved (This Month)", value: `${totalCO2} tonnes`, icon: <Leaf className="h-5 w-5 text-green-400" />, color: "text-green-400", bg: "bg-green-500/10" },
          { title: "Trees Equivalent", value: `${treesEquiv} trees`, icon: <TreePine className="h-5 w-5 text-emerald-400" />, color: "text-emerald-400", bg: "bg-emerald-500/10" },
          { title: "Eco Users", value: activeUsers.toString(), icon: <Users className="h-5 w-5 text-blue-400" />, color: "text-blue-400", bg: "bg-blue-500/10" },
          { title: "Fuel Saved (L)", value: "8,420 L", icon: <TrendingUp className="h-5 w-5 text-purple-400" />, color: "text-purple-400", bg: "bg-purple-500/10" },
        ].map((stat, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}>
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-slate-400">{stat.title}</CardTitle>
                <div className={`p-2 rounded-lg ${stat.bg}`}>{stat.icon}</div>
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Chart + Pie */}
      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Monthly CO₂ Savings Trend</CardTitle>
              <p className="text-sm text-slate-400">Cumulative grams of CO₂ saved per month</p>
            </CardHeader>
            <CardContent>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={monthlyData}>
                    <defs>
                      <linearGradient id="colorCO2" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="month" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155" }} labelStyle={{ color: "#f1f5f9" }} />
                    <Area type="monotone" dataKey="co2" stroke="#10b981" strokeWidth={2} fill="url(#colorCO2)" name="CO₂ (g)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Badge Distribution</CardTitle>
            <p className="text-sm text-slate-400">Users per eco badge tier</p>
          </CardHeader>
          <CardContent>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={badges} dataKey="users" nameKey="name" cx="50%" cy="50%" innerRadius={50} outerRadius={80}>
                    {badges.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155" }} formatter={(v, n) => [`${v} users`, n]} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="space-y-1 mt-2">
              {badges.slice(0, 4).map((b, i) => (
                <div key={i} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[i] }} />
                    <span className="text-slate-400">{b.icon} {b.name}</span>
                  </div>
                  <span className="text-slate-300 font-medium">{b.users}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Eco Badges Grid */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2"><Award className="h-5 w-5 text-yellow-400" /> Eco Badge Tiers</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {badges.map((badge, i) => (
              <div key={i} className="text-center p-4 rounded-xl border border-slate-700 hover:border-slate-500 transition-colors">
                <div className="text-3xl mb-2">{badge.icon}</div>
                <div className="text-white font-medium text-sm">{badge.name}</div>
                <div className="text-slate-500 text-xs mt-1">{badge.threshold} CO₂</div>
                <div className="mt-2 text-xs font-bold" style={{ color: badge.color }}>{badge.users} users</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Leaderboard */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">🏆 Eco Leaderboard — Top Users</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {leaderboard.map((user) => (
              <div key={user.rank} className={`flex items-center gap-4 p-3 rounded-xl border transition-colors ${user.rank === 1 ? "border-yellow-500/30 bg-yellow-500/5" : "border-slate-700 hover:border-slate-600"}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${user.rank === 1 ? "bg-yellow-500 text-black" : user.rank === 2 ? "bg-slate-400 text-black" : user.rank === 3 ? "bg-amber-600 text-white" : "bg-slate-700 text-white"}`}>
                  {user.rank}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-white font-medium">{user.name}</span>
                    <span className="text-xs text-slate-500">{user.badge}</span>
                  </div>
                  <div className="text-slate-500 text-xs">{user.plate} · {user.sessions} sessions</div>
                </div>
                <div className="text-green-400 font-bold">{user.co2}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
