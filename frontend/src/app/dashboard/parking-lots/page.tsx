"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MapPin, Plus, Edit2, Trash2, Clock, Users, Car } from "lucide-react";

interface ParkingLot {
  id: string;
  name: string;
  address: string;
  capacity: number;
  occupied: number;
  status: "active" | "inactive";
  operatingHours: string;
  zones: string[];
}

export default function ParkingLotManagementPage() {
  const [lots, setLots] = useState<ParkingLot[]>([
    { id: "1", name: "Downtown Garage", address: "123 Main St", capacity: 150, occupied: 98, status: "active", operatingHours: "24/7", zones: ["A", "B", "C"] },
    { id: "2", name: "City Center Parking", address: "456 Oak Ave", capacity: 100, occupied: 45, status: "active", operatingHours: "6AM - 12AM", zones: ["X", "Y"] },
    { id: "3", name: "Waterfront Parking", address: "789 River Rd", capacity: 200, occupied: 120, status: "active", operatingHours: "24/7", zones: ["P", "Q", "R", "S"] },
  ]);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Parking Lot Management</h1>
          <p className="text-slate-400">Manage all parking locations</p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Add New Lot
        </Button>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {lots.map((lot) => (
          <Card key={lot.id} className="bg-slate-800 border-slate-700">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-xl text-white">{lot.name}</CardTitle>
                  <p className="text-slate-400 text-sm flex items-center gap-1">
                    <MapPin className="h-4 w-4" />
                    {lot.address}
                  </p>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  lot.status === "active" ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
                }`}>
                  {lot.status}
                </span>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <Car className="h-4 w-4 text-blue-500" />
                  <span className="text-slate-400">Capacity:</span>
                  <span className="text-white font-medium">{lot.capacity}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-green-500" />
                  <span className="text-slate-400">Occupied:</span>
                  <span className="text-white font-medium">{lot.occupied}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 text-sm">
                <Clock className="h-4 w-4 text-yellow-500" />
                <span className="text-slate-400">Hours:</span>
                <span className="text-white">{lot.operatingHours}</span>
              </div>

              <div className="flex flex-wrap gap-2">
                {lot.zones.map((zone) => (
                  <span key={zone} className="px-2 py-1 bg-slate-700 rounded-full text-xs text-slate-300">
                    Zone {zone}
                  </span>
                ))}
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
