'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  MapPin,
  Calendar,
  Clock,
  Star,
  ChevronDown
} from 'lucide-react';

export default function ParkingHistoryPage() {
  const history = [
    {
      id: 'HIST-12345',
      location: 'Downtown Garage',
      date: 'Dec 18, 2024',
      entryTime: '10:00 AM',
      exitTime: '1:00 PM',
      duration: '3h',
      amount: '$45.00',
      slot: 'A-12',
      rating: 5,
    },
    {
      id: 'HIST-12344',
      location: 'City Center Parking',
      date: 'Dec 12, 2024',
      entryTime: '2:00 PM',
      exitTime: '5:00 PM',
      duration: '3h',
      amount: '$36.00',
      slot: 'B-05',
      rating: 4,
    },
    {
      id: 'HIST-12343',
      location: 'Waterfront Parking',
      date: 'Dec 10, 2024',
      entryTime: '9:00 AM',
      exitTime: '6:00 PM',
      duration: '9h',
      amount: '$90.00',
      slot: 'C-18',
      rating: null,
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Parking History</h1>
        <p className="text-slate-400">View all your past parking sessions</p>
      </div>

      {/* History List */}
      <div className="space-y-4">
        {history.map((item) => (
          <Card key={item.id} className="bg-slate-800 border-slate-700">
            <CardHeader className="pb-3">
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-xl text-white">{item.location}</CardTitle>
                  <p className="text-slate-400 text-sm flex items-center gap-1">
                    <MapPin className="h-4 w-4" />
                    Slot {item.slot}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-white">{item.amount}</p>
                  <p className="text-slate-400 text-sm">{item.duration}</p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-3 gap-4 mb-4 text-sm">
                <div className="flex items-center gap-2 text-slate-300">
                  <Calendar className="h-4 w-4 text-blue-500" />
                  {item.date}
                </div>
                <div className="flex items-center gap-2 text-slate-300">
                  <Clock className="h-4 w-4 text-green-500" />
                  {item.entryTime} - {item.exitTime}
                </div>
              </div>
              <div className="flex items-center justify-between pt-2 border-t border-slate-700">
                {item.rating ? (
                  <div className="flex items-center gap-1 text-yellow-400">
                    {[...Array(5)].map((_, i) => (
                      <Star
                        key={i}
                        className="h-4 w-4"
                        fill={i < item.rating ? 'currentColor' : 'none'}
                      />
                    ))}
                    <span className="text-slate-400 ml-2 text-sm">Your rating</span>
                  </div>
                ) : (
                  <p className="text-slate-400 text-sm">Rate this parking</p>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
