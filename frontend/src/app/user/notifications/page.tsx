'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Bell,
  CheckCircle2,
  XCircle,
  Clock,
  MapPin,
  CreditCard,
  Star
} from 'lucide-react';

interface Notification {
  id: string;
  type: 'booking' | 'payment' | 'reminder' | 'review';
  title: string;
  message: string;
  time: string;
  read: boolean;
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([
    {
      id: '1',
      type: 'booking',
      title: 'Booking Confirmed!',
      message: 'Your booking at Downtown Garage has been confirmed for tomorrow 2:00 PM',
      time: '2 hours ago',
      read: false,
    },
    {
      id: '2',
      type: 'payment',
      title: 'Payment Successful',
      message: 'Payment of $45.00 has been processed successfully',
      time: '5 hours ago',
      read: false,
    },
    {
      id: '3',
      type: 'reminder',
      title: 'Booking Reminder',
      message: 'You have an upcoming booking in 1 hour',
      time: '1 day ago',
      read: true,
    },
    {
      id: '4',
      type: 'review',
      title: 'Rate Your Experience',
      message: 'How was your parking at Waterfront Parking? Leave a review!',
      time: '3 days ago',
      read: true,
    },
  ]);

  const markAsRead = (id: string) => {
    setNotifications(prev => prev.map(n => n.id === id ? {...n, read: true} : n));
  };

  const getIcon = (type: string) => {
    switch(type) {
      case 'booking': return <MapPin className="h-5 w-5 text-blue-500" />;
      case 'payment': return <CreditCard className="h-5 w-5 text-green-500" />;
      case 'reminder': return <Clock className="h-5 w-5 text-yellow-500" />;
      case 'review': return <Star className="h-5 w-5 text-purple-500" />;
      default: return <Bell className="h-5 w-5 text-slate-500" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Notifications</h1>
          <p className="text-slate-400">Stay updated with your parking activities</p>
        </div>
        <button className="text-blue-400 hover:text-blue-300 text-sm">
          Mark all as read
        </button>
      </div>

      <div className="space-y-4">
        {notifications.map((notification) => (
          <Card
            key={notification.id}
            className={`bg-slate-800 border-slate-700 cursor-pointer transition-colors ${!notification.read ? 'border-l-4 border-l-blue-500' : ''}`}
            onClick={() => markAsRead(notification.id)}
          >
            <CardContent className="p-6">
              <div className="flex gap-4">
                <div className={`p-3 rounded-full ${!notification.read ? 'bg-blue-500/20' : 'bg-slate-700'}`}>
                  {getIcon(notification.type)}
                </div>
                <div className="flex-1">
                  <div className="flex justify-between items-start mb-1">
                    <p className={`font-semibold ${!notification.read ? 'text-white' : 'text-slate-300'}`}>
                      {notification.title}
                    </p>
                    <p className="text-slate-400 text-sm">{notification.time}</p>
                  </div>
                  <p className={`${!notification.read ? 'text-slate-300' : 'text-slate-400'}`}>
                    {notification.message}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
