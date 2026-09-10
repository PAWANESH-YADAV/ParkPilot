"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { DollarSign, Plus, Edit2, Trash2, Clock } from "lucide-react";

interface PricingRule {
  id: string;
  name: string;
  type: "hourly" | "daily" | "peak";
  rate: string;
  vehicleType: string;
  active: boolean;
}

export default function PricingManagementPage() {
  const [rules, setRules] = useState<PricingRule[]>([
    { id: "1", name: "Standard Hourly", type: "hourly", rate: "$15/hr", vehicleType: "All", active: true },
    { id: "2", name: "Peak Hour (7AM-10AM)", type: "peak", rate: "$20/hr", vehicleType: "All", active: true },
    { id: "3", name: "Daily Rate", type: "daily", rate: "$50/day", vehicleType: "Car", active: true },
    { id: "4", name: "Bike Parking", type: "hourly", rate: "$5/hr", vehicleType: "Bike", active: true },
  ]);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Pricing Management</h1>
          <p className="text-slate-400">Configure parking rates and rules</p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Add New Rule
        </Button>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {rules.map((rule) => (
          <Card key={rule.id} className="bg-slate-800 border-slate-700">
            <CardHeader>
              <div className="flex justify-between items-start">
                <CardTitle className="text-xl text-white">{rule.name}</CardTitle>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  rule.active ? "bg-green-500/20 text-green-400" : "bg-slate-500/20 text-slate-400"
                }`}>
                  {rule.active ? "Active" : "Inactive"}
                </span>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-yellow-500" />
                <span className="text-2xl font-bold text-white">{rule.rate}</span>
              </div>
              <div className="text-sm space-y-1">
                <p className="text-slate-400">Type: <span className="text-white">{rule.type}</span></p>
                <p className="text-slate-400">Vehicles: <span className="text-white">{rule.vehicleType}</span></p>
              </div>
              <div className="flex gap-2 pt-2 border-t border-slate-700">
                <Button variant="ghost" size="sm" className="flex-1">
                  <Edit2 className="h-4 w-4 mr-1" />
                  Edit
                </Button>
                <Button variant="ghost" size="sm" className="flex-1 text-red-400">
                  <Trash2 className="h-4 w-4 mr-1" />
                  Delete
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
