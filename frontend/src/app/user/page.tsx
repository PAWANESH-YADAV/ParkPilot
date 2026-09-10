'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  MapPin,
  Car,
  Clock,
  CreditCard,
  QrCode,
  ChevronRight,
  TrendingUp,
  Calendar,
  Bell
} from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth } from '@/lib/auth-context';

interface Booking {
  id: string;
  userId: string;
  parkingLotId: string;
  parkingLotName: string;
  slotNumber: string;
  date: string;
  startTime: string;
  endTime: string;
  duration: number;
  amount: number;
  status: 'pending' | 'confirmed' | 'active' | 'completed' | 'cancelled';
  vehicleType: string;
}

export default function UserDashboard() {
  const router = useRouter();
  const { user } = useAuth();
  const [currentBooking, setCurrentBooking] = useState<Booking | null>(null);
  const [totalBookings, setTotalBookings] = useState(0);
  const [totalSpent, setTotalSpent] = useState(0);

  useEffect(() => {
    if (user) {
      const allBookings = JSON.parse(localStorage.getItem('parkpilot_bookings') || '[]');
      const userBookings = allBookings.filter((b: Booking) => b.userId === user.id);
      
      setTotalBookings(userBookings.length);
      
      const spent = userBookings.reduce((acc: number, b: Booking) => acc + b.amount, 0);
      setTotalSpent(spent);
      
      const active = userBookings.find((b: Booking) => b.status === 'active');
      if (active) {
        setCurrentBooking(active);
      } else {
        const upcoming = userBookings.find((b: Booking) => b.status === 'confirmed');
        setCurrentBooking(upcoming || null);
      }
    }
  }, [user]);

  const formatTime = (time: string) => {
    const [hour, minute] = time.split(':');
    const h = parseInt(hour);
    const ampm = h >= 12 ? 'PM' : 'AM';
    const hour12 = h % 12 || 12;
    return `${hour12}:${minute} ${ampm}`;
  };

  const stats = [
    { title: 'Total Bookings', value: totalBookings.toString(), icon: <Calendar className="h-6 w-6 text-blue-500" /> },
    { title: 'Active Booking', value: currentBooking ? '1' : '0', icon: <Car className="h-6 w-6 text-green-500" /> },
    { title: 'Total Spent', value: `$${totalSpent.toFixed(2)}`, icon: <CreditCard className="h-6 w-6 text-yellow-500" /> },
    { title: 'Saved Locations', value: '5', icon: <MapPin className="h-6 w-6 text-purple-500" /> },
  ];

  if (!user) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Hello, {user.firstName}!</h1>
        <p className="text-slate-400">Welcome back to ParkPilot</p>
      </div>

      {/* Stats Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-slate-400">{stat.title}</CardTitle>
                {stat.icon}
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-white">{stat.value}</div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Current Booking */}
      {currentBooking && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.4 }}
        >
          <Card className="bg-gradient-to-r from-blue-600 to-cyan-600 border-none">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Clock className="h-6 w-6" />
                {currentBooking.status === 'active' ? 'Current Booking' : 'Upcoming Booking'}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <p className="text-blue-100 text-sm">Location</p>
                  <p className="text-white font-semibold text-lg">{currentBooking.parkingLotName}</p>
                  <p className="text-blue-200 text-sm">Slot {currentBooking.slotNumber}</p>
                </div>
                <div>
                  <p className="text-blue-100 text-sm">Duration</p>
                  <p className="text-white font-semibold text-lg">
                    {formatTime(currentBooking.startTime)} - {formatTime(currentBooking.endTime)}
                  </p>
                  <p className="text-blue-200 text-sm">{currentBooking.duration}h • ${currentBooking.amount.toFixed(2)}</p>
                </div>
              </div>
              <div className="flex gap-3">
                {currentBooking.status === 'active' && (
                  <Button className="bg-white text-blue-600 hover:bg-blue-50">
                    Extend Parking
                  </Button>
                )}
                <Button variant="outline" className="border-white text-white hover:bg-white/10" onClick={() => router.push('/user/bookings')}>
                  View Details
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Quick Actions */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card 
          className="bg-slate-800 border-slate-700 cursor-pointer hover:border-blue-500 transition-colors" 
          onClick={() => router.push('/user/find-parking')}
        >
          <CardContent className="p-6 flex flex-col items-center text-center gap-3">
            <div className="p-3 bg-blue-500/10 rounded-lg">
              <MapPin className="h-8 w-8 text-blue-500" />
            </div>
            <div>
              <p className="text-white font-semibold">Find Parking</p>
              <p className="text-slate-400 text-sm">Search nearby lots</p>
            </div>
            <ChevronRight className="h-5 w-5 text-slate-500" />
          </CardContent>
        </Card>

        <Card 
          className="bg-slate-800 border-slate-700 cursor-pointer hover:border-green-500 transition-colors" 
          onClick={() => router.push('/user/qr-code')}
        >
          <CardContent className="p-6 flex flex-col items-center text-center gap-3">
            <div className="p-3 bg-green-500/10 rounded-lg">
              <QrCode className="h-8 w-8 text-green-500" />
            </div>
            <div>
              <p className="text-white font-semibold">QR Entry</p>
              <p className="text-slate-400 text-sm">Quick access</p>
            </div>
            <ChevronRight className="h-5 w-5 text-slate-500" />
          </CardContent>
        </Card>

        <Card 
          className="bg-slate-800 border-slate-700 cursor-pointer hover:border-yellow-500 transition-colors" 
          onClick={() => router.push('/user/vehicles')}
        >
          <CardContent className="p-6 flex flex-col items-center text-center gap-3">
            <div className="p-3 bg-yellow-500/10 rounded-lg">
              <Car className="h-8 w-8 text-yellow-500" />
            </div>
            <div>
              <p className="text-white font-semibold">My Vehicles</p>
              <p className="text-slate-400 text-sm">Manage cars</p>
            </div>
            <ChevronRight className="h-5 w-5 text-slate-500" />
          </CardContent>
        </Card>

        <Card 
          className="bg-slate-800 border-slate-700 cursor-pointer hover:border-purple-500 transition-colors" 
          onClick={() => router.push('/user/notifications')}
        >
          <CardContent className="p-6 flex flex-col items-center text-center gap-3">
            <div className="p-3 bg-purple-500/10 rounded-lg">
              <Bell className="h-8 w-8 text-purple-500" />
            </div>
            <div>
              <p className="text-white font-semibold">Notifications</p>
              <p className="text-slate-400 text-sm">Stay updated</p>
            </div>
            <ChevronRight className="h-5 w-5 text-slate-500" />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
