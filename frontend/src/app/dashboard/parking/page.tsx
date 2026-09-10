"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import ParkingMap from "@/components/ParkingMap";

export default function ParkingPage() {
  const lots = [
    { name: "Downtown Garage", slots: 150, occupied: 105, available: 45, price: "$15/hr" },
    { name: "City Center Parking", slots: 100, occupied: 77, available: 23, price: "$12/hr" },
    { name: "Waterfront Parking", slots: 200, occupied: 133, available: 67, price: "$10/hr" },
    { name: "Uptown Plaza", slots: 120, occupied: 88, available: 32, price: "$18/hr" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white mb-2">Parking Lots</h1>
        <p className="text-slate-400">View and manage all your parking locations.</p>
      </div>

      <ParkingMap />

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
        {lots.map((lot, idx) => (
          <Card key={idx} className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-lg text-white">{lot.name}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Total Slots:</span>
                <span className="text-white font-medium">{lot.slots}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Occupied:</span>
                <span className="text-red-400 font-medium">{lot.occupied}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Available:</span>
                <span className="text-green-400 font-medium">{lot.available}</span>
              </div>
              <div className="flex justify-between text-sm pt-2 border-t border-slate-700">
                <span className="text-slate-400">Price:</span>
                <span className="text-yellow-400 font-medium">{lot.price}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
