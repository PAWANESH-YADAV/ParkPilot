'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Calendar,
  Clock,
  MapPin,
  Car,
  X,
  Plus,
  ChevronDown,
  ChevronUp,
  Clock3,
  AlertTriangle,
  CreditCard,
  Tag,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/lib/auth-context';
import { useToast } from '@/lib/toast-context';
import { cn } from '@/lib/utils';
import {
  reservationsApi,
  extractError,
  Reservation,
  ReservationStatus,
} from '@/lib/api';

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
  vehicleId?: string;
  licensePlate?: string;
  paymentMethod?: string;
  createdAt: string;
}

const reservationToBooking = (r: Reservation): Booking => {
  const start = new Date(r.start_time);
  const end = new Date(r.end_time);
  const pad = (n: number) => n.toString().padStart(2, '0');
  const dateStr = `${start.getFullYear()}-${pad(start.getMonth() + 1)}-${pad(start.getDate())}`;
  const startTimeStr = `${pad(start.getHours())}:${pad(start.getMinutes())}`;
  const endTimeStr = `${pad(end.getHours())}:${pad(end.getMinutes())}`;
  const durationHrs = Math.max(
    0.5,
    Math.round(((end.getTime() - start.getTime()) / (1000 * 60 * 60)) * 10) / 10
  );
  return {
    id: String(r.id),
    userId: String(r.user_id),
    parkingLotId: String(r.parking_lot_id ?? ''),
    parkingLotName: r.parking_lot_name ?? 'Parking Lot',
    slotNumber: r.slot_number ?? String(r.slot_id),
    date: dateStr,
    startTime: startTimeStr,
    endTime: endTimeStr,
    duration: durationHrs,
    amount: r.amount,
    status: r.status as Booking['status'],
    vehicleType: r.vehicle_type ?? 'car',
    vehicleId: r.vehicle_id ? String(r.vehicle_id) : undefined,
    licensePlate: r.license_plate,
    paymentMethod: r.payment_method,
    createdAt: r.created_at,
  };
};

const loadLocalBookings = (userId: string): Booking[] => {
  if (typeof window === 'undefined') return [];
  const all: Booking[] = JSON.parse(
    localStorage.getItem('parkpilot_bookings') || '[]'
  );
  return all
    .filter((b) => b.userId === userId)
    .sort((a, b) => (b.createdAt || '').localeCompare(a.createdAt || ''));
};

