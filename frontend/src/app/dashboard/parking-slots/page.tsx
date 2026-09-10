"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Car, Plus, Edit2, Trash2, Wrench, CheckCircle2, XCircle } from "lucide-react";

interface Slot {
  id: string;
  number: string;
  type: "car" | "bike" | "ev" | "disabled";
  status: "available" | "occupied" | "maintenance";
  zone: string;
}

export default function ParkingSlotManagementPage() {
  const [slots, setSlots] = useState<Slot[]>([
    { id: "1", number: "A-01", type: "car", status: "occupied", zone: "A" },
    { id: "2", number: "A-02", type: "car", status: "available", zone: "A" },
    { id: "3", number: "A-03", type: "ev", status: "available", zone: "A" },
    { id: "4", number: "B-01", type: "disabled", status: "available", zone: "B" },
    { id: "5", number: "B-02", type: "bike", status: "maintenance", zone: "B" },
    { id: "6", number: "C-01", type: "car", status: "available", zone: "C" },
  ]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "available": return "bg-green-500/20 text-green-400";
      case "occupied": return "bg-red-500/20 text-red-400";
      case "maintenance": return "bg-yellow-500/20 text-yellow-400";
      default: return "";
    }
  };

  const getTypeIcon = (type: string) => {
    return <Car className="h-6 w-6" />;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Parking Slot Management</h1>
          <p className="text-slate-400">Manage individual parking slots</p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Add New Slot
        </Button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {slots.map((slot) => (
          <Card key={slot.id} className={`bg-slate-800 border-slate-700 border-l-4 ${
            slot.status === "available" ? "border-l-green-500" :
            slot.status === "occupied" ? "border-l-red-500" :
            "border-l-yellow-500"
          }`}>
            <CardContent className="p-4 text-center">
              <div className="flex justify-center mb-2">
                {slot.status === "available" ? <CheckCircle2 className="h-6 w-6 text-green-500" /> :
                 slot.status === "occupied" ? <XCircle className="h-6 w-6 text-red-500" /> :
                 <Wrench className="h-6 w-6 text-yellow-500" />}
              </div>
              <p className="text-white font-bold text-lg">{slot.number}</p>
              <p className={`text-xs px-2 py-1 rounded-full ${getStatusColor(slot.status)} mb-1`}>
                {slot.status}
              </p>
              <p className="text-slate-400 text-xs">{slot.type}</p>
              <div className="flex gap-1 justify-center mt-2">
                <Button variant="ghost" size="sm" className="h-8 px-2">
                  <Edit2 className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm" className="h-8 px-2 text-red-400">
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
