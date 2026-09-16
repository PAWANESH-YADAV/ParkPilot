"use client";

import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Car, MapPin, DollarSign, TrendingUp, Users, Camera, Zap, QrCode, ChevronRight } from "lucide-react";
import { motion } from "framer-motion";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from "recharts";

const chartData = [
  { name: "00:00", occupancy: 20 },
  { name: "04:00", occupancy: 10 },
  { name: "08:00", occupancy: 45 },
  { name: "12:00", occupancy: 65 },
  { name: "16:00", occupancy: 75 },
  { name: "20:00", occupancy: 85 },
  { name: "23:59", occupancy: 40 },
];

const revenueData = [
  { name: "Mon", revenue: 1200 },
  { name: "Tue", revenue: 1500 },
  { name: "Wed", revenue: 1100 },
  { name: "Thu", revenue: 1800 },
  { name: "Fri", revenue: 2200 },
  { name: "Sat", revenue: 2500 },
  { name: "Sun", revenue: 1900 },
];

export default function Dashboard() {
  const router = useRouter();
  const stats = [
    {
      title: "Total Slots",
      value: "150",
      icon: <MapPin className="h-6 w-6 text-blue-500" />,
      change: "+5%",
      trend: "up",
    },
    {
      title: "Occupied",
      value: "98",
      icon: <Car className="h-6 w-6 text-cyan-500" />,
      change: "+12%",
      trend: "up",
    },
    {
      title: "Available",
      value: "52",
      icon: <MapPin className="h-6 w-6 text-emerald-500" />,
      change: "-3%",
      trend: "down",
    },
    {
      title: "Revenue Today",
      value: "₹24,500",
      icon: <DollarSign className="h-6 w-6 text-emerald-500" />,
      change: "+18%",
      trend: "up",
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Dashboard</h1>
        <p className="text-slate-500 dark:text-slate-400">Welcome back! Here's what's happening at your parking lots.</p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card className="bg-white dark:bg-slate-850 dark:bg-slate-800/90 border-slate-200 dark:border-slate-700 shadow-xs dark:shadow-none hover:shadow-md transition-shadow">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-slate-500 dark:text-slate-400">{stat.title}</CardTitle>
                {stat.icon}
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-slate-900 dark:text-white">{stat.value}</div>
                <p className={`text-xs pt-1 font-medium ${stat.trend === "up" ? "text-emerald-600 dark:text-green-400" : "text-red-600 dark:text-red-400"}`}>
                  {stat.change} from yesterday
                </p>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="bg-white dark:bg-slate-850 dark:bg-slate-800/90 border-slate-200 dark:border-slate-700">
            <CardHeader>
              <CardTitle className="text-slate-900 dark:text-white">Occupancy Trend</CardTitle>
              <p className="text-sm text-slate-500 dark:text-slate-400">Real-time parking occupancy over the last 24 hours</p>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="colorOccupancy" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-700" />
                    <XAxis dataKey="name" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip />
                    <Area
                      type="monotone"
                      dataKey="occupancy"
                      stroke="#2563eb"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#colorOccupancy)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card className="bg-white dark:bg-slate-850 dark:bg-slate-800/90 border-slate-200 dark:border-slate-700">
            <CardHeader>
              <CardTitle className="text-slate-900 dark:text-white">Revenue</CardTitle>
              <p className="text-sm text-slate-500 dark:text-slate-400">Weekly revenue overview</p>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={revenueData}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-700" />
                    <XAxis dataKey="name" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="revenue"
                      stroke="#10b981"
                      strokeWidth={2}
                      dot={{ fill: "#10b981" }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <Card className="bg-white dark:bg-slate-850 dark:bg-slate-800/90 border-slate-200 dark:border-slate-700">
            <CardHeader className="flex flex-row items-center gap-4">
              <div className="p-3 bg-blue-500/10 rounded-xl">
                <Camera className="h-6 w-6 text-blue-600 dark:text-blue-500" />
              </div>
              <div>
                <CardTitle className="text-slate-900 dark:text-white text-lg">Cameras</CardTitle>
                <p className="text-sm text-slate-500 dark:text-slate-400">Active CCTV feeds</p>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900 dark:text-white">8/8</div>
              <div className="flex gap-2 mt-2">
                <span className="inline-flex items-center gap-1.5 text-xs text-emerald-600 dark:text-green-400 font-medium">
                  <span className="w-2 h-2 bg-emerald-500 rounded-full" />
                  All Online
                </span>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <Card className="bg-white dark:bg-slate-850 dark:bg-slate-800/90 border-slate-200 dark:border-slate-700">
            <CardHeader className="flex flex-row items-center gap-4">
              <div className="p-3 bg-amber-500/10 rounded-xl">
                <Zap className="h-6 w-6 text-amber-500" />
              </div>
              <div>
                <CardTitle className="text-slate-900 dark:text-white text-lg">IoT Sensors</CardTitle>
                <p className="text-sm text-slate-500 dark:text-slate-400">Parking slot sensors</p>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900 dark:text-white">148/150</div>
              <div className="flex gap-2 mt-2">
                <span className="inline-flex items-center gap-1.5 text-xs text-amber-600 dark:text-yellow-400 font-medium">
                  <span className="w-2 h-2 bg-amber-500 rounded-full" />
                  2 Offline
                </span>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
        >
          <Card className="bg-white dark:bg-slate-850 dark:bg-slate-800/90 border-slate-200 dark:border-slate-700">
            <CardHeader className="flex flex-row items-center gap-4">
              <div className="p-3 bg-purple-500/10 rounded-xl">
                <Users className="h-6 w-6 text-purple-600 dark:text-purple-500" />
              </div>
              <div>
                <CardTitle className="text-slate-900 dark:text-white text-lg">Active Users</CardTitle>
                <p className="text-sm text-slate-500 dark:text-slate-400">Currently parked vehicles</p>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900 dark:text-white">89</div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">Peak occupancy: 128 at 6:30 PM</p>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
      >
        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Quick Actions</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card
            className="bg-white dark:bg-slate-850 dark:bg-slate-800/90 border-slate-200 dark:border-slate-700 cursor-pointer hover:border-emerald-500 dark:hover:border-emerald-500 transition-all hover:shadow-md"
            onClick={() => router.push("/dashboard/qr-system")}
          >
            <CardContent className="p-6 flex flex-col items-center text-center gap-3">
              <div className="p-3 bg-emerald-500/10 rounded-xl">
                <QrCode className="h-8 w-8 text-emerald-600 dark:text-emerald-500" />
              </div>
              <div>
                <p className="text-slate-900 dark:text-white font-semibold">QR Code System</p>
                <p className="text-slate-500 dark:text-slate-400 text-sm">Generate & scan tickets</p>
              </div>
              <ChevronRight className="h-5 w-5 text-slate-400" />
            </CardContent>
          </Card>

          <Card
            className="bg-white dark:bg-slate-850 dark:bg-slate-800/90 border-slate-200 dark:border-slate-700 cursor-pointer hover:border-blue-500 dark:hover:border-blue-500 transition-all hover:shadow-md"
            onClick={() => router.push("/dashboard/parking-lots")}
          >
            <CardContent className="p-6 flex flex-col items-center text-center gap-3">
              <div className="p-3 bg-blue-500/10 rounded-xl">
                <MapPin className="h-8 w-8 text-blue-600 dark:text-blue-500" />
              </div>
              <div>
                <p className="text-slate-900 dark:text-white font-semibold">Parking Lots</p>
                <p className="text-slate-500 dark:text-slate-400 text-sm">Manage locations</p>
              </div>
              <ChevronRight className="h-5 w-5 text-slate-400" />
            </CardContent>
          </Card>

          <Card
            className="bg-white dark:bg-slate-850 dark:bg-slate-800/90 border-slate-200 dark:border-slate-700 cursor-pointer hover:border-cyan-500 dark:hover:border-cyan-500 transition-all hover:shadow-md"
            onClick={() => router.push("/dashboard/bookings")}
          >
            <CardContent className="p-6 flex flex-col items-center text-center gap-3">
              <div className="p-3 bg-cyan-500/10 rounded-xl">
                <Car className="h-8 w-8 text-cyan-600 dark:text-cyan-500" />
              </div>
              <div>
                <p className="text-slate-900 dark:text-white font-semibold">Bookings</p>
                <p className="text-slate-500 dark:text-slate-400 text-sm">View all reservations</p>
              </div>
              <ChevronRight className="h-5 w-5 text-slate-400" />
            </CardContent>
          </Card>

          <Card
            className="bg-white dark:bg-slate-850 dark:bg-slate-800/90 border-slate-200 dark:border-slate-700 cursor-pointer hover:border-amber-500 dark:hover:border-amber-500 transition-all hover:shadow-md"
            onClick={() => router.push("/dashboard/billing")}
          >
            <CardContent className="p-6 flex flex-col items-center text-center gap-3">
              <div className="p-3 bg-amber-500/10 rounded-xl">
                <DollarSign className="h-8 w-8 text-amber-600 dark:text-amber-500" />
              </div>
              <div>
                <p className="text-slate-900 dark:text-white font-semibold">Billing</p>
                <p className="text-slate-500 dark:text-slate-400 text-sm">Payments & invoices</p>
              </div>
              <ChevronRight className="h-5 w-5 text-slate-400" />
            </CardContent>
          </Card>
        </div>
      </motion.div>
    </div>
  );
}
