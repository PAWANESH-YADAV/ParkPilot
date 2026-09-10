"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BarChart3, Download, TrendingUp, Users, Car } from "lucide-react";

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Analytics & Reports</h1>
          <p className="text-slate-400">View key metrics and insights</p>
        </div>
        <Button>
          <Download className="h-4 w-4 mr-2" />
          Export Report
        </Button>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-6">
            <p className="text-slate-400 text-sm mb-2">Total Revenue</p>
            <p className="text-3xl font-bold text-white">$12,450.00</p>
            <p className="text-green-400 text-sm flex items-center gap-1 mt-2">
              <TrendingUp className="h-4 w-4" />
              +12.5%
            </p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-6">
            <p className="text-slate-400 text-sm mb-2">Occupancy Rate</p>
            <p className="text-3xl font-bold text-white">78%</p>
            <p className="text-blue-400 text-sm mt-2">All lots</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-6">
            <p className="text-slate-400 text-sm mb-2">Active Users</p>
            <p className="text-3xl font-bold text-white">142</p>
            <p className="text-purple-400 text-sm mt-2">Today</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-6">
            <p className="text-slate-400 text-sm mb-2">Total Bookings</p>
            <p className="text-3xl font-bold text-white">342</p>
            <p className="text-yellow-400 text-sm mt-2">This month</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Occupancy Analytics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 bg-slate-700/50 rounded-lg flex items-center justify-center">
              <BarChart3 className="h-16 w-16 text-slate-500" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Revenue Analytics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 bg-slate-700/50 rounded-lg flex items-center justify-center">
              <TrendingUp className="h-16 w-16 text-slate-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">Available Reports</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {[
            "Occupancy Report (Daily/Weekly/Monthly)",
            "Revenue Report",
            "User Activity Report",
            "Parking Utilization Report",
            "Financial Summary",
          ].map((report, idx) => (
            <div key={idx} className="flex justify-between items-center p-3 bg-slate-700/50 rounded-lg">
              <span className="text-white">{report}</span>
              <Button variant="ghost" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