export default function BookingsPage() {
  const router = useRouter();
  const { user } = useAuth();
  const toast = useToast();
  const [activeTab, setActiveTab] = useState<
    'all' | 'upcoming' | 'active' | 'completed' | 'cancelled'
  >('all');
  const [expandedBooking, setExpandedBooking] = useState<string | null>(null);
  const [bookings, setBookings] = useState<Booking[]>([]);

  const [showCancelModal, setShowCancelModal] = useState<Booking | null>(null);
  const [showExtendModal, setShowExtendModal] = useState<Booking | null>(null);
  const [extendHours, setExtendHours] = useState(1);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [serverFallback, setServerFallback] = useState(false);

  useEffect(() => {
    refreshBookings();
  }, [user]);

  const refreshBookings = async () => {
    if (!user) return;
    setIsLoading(true);
    try {
      const list = await reservationsApi.list();
      const converted = list.map(reservationToBooking);
      converted.sort((a, b) => (b.createdAt || '').localeCompare(a.createdAt || ''));
      setBookings(converted);
      setServerFallback(false);
    } catch (err) {
      const local = loadLocalBookings(user.id);
      setBookings(local);
      setServerFallback(true);
    } finally {
      setIsLoading(false);
    }
  };

  const persistBookings = (updated: Booking[]) => {
    if (typeof window === 'undefined') return;
    const allBookings: Booking[] = JSON.parse(
      localStorage.getItem('parkpilot_bookings') || '[]'
    );
    const others = allBookings.filter((b) => b.userId !== user?.id);
    const merged = [...others, ...updated];
    localStorage.setItem('parkpilot_bookings', JSON.stringify(merged));
  };

  const updateBookingLocal = (id: string, patch: Partial<Booking>) => {
    const updated = bookings.map((b) => (b.id === id ? { ...b, ...patch } : b));
    setBookings(updated);
    persistBookings(updated);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-500';
      case 'confirmed':
        return 'bg-blue-500';
      case 'pending':
        return 'bg-yellow-500';
      case 'completed':
        return 'bg-slate-400';
      case 'cancelled':
        return 'bg-red-500';
      default:
        return 'bg-slate-500';
    }
  };

  const getStatusPill = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'confirmed':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'pending':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'completed':
        return 'bg-slate-500/20 text-slate-300 border-slate-500/30';
      case 'cancelled':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      default:
        return '';
    }
  };

  const statusCategory = (s: Booking['status']) => {
    if (s === 'confirmed' || s === 'pending') return 'upcoming';
    return s;
  };

  const filteredBookings =
    activeTab === 'all'
      ? bookings
      : bookings.filter((b) => statusCategory(b.status) === activeTab);

  const handleCancel = async () => {
    if (!showCancelModal) return;
    setIsProcessing(true);
    try {
      if (serverFallback) {
        await new Promise((r) => setTimeout(r, 600));
        updateBookingLocal(showCancelModal.id, { status: 'cancelled' });
      } else {
        await reservationsApi.cancel(parseInt(showCancelModal.id, 10));
        await refreshBookings();
      }
      toast.success(
        'Booking cancelled',
        `${showCancelModal.parkingLotName} booking has been cancelled`
      );
      setShowCancelModal(null);
    } catch (err) {
      toast.error('Failed to cancel', extractError(err));
    } finally {
      setIsProcessing(false);
    }
  };

  const handleExtend = async () => {
    if (!showExtendModal) return;
    setIsProcessing(true);
    try {
      if (serverFallback) {
        await new Promise((r) => setTimeout(r, 600));
        const b = showExtendModal;
        const [eh, em] = b.endTime.split(':').map(Number);
        const totalMin = eh * 60 + em + extendHours * 60;
        const newH = Math.floor((totalMin % (24 * 60)) / 60);
        const newM = totalMin % 60;
        const pad = (n: number) => n.toString().padStart(2, '0');
        const newEndTime = `${pad(newH)}:${pad(newM)}`;
        const extraRate = b.amount / Math.max(0.1, b.duration);
        const extraAmount = Math.round(extendHours * extraRate * 100) / 100;
        const newDuration = Math.round((b.duration + extendHours) * 10) / 10;
        const newAmount = Math.round((b.amount + extraAmount) * 100) / 100;
        updateBookingLocal(b.id, {
          endTime: newEndTime,
          duration: newDuration,
          amount: newAmount,
        });
        toast.success(
          `Extended by ${extendHours}h`,
          `New end time: ${formatTime(newEndTime)} • +$${extraAmount.toFixed(2)}`
        );
      } else {
        const updated = await reservationsApi.extend(
          parseInt(showExtendModal.id, 10),
          extendHours
        );
        const newEndTime = new Date(updated.end_time);
        const pad = (n: number) => n.toString().padStart(2, '0');
        const newEndTimeStr = `${pad(newEndTime.getHours())}:${pad(newEndTime.getMinutes())}`;
        const extraRate = showExtendModal.amount / Math.max(0.1, showExtendModal.duration);
        const extraAmount = Math.round(extendHours * extraRate * 100) / 100;
        await refreshBookings();
        toast.success(
          `Extended by ${extendHours}h`,
          `New end time: ${formatTime(newEndTimeStr)} • +$${extraAmount.toFixed(2)}`
        );
      }
      setShowExtendModal(null);
      setExtendHours(1);
    } catch (err) {
      toast.error('Failed to extend', extractError(err));
    } finally {
      setIsProcessing(false);
    }
  };

  const handleActivate = async (b: Booking) => {
    try {
      setIsProcessing(true);
      if (serverFallback) {
        updateBookingLocal(b.id, { status: 'active' });
      } else {
        await reservationsApi.updateStatus(
          parseInt(b.id, 10),
          'active' as ReservationStatus
        );
        await refreshBookings();
      }
      toast.success('Parking started', `Slot ${b.slotNumber} is now active`);
    } catch (err) {
      toast.error('Failed to start parking', extractError(err));
    } finally {
      setIsProcessing(false);
    }
  };

  const handleComplete = async (b: Booking) => {
    try {
      setIsProcessing(true);
      if (serverFallback) {
        updateBookingLocal(b.id, { status: 'completed' });
      } else {
        await reservationsApi.updateStatus(
          parseInt(b.id, 10),
          'completed' as ReservationStatus
        );
        await refreshBookings();
      }
      toast.success('Parking completed', 'Thank you for using ParkPilot');
    } catch (err) {
      toast.error('Failed to complete parking', extractError(err));
    } finally {
      setIsProcessing(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    if (date.toDateString() === today.toDateString()) return 'Today';
    if (date.toDateString() === tomorrow.toDateString()) return 'Tomorrow';
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const formatTime = (time: string) => {
    const [hour, minute] = time.split(':');
    const h = parseInt(hour);
    const ampm = h >= 12 ? 'PM' : 'AM';
    const hour12 = h % 12 || 12;
    return `${hour12}:${minute} ${ampm}`;
  };

  const paymentLabel = (m?: string) => {
    if (m === 'card') return 'Card';
    if (m === 'wallet') return 'Wallet';
    if (m === 'upi') return 'UPI';
    return '—';
  };

  const tabs = [
    { id: 'all', label: 'All' },
    { id: 'upcoming', label: 'Upcoming' },
    { id: 'active', label: 'Active' },
    { id: 'completed', label: 'Completed' },
    { id: 'cancelled', label: 'Cancelled' },
  ] as const;

  if (!user) return null;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">My Bookings</h1>
          <p className="text-slate-400">Manage your parking reservations</p>
        </div>
        <Button
          className="bg-blue-600 hover:bg-blue-700 self-start sm:self-auto"
          onClick={() => router.push('/user/find-parking')}
        >
          <Plus className="h-5 w-5 mr-2" />
          New Booking
        </Button>
      </div>

      {serverFallback && (
        <div className="flex items-start gap-3 p-4 rounded-xl bg-yellow-500/10 border border-yellow-500/30">
          <AlertCircle className="h-5 w-5 text-yellow-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="text-yellow-300 font-medium">
              Demo mode — using local data
            </p>
            <p className="text-yellow-400/80">
              Backend server is unreachable. Your changes will be stored locally.
              Start the backend server with <code className="bg-yellow-500/20 px-1 rounded">uvicorn app.main:app --port 8000</code> to enable real bookings.
            </p>
          </div>
        </div>
      )}

      <div className="flex gap-2 flex-wrap">
        {tabs.map((tab) => (
          <Button
            key={tab.id}
            variant={activeTab === tab.id ? 'default' : 'ghost'}
            className={cn(
              'text-sm capitalize',
              activeTab === tab.id
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            )}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
            <span className="ml-2 text-xs px-1.5 py-0.5 rounded bg-slate-700/80 text-slate-300">
              {tab.id === 'all'
                ? bookings.length
                : bookings.filter((b) => statusCategory(b.status) === tab.id).length}
            </span>
          </Button>
        ))}
      </div>

      <div className="space-y-4">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <Card key={i} className="bg-slate-800 border-slate-700">
              <CardContent className="p-8 space-y-4">
                <div className="h-5 bg-slate-700 rounded w-1/3 animate-pulse" />
                <div className="h-4 bg-slate-700 rounded w-2/3 animate-pulse" />
                <div className="h-4 bg-slate-700 rounded w-1/2 animate-pulse" />
              </CardContent>
            </Card>
          ))
        ) : filteredBookings.length === 0 ? (
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-12 text-center">
              <Car className="h-16 w-16 text-slate-600 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-white mb-2">
                {activeTab === 'all' ? 'No Bookings Yet' : `No ${activeTab} bookings`}
              </h3>
              <p className="text-slate-400 mb-6 max-w-md mx-auto">
                {activeTab === 'all'
                  ? "You haven't made any parking reservations yet. Find a spot and park smarter."
                  : `You don't have any ${activeTab} bookings right now.`}
              </p>
              {(activeTab === 'all' || activeTab === 'upcoming') && (
                <Button
                  className="bg-blue-600 hover:bg-blue-700"
                  onClick={() => router.push('/user/find-parking')}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Book Parking Now
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          filteredBookings.map((booking) => (
            <motion.div
              key={booking.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              layout
            >
              <Card className="bg-slate-800 border-slate-700 overflow-hidden">
                <CardHeader className="pb-3">
                  <div className="flex flex-wrap justify-between items-start gap-4">
                    <div className="flex items-start gap-3 min-w-0 flex-1">
                      <div
                        className={`w-3 h-3 rounded-full mt-1.5 flex-shrink-0 ${getStatusColor(
                          booking.status
                        )} ${booking.status === 'active' ? 'animate-pulse' : ''}`}
                      />
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2 mb-1">
                          <CardTitle className="text-xl text-white truncate">
                            {booking.parkingLotName}
                          </CardTitle>
                          <span
                            className={cn(
                              'px-2 py-0.5 rounded-full border text-xs font-medium capitalize',
                              getStatusPill(booking.status)
                            )}
                          >
                            {booking.status}
                          </span>
                        </div>
                        <p className="text-slate-400 text-sm flex items-center gap-1 flex-wrap">
                          <Tag className="h-3.5 w-3.5" />
                          Slot {booking.slotNumber}
                          <span className="text-slate-600 mx-1">•</span>
                          <Car className="h-3.5 w-3.5" />
                          {booking.vehicleType.charAt(0).toUpperCase() +
                            booking.vehicleType.slice(1)}
                          {booking.licensePlate && (
                            <>
                              <span className="text-slate-600 mx-1">•</span>
                              <span className="font-mono text-slate-300">
                                {booking.licensePlate}
                              </span>
                            </>
                          )}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-white">
                        ${booking.amount.toFixed(2)}
                      </p>
                      <p className="text-slate-400 text-sm">
                        {booking.duration}h total
                      </p>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  <div className="flex flex-wrap gap-6 text-sm">
                    <div className="flex items-center gap-2 text-slate-300">
                      <Calendar className="h-4 w-4 text-blue-500" />
                      <div>
                        <span className="text-white font-medium">
                          {formatDate(booking.date)}
                        </span>
                        <span className="text-slate-500 mx-1.5">·</span>
                        <span className="text-slate-400">{booking.date}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-slate-300">
                      <Clock className="h-4 w-4 text-green-500" />
                      <span>
                        {formatTime(booking.startTime)}
                        <span className="text-slate-500 mx-1">–</span>
                        {formatTime(booking.endTime)}
                      </span>
                    </div>
                    {booking.paymentMethod && (
                      <div className="flex items-center gap-2 text-slate-300">
                        <CreditCard className="h-4 w-4 text-purple-500" />
                        <span>Paid via {paymentLabel(booking.paymentMethod)}</span>
                      </div>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-700">
                    {booking.status === 'active' && (
                      <>
                        <Button
                          className="bg-yellow-600 hover:bg-yellow-700"
                          onClick={() => {
                            setShowExtendModal(booking);
                            setExtendHours(1);
                          }}
                          disabled={isProcessing}
                        >
                          <Clock3 className="h-4 w-4 mr-2" />
                          Extend
                        </Button>
                        <Button
                          variant="outline"
                          className="border-slate-600 text-slate-300 hover:text-white hover:bg-slate-700"
                          onClick={() => handleComplete(booking)}
                          disabled={isProcessing}
                        >
                          Complete
                        </Button>
                      </>
                    )}
                    {(booking.status === 'confirmed' ||
                      booking.status === 'pending') && (
                      <Button
                        variant="outline"
                        className="border-red-500/50 text-red-400 hover:bg-red-500/10 hover:text-red-300"
                        onClick={() => setShowCancelModal(booking)}
                        disabled={isProcessing}
                      >
                        <X className="h-4 w-4 mr-2" />
                        Cancel
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        setExpandedBooking(
                          expandedBooking === booking.id ? null : booking.id
                        )
                      }
                      className="text-slate-400 hover:text-white ml-auto"
                    >
                      {expandedBooking === booking.id ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </Button>
                  </div>

                  <AnimatePresence>
                    {expandedBooking === booking.id && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                      >
                        <div className="pt-4 border-t border-slate-700 grid sm:grid-cols-2 gap-y-2 gap-x-8 text-sm">
                          <p className="text-slate-400">
                            <span className="text-slate-300 font-medium inline-block w-32">
                              Booking ID
                            </span>
                            <span className="font-mono">{booking.id}</span>
                          </p>
                          <p className="text-slate-400">
                            <span className="text-slate-300 font-medium inline-block w-32">
                              Parking Lot ID
                            </span>
                            {booking.parkingLotId}
                          </p>
                          <p className="text-slate-400">
                            <span className="text-slate-300 font-medium inline-block w-32">
                              Created
                            </span>
                            {booking.createdAt
                              ? new Date(booking.createdAt).toLocaleString()
                              : '—'}
                          </p>
                          <p className="text-slate-400">
                            <span className="text-slate-300 font-medium inline-block w-32">
                              Vehicle
                            </span>
                            {booking.vehicleType.charAt(0).toUpperCase() +
                              booking.vehicleType.slice(1)}
                            {booking.licensePlate
                              ? ` · ${booking.licensePlate}`
                              : ''}
                          </p>
                          <p className="text-slate-400 sm:col-span-2">
                            <span className="text-slate-300 font-medium inline-block w-32">
                              Address
                            </span>
                            <MapPin className="h-3.5 w-3.5 inline text-slate-500 mr-1" />
                            {booking.parkingLotName} Parking Lot
                          </p>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </CardContent>
              </Card>
            </motion.div>
          ))
        )}
      </div>


      <AnimatePresence>
        {showCancelModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
            onClick={() => !isProcessing && setShowCancelModal(null)}
          >
            <motion.div
              initial={{ scale: 0.95, y: 20, opacity: 0 }}
              animate={{ scale: 1, y: 0, opacity: 1 }}
              exit={{ scale: 0.95, y: 20, opacity: 0 }}
              className="w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
            >
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-red-500/20 rounded-full">
                      <AlertTriangle className="h-6 w-6 text-red-400" />
                    </div>
                    <div>
                      <CardTitle className="text-xl text-white">Cancel Booking?</CardTitle>
                      <p className="text-slate-400 text-sm">
                        {showCancelModal.parkingLotName} · Slot {showCancelModal.slotNumber}
                      </p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-5 pt-4">
                  <p className="text-slate-300 text-sm">
                    This booking will be permanently cancelled. A partial refund of{' '}
                    <span className="text-white font-semibold">
                      ${(showCancelModal.amount * 0.8).toFixed(2)}
                    </span>{' '}
                    (80%) will be credited to your wallet.
                  </p>
                  <div className="flex gap-3 pt-2">
                    <Button
                      variant="outline"
                      className="flex-1 border-slate-600 text-slate-300"
                      onClick={() => setShowCancelModal(null)}
                      disabled={isProcessing}
                    >
                      Keep Booking
                    </Button>
                    <Button
                      className="flex-1 bg-red-600 hover:bg-red-700"
                      onClick={handleCancel}
                      disabled={isProcessing}
                    >
                      {isProcessing ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Cancelling...
                        </>
                      ) : (
                        <>Yes, Cancel</>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showExtendModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
            onClick={() => !isProcessing && setShowExtendModal(null)}
          >
            <motion.div
              initial={{ scale: 0.95, y: 20, opacity: 0 }}
              animate={{ scale: 1, y: 0, opacity: 1 }}
              exit={{ scale: 0.95, y: 20, opacity: 0 }}
              className="w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
            >
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-yellow-500/20 rounded-full">
                      <Clock3 className="h-6 w-6 text-yellow-400" />
                    </div>
                    <div>
                      <CardTitle className="text-xl text-white">Extend Parking</CardTitle>
                      <p className="text-slate-400 text-sm">
                        Slot {showExtendModal.slotNumber}
                      </p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-5 pt-4">
                  <div className="space-y-2">
                    <label className="text-slate-300 text-sm font-medium">
                      Extend by ({extendHours} hour{extendHours > 1 ? 's' : ''})
                    </label>
                    <input
                      type="range"
                      min={0.5}
                      max={8}
                      step={0.5}
                      value={extendHours}
                      onChange={(e) => setExtendHours(parseFloat(e.target.value))}
                      className="w-full accent-blue-500"
                    />
                    <div className="flex justify-between text-xs text-slate-500">
                      <span>30m</span>
                      <span>4h</span>
                      <span>8h</span>
                    </div>
                  </div>
                  <div className="p-4 bg-slate-700/40 rounded-lg space-y-2 text-sm">
                    <div className="flex justify-between text-slate-300">
                      <span>Current ends at</span>
                      <span className="text-white font-medium">
                        {formatTime(showExtendModal.endTime)}
                      </span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>New end time</span>
                      <span className="text-white font-medium">
                        {formatTime(
                          (() => {
                            const [eh, em] = showExtendModal.endTime.split(':').map(Number);
                            const totalMin = eh * 60 + em + extendHours * 60;
                            const newH = Math.floor((totalMin % (24 * 60)) / 60);
                            const newM = totalMin % 60;
                            const pad = (n: number) => n.toString().padStart(2, '0');
                            return `${pad(newH)}:${pad(newM)}`;
                          })()
                        )}
                      </span>
                    </div>
                    <div className="flex justify-between text-lg pt-2 mt-2 border-t border-slate-600">
                      <span className="text-slate-200 font-semibold">Extra cost</span>
                      <span className="text-green-400 font-bold">
                        +$
                        {(
                          (showExtendModal.amount /
                            Math.max(0.1, showExtendModal.duration)) *
                          extendHours
                        ).toFixed(2)}
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-3 pt-2">
                    <Button
                      variant="outline"
                      className="flex-1 border-slate-600 text-slate-300"
                      onClick={() => setShowExtendModal(null)}
                      disabled={isProcessing}
                    >
                      Cancel
                    </Button>
                    <Button
                      className="flex-1 bg-blue-600 hover:bg-blue-700"
                      onClick={handleExtend}
                      disabled={isProcessing}
                    >
                      {isProcessing ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Extending...
                        </>
                      ) : (
                        <>Confirm Extension</>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
