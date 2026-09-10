'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  MapPin,
  Search,
  Filter,
  Star,
  DollarSign,
  Car,
  Navigation,
  Heart,
  X,
  Calendar,
  Clock,
  Check,
  CreditCard,
  Truck,
  Bike,
  ChevronRight,
  ChevronLeft,
  Loader2,
  ShieldCheck,
  Receipt,
  AlertCircle,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/lib/auth-context';
import { useToast } from '@/lib/toast-context';
import { cn } from '@/lib/utils';
import {
  parkingApi,
  reservationsApi,
  vehiclesApi,
  ParkingLot as ParkingLotApi,
  Reservation,
  extractError,
} from '@/lib/api';

interface ParkingLot {
  id: string;
  name: string;
  address: string;
  distance: string;
  price: string;
  pricePerHour: number;
  rating: number;
  totalSlots: number;
  availableSlots: number;
  vehicleTypes: string[];
  features: string[];
  image?: string;
  _backendId: number;
}

type BookingStep = 'details' | 'vehicle' | 'payment' | 'success';

const FALLBACK_DISTANCES = ['0.5 km', '1.2 km', '2.0 km', '1.8 km', '8.5 km', '3.2 km'];

const toFrontendLot = (lot: ParkingLotApi, idx: number): ParkingLot => ({
  id: `lot-${lot.id}`,
  _backendId: lot.id,
  name: lot.name,
  address: lot.address || '',
  distance: lot.distance || FALLBACK_DISTANCES[idx % FALLBACK_DISTANCES.length],
  price: `$${lot.price_per_hour.toFixed(0)}/hr`,
  pricePerHour: lot.price_per_hour,
  rating: lot.rating ?? 4.5,
  totalSlots: lot.total_slots,
  availableSlots: lot.available_slots ?? 0,
  vehicleTypes: lot.vehicle_types?.length ? lot.vehicle_types : ['car'],
  features: lot.features || [],
});

const toIsoDate = (date: string, time: string) => {
  const ymd = date || new Date().toISOString().slice(0, 10);
  const hhmm = time || '00:00';
  return new Date(`${ymd}T${hhmm}:00`).toISOString();
};

export default function FindParking() {
  const router = useRouter();
  const { user } = useAuth();
  const toast = useToast();

  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('distance');
  const [vehicleTypeFilter, setVehicleTypeFilter] = useState('all');
  const [favoriteLots, setFavoriteLots] = useState<string[]>([]);
  const [selectedLot, setSelectedLot] = useState<ParkingLot | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [step, setStep] = useState<BookingStep>('details');
  const [isBooking, setIsBooking] = useState(false);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [isLoadingLots, setIsLoadingLots] = useState(true);
  const [lotsError, setLotsError] = useState<string | null>(null);
  const [serverFallback, setServerFallback] = useState(false);
  const [lastCreatedBooking, setLastCreatedBooking] =
    useState<Reservation | null>(null);

  const [bookingData, setBookingData] = useState({
    date: new Date().toISOString().split('T')[0],
    startTime: '',
    endTime: '',
    vehicleType: 'car',
    vehicleId: '',
    licensePlate: '',
    paymentMethod: 'card',
  });

  const [parkingLots, setParkingLots] = useState<ParkingLot[]>([]);
  const [userVehicles, setUserVehicles] = useState<
    { id: number; make?: string; model?: string; license_plate: string }[]
  >([]);

  useEffect(() => {
    let alive = true;
    (async () => {
      setIsLoadingLots(true);
      setLotsError(null);
      try {
        const lots = await parkingApi.getLots();
        if (!alive) return;
        const frontend = lots.map(toFrontendLot);
        setParkingLots(frontend);
        setServerFallback(false);
      } catch (err) {
        if (!alive) return;
        setLotsError(extractError(err));
        setServerFallback(true);
        const hardcoded: ParkingLot[] = [
          {
            id: '1',
            _backendId: 1,
            name: 'Downtown Garage',
            address: '123 Main St, Downtown',
            distance: '0.5 km',
            price: '$15/hr',
            pricePerHour: 15,
            rating: 4.8,
            totalSlots: 150,
            availableSlots: 45,
            vehicleTypes: ['car', 'bike'],
            features: ['24/7', 'Security', 'EV Charging'],
          },
          {
            id: '2',
            _backendId: 2,
            name: 'City Center Parking',
            address: '456 Oak Ave, City Center',
            distance: '1.2 km',
            price: '$12/hr',
            pricePerHour: 12,
            rating: 4.5,
            totalSlots: 100,
            availableSlots: 23,
            vehicleTypes: ['car'],
            features: ['24/7', 'Security'],
          },
          {
            id: '3',
            _backendId: 3,
            name: 'Waterfront Parking',
            address: '789 River Rd, Waterfront',
            distance: '2.0 km',
            price: '$10/hr',
            pricePerHour: 10,
            rating: 4.6,
            totalSlots: 200,
            availableSlots: 67,
            vehicleTypes: ['car', 'bike', 'suv'],
            features: ['24/7', 'Security', 'EV Charging', 'Wash'],
          },
          {
            id: '4',
            _backendId: 4,
            name: 'Uptown Plaza',
            address: '321 Park Blvd, Uptown',
            distance: '1.8 km',
            price: '$18/hr',
            pricePerHour: 18,
            rating: 4.9,
            totalSlots: 120,
            availableSlots: 8,
            vehicleTypes: ['car', 'bike'],
            features: ['24/7', 'Security', 'EV Charging', 'Valet'],
          },
          {
            id: '5',
            _backendId: 5,
            name: 'Airport Long Stay',
            address: '999 Airport Rd',
            distance: '8.5 km',
            price: '$8/hr',
            pricePerHour: 8,
            rating: 4.3,
            totalSlots: 500,
            availableSlots: 210,
            vehicleTypes: ['car', 'suv'],
            features: ['24/7', 'Shuttle', 'Security', 'Covered'],
          },
          {
            id: '6',
            _backendId: 6,
            name: 'Mall Parking',
            address: '500 Shopping Ave',
            distance: '3.2 km',
            price: '$5/hr',
            pricePerHour: 5,
            rating: 4.1,
            totalSlots: 350,
            availableSlots: 142,
            vehicleTypes: ['car', 'bike'],
            features: ['Security', 'Covered', 'Handicap Access'],
          },
        ];
        setParkingLots(hardcoded);
      } finally {
        if (alive) setIsLoadingLots(false);
      }
    })();

    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    if (!user) return;
    const favKey = `parkpilot_favorites_${user.id}`;
    const favs = JSON.parse(localStorage.getItem(favKey) || '[]');
    setFavoriteLots(favs);

    if (!serverFallback) {
      vehiclesApi
        .list()
        .then((vs) => setUserVehicles(vs))
        .catch(() => {});
    } else {
      const legacy = JSON.parse(
        localStorage.getItem(`parkpilot_vehicles_${user.id}`) || '[]'
      );
      setUserVehicles(legacy);
    }
  }, [user, serverFallback]);

  const toggleFavorite = (id: string) => {
    if (!user) {
      toast.warning('Please login', 'You need to be signed in to save favorites');
      return;
    }
    const newFavs = favoriteLots.includes(id)
      ? favoriteLots.filter((x) => x !== id)
      : [...favoriteLots, id];
    setFavoriteLots(newFavs);
    localStorage.setItem(
      `parkpilot_favorites_${user.id}`,
      JSON.stringify(newFavs)
    );
    toast.success(
      favoriteLots.includes(id) ? 'Removed from favorites' : 'Added to favorites'
    );
  };

  const openBookingModal = (lot: ParkingLot) => {
    if (
      !lot.vehicleTypes.includes(bookingData.vehicleType) &&
      vehicleTypeFilter !== 'all'
    ) {
      setBookingData({ ...bookingData, vehicleType: lot.vehicleTypes[0] });
    }
    const now = new Date();
    const rounded = new Date(now.getTime() + 30 * 60000);
    rounded.setMinutes(rounded.getMinutes() >= 30 ? 0 : 0);
    rounded.setHours(rounded.getHours() + 1);
    const later = new Date(rounded.getTime() + 2 * 3600000);
    const pad = (n: number) => n.toString().padStart(2, '0');
    setSelectedLot(lot);
    setBookingData({
      ...bookingData,
      startTime: `${pad(rounded.getHours())}:${pad(rounded.getMinutes())}`,
      endTime: `${pad(later.getHours())}:${pad(later.getMinutes())}`,
      vehicleType: lot.vehicleTypes.includes(bookingData.vehicleType)
        ? bookingData.vehicleType
        : lot.vehicleTypes[0],
      vehicleId: '',
      licensePlate: '',
      paymentMethod: 'card',
    });
    setStep('details');
    setFormErrors({});
    setLastCreatedBooking(null);
    setShowModal(true);
  };

  const closeModal = () => {
    if (isBooking) return;
    setShowModal(false);
    setTimeout(() => {
      setStep('details');
      setSelectedLot(null);
      setIsBooking(false);
      setFormErrors({});
    }, 200);
  };

  const calculateDuration = useMemo(() => {
    if (!bookingData.startTime || !bookingData.endTime) return 0;
    const [sh, sm] = bookingData.startTime.split(':').map(Number);
    const [eh, em] = bookingData.endTime.split(':').map(Number);
    const startMin = sh * 60 + sm;
    const endMin = eh * 60 + em;
    let durationMin = endMin - startMin;
    if (durationMin < 0) durationMin += 24 * 60;
    const duration = Math.max(0.5, durationMin / 60);
    return Math.round(duration * 10) / 10;
  }, [bookingData.startTime, bookingData.endTime]);

  const calculateAmount = useMemo(() => {
    if (!selectedLot) return 0;
    const base = selectedLot.pricePerHour * calculateDuration;
    const fees = base * 0.05;
    const total = base + fees;
    return Math.round(total * 100) / 100;
  }, [selectedLot, calculateDuration]);

  const validateStep = (s: BookingStep): boolean => {
    const errors: Record<string, string> = {};
    const today = new Date().toISOString().split('T')[0];

    if (s === 'details') {
      if (!bookingData.date) errors.date = 'Date is required';
      else if (bookingData.date < today) errors.date = 'Cannot book past dates';

      if (!bookingData.startTime) errors.startTime = 'Start time is required';
      if (!bookingData.endTime) errors.endTime = 'End time is required';

      if (bookingData.date === today && bookingData.startTime) {
        const now = new Date();
        const [h, m] = bookingData.startTime.split(':').map(Number);
        const st = new Date();
        st.setHours(h, m, 0, 0);
        if (st.getTime() < now.getTime() - 5 * 60000) {
          errors.startTime = 'Start time has already passed';
        }
      }

      if (bookingData.startTime && bookingData.endTime) {
        const [sh, sm] = bookingData.startTime.split(':').map(Number);
        const [eh, em] = bookingData.endTime.split(':').map(Number);
        const sMin = sh * 60 + sm;
        const eMin = eh * 60 + em;
        if (eMin <= sMin) errors.endTime = 'End time must be after start time';
      }

      if (calculateDuration < 0.5) errors.endTime = 'Minimum duration is 30 minutes';
      if (calculateDuration > 24) errors.endTime = 'Maximum booking is 24 hours';
    }

    if (s === 'vehicle') {
      if (!bookingData.vehicleType) errors.vehicleType = 'Vehicle type required';
      if (
        selectedLot &&
        !selectedLot.vehicleTypes.includes(bookingData.vehicleType)
      ) {
        errors.vehicleType = `${bookingData.vehicleType} not allowed at this lot`;
      }
      if (userVehicles.length === 0 && !bookingData.licensePlate.trim()) {
        errors.licensePlate = 'Enter license plate or add a vehicle first';
      }
    }

    if (s === 'payment') {
      if (!bookingData.paymentMethod) errors.paymentMethod = 'Select payment method';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const nextStep = () => {
    const current: BookingStep = step;
    if (!validateStep(current)) return;
    if (current === 'details') setStep('vehicle');
    else if (current === 'vehicle') setStep('payment');
    else if (current === 'payment') handleBooking();
  };

  const prevStep = () => {
    if (step === 'vehicle') setStep('details');
    else if (step === 'payment') setStep('vehicle');
  };

  const handleBooking = async () => {
    if (!user || !selectedLot) return;
    setIsBooking(true);

    try {
      let created: Reservation | null = null;
      if (serverFallback) {
        await new Promise((r) => setTimeout(r, 1200));
      } else {
        try {
          const vehicleIdInt = bookingData.vehicleId
            ? Number(bookingData.vehicleId)
            : undefined;
          created = await reservationsApi.book({
            parking_lot_id: selectedLot._backendId,
            start_time: toIsoDate(bookingData.date, bookingData.startTime),
            end_time: toIsoDate(bookingData.date, bookingData.endTime),
            license_plate: bookingData.licensePlate || undefined,
            vehicle_type: (bookingData.vehicleType as any) || 'car',
            payment_method: (bookingData.paymentMethod as any) || 'card',
            vehicle_id:
              vehicleIdInt && !Number.isNaN(vehicleIdInt)
                ? vehicleIdInt
                : undefined,
            amount: calculateAmount,
          });
        } catch (err) {
          toast.error('Booking failed', extractError(err));
          setIsBooking(false);
          return;
        }
      }

      const amount = calculateAmount;
      const duration = calculateDuration;
      const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
      const prefix = alphabet[Math.floor(Math.random() * 26)];
      const slot =
        created?.slot_number ||
        `${prefix}-${String(
          Math.floor(Math.random() * Math.min(selectedLot.totalSlots, 50)) + 1
        ).padStart(2, '0')}`;

      if (!created) {
        const existingBookings = JSON.parse(
          localStorage.getItem('parkpilot_bookings') || '[]'
        );
        const fallbackBooking = {
          id: `BK-${Date.now()}`,
          userId: user.id,
          parkingLotId: selectedLot._backendId,
          parkingLotName: selectedLot.name,
          slotNumber: slot,
          date: bookingData.date,
          startTime: bookingData.startTime,
          endTime: bookingData.endTime,
          duration,
          amount,
          status: 'confirmed',
          vehicleType: bookingData.vehicleType,
          vehicleId: bookingData.vehicleId || undefined,
          licensePlate: bookingData.licensePlate || undefined,
          paymentMethod: bookingData.paymentMethod,
          createdAt: new Date().toISOString(),
        };
        existingBookings.push(fallbackBooking);
        localStorage.setItem(
          'parkpilot_bookings',
          JSON.stringify(existingBookings)
        );
      } else {
        setLastCreatedBooking(created);
      }

      setStep('success');
      setIsBooking(false);
      toast.success(
        'Booking confirmed!',
        `Slot ${slot} at ${selectedLot.name}`
      );

      setTimeout(() => {
        setShowModal(false);
        router.push('/user/bookings');
      }, 2500);
    } catch (err) {
      setIsBooking(false);
      toast.error('Booking failed', extractError(err));
    }
  };

  const filteredAndSorted = useMemo(() => {
    let lots = parkingLots.filter((lot) => {
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        if (
          !lot.name.toLowerCase().includes(q) &&
          !lot.address.toLowerCase().includes(q)
        )
          return false;
      }
      if (
        vehicleTypeFilter !== 'all' &&
        !lot.vehicleTypes.includes(vehicleTypeFilter)
      )
        return false;
      return true;
    });
    lots = [...lots].sort((a, b) => {
      if (sortBy === 'price-low') return a.pricePerHour - b.pricePerHour;
      if (sortBy === 'price-high') return b.pricePerHour - a.pricePerHour;
      if (sortBy === 'rating') return b.rating - a.rating;
      if (sortBy === 'availability')
        return b.availableSlots / b.totalSlots - a.availableSlots / a.totalSlots;
      return parseFloat(a.distance) - parseFloat(b.distance);
    });
    return lots;
  }, [parkingLots, searchQuery, vehicleTypeFilter, sortBy]);

  const stepNumber: Record<BookingStep, number> = {
    details: 1,
    vehicle: 2,
    payment: 3,
    success: 4,
  };

  const VehicleIcon = ({ type }: { type: string }) => {
    if (type === 'bike') return <Bike className="h-5 w-5" />;
    if (type === 'truck' || type === 'suv') return <Truck className="h-5 w-5" />;
    return <Car className="h-5 w-5" />;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Find Parking</h1>
        <p className="text-slate-400">Search and book parking spots near you</p>
      </div>

      <Card className="bg-slate-800 border-slate-700">
        <CardContent className="p-6 space-y-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
              <Input
                placeholder="Search location or parking lot..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-slate-700 border-slate-600 text-white placeholder:text-slate-400"
              />
            </div>
            <Button
              variant="outline"
              className="border-slate-600 text-slate-300"
            >
              <Filter className="h-5 w-5 mr-2" />
              Filters
            </Button>
          </div>
          <div className="flex flex-wrap gap-3">
            <select
              value={vehicleTypeFilter}
              onChange={(e) => setVehicleTypeFilter(e.target.value)}
              className="px-4 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Vehicle Types</option>
              <option value="car">Car</option>
              <option value="bike">Bike</option>
              <option value="suv">SUV / Truck</option>
            </select>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-4 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="distance">Sort: Distance</option>
              <option value="price-low">Sort: Price Low to High</option>
              <option value="price-high">Sort: Price High to Low</option>
              <option value="rating">Sort: Rating</option>
              <option value="availability">Sort: Availability</option>
            </select>
            {serverFallback && (
              <span className="inline-flex items-center gap-2 px-3 py-2 bg-yellow-500/10 text-yellow-400 rounded-md text-xs border border-yellow-500/30">
                <AlertCircle className="h-4 w-4" />
                Demo mode (backend offline)
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      {isLoadingLots ? (
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-12 text-center">
            <Loader2 className="h-12 w-12 text-blue-500 animate-spin mx-auto mb-4" />
            <p className="text-slate-400">Loading parking lots...</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredAndSorted.map((lot, idx) => (
            <motion.div
              key={lot.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
            >
              <Card className="bg-slate-800 border-slate-700 overflow-hidden h-full flex flex-col hover:border-slate-600 transition-all group">
                <CardHeader className="pb-3">
                  <div className="flex justify-between items-start gap-2">
                    <div className="min-w-0 flex-1">
                      <CardTitle className="text-xl text-white truncate group-hover:text-blue-400 transition-colors">
                        {lot.name}
                      </CardTitle>
                      <p className="text-slate-400 text-sm flex items-center gap-1 mt-1">
                        <MapPin className="h-4 w-4 flex-shrink-0" />
                        <span className="truncate">{lot.address}</span>
                        <span className="text-slate-500 flex-shrink-0">
                          • {lot.distance}
                        </span>
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleFavorite(lot.id);
                      }}
                      className={cn(
                        'flex-shrink-0',
                        favoriteLots.includes(lot.id)
                          ? 'text-red-500'
                          : 'text-slate-400'
                      )}
                    >
                      <Heart
                        className="h-5 w-5"
                        fill={
                          favoriteLots.includes(lot.id)
                            ? 'currentColor'
                            : 'none'
                        }
                      />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4 flex-1 flex flex-col">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div
                        className={cn(
                          'w-3 h-3 rounded-full',
                          lot.availableSlots > 30
                            ? 'bg-green-500'
                            : lot.availableSlots > 10
                            ? 'bg-yellow-500'
                            : 'bg-red-500'
                        )}
                      />
                      <span className="text-white font-medium text-sm">
                        {lot.availableSlots}/{lot.totalSlots} slots
                      </span>
                    </div>
                    <div className="flex items-center gap-1 text-yellow-400 text-sm">
                      <Star className="h-4 w-4" fill="currentColor" />
                      <span className="font-medium">{lot.rating}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {lot.vehicleTypes.map((vt) => (
                      <span
                        key={vt}
                        className="p-1.5 bg-slate-700 rounded-md text-slate-300"
                        title={vt}
                      >
                        <VehicleIcon type={vt} />
                      </span>
                    ))}
                  </div>

                  <div className="flex flex-wrap gap-1.5">
                    {lot.features.map((f) => (
                      <span
                        key={f}
                        className="px-2.5 py-1 bg-slate-700/70 rounded-full text-xs text-slate-300"
                      >
                        {f}
                      </span>
                    ))}
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t border-slate-700 mt-auto">
                    <div>
                      <p className="text-2xl font-bold text-white">
                        {lot.price}
                      </p>
                      <p className="text-slate-400 text-xs">per hour</p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="border-slate-600 text-slate-300"
                      >
                        <Navigation className="h-4 w-4" />
                      </Button>
                      <Button
                        className="bg-blue-600 hover:bg-blue-700"
                        onClick={() => openBookingModal(lot)}
                        disabled={lot.availableSlots === 0}
                      >
                        {lot.availableSlots === 0 ? 'Full' : 'Book Now'}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      {!isLoadingLots && filteredAndSorted.length === 0 && (
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-12 text-center">
            <Search className="h-16 w-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-white mb-2">
              No parking lots found
            </h3>
            <p className="text-slate-400">
              Try adjusting your search filters or vehicle type.
            </p>
          </CardContent>
        </Card>
      )}

      <AnimatePresence>
        {showModal && selectedLot && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
            onClick={closeModal}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 20 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col"
              onClick={(e) => e.stopPropagation()}
            >
              <Card className="bg-slate-800 border-slate-700 w-full flex flex-col max-h-[90vh] overflow-hidden">
                <CardHeader className="flex flex-row items-center justify-between pb-2 flex-shrink-0 border-b border-slate-700">
                  <div>
                    <CardTitle className="text-xl text-white">
                      {step === 'success'
                        ? 'Booking Confirmed!'
                        : `Book - ${selectedLot.name}`}
                    </CardTitle>
                    {step !== 'success' && (
                      <p className="text-slate-400 text-sm mt-1">
                        {selectedLot.address}
                      </p>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={closeModal}
                    disabled={isBooking || step === 'success'}
                    className="text-slate-400 hover:text-white flex-shrink-0"
                  >
                    <X className="h-5 w-5" />
                  </Button>
                </CardHeader>

                {step !== 'success' && (
                  <div className="px-6 py-4 flex-shrink-0 border-b border-slate-700">
                    <div className="flex items-center justify-between max-w-md mx-auto">
                      {(['details', 'vehicle', 'payment'] as const).map(
                        (s, i) => (
                          <div key={s} className="flex items-center">
                            <div
                              className={cn(
                                'h-9 w-9 rounded-full flex items-center justify-center font-semibold text-sm transition-all',
                                stepNumber[step] >= i + 1
                                  ? 'bg-blue-600 text-white'
                                  : 'bg-slate-700 text-slate-400'
                              )}
                            >
                              {stepNumber[step] > i + 1 ? (
                                <Check className="h-4 w-4" />
                              ) : (
                                i + 1
                              )}
                            </div>
                            {i < 2 && (
                              <div
                                className={cn(
                                  'w-10 sm:w-16 h-0.5 mx-2',
                                  stepNumber[step] > i + 1
                                    ? 'bg-blue-600'
                                    : 'bg-slate-700'
                                )}
                              />
                            )}
                          </div>
                        )
                      )}
                    </div>
                    <div className="flex justify-between max-w-md mx-auto mt-2 text-xs">
                      <span
                        className={cn(
                          'text-center w-20',
                          step === 'details'
                            ? 'text-blue-400'
                            : 'text-slate-500'
                        )}
                      >
                        Details
                      </span>
                      <span
                        className={cn(
                          'text-center w-20',
                          step === 'vehicle'
                            ? 'text-blue-400'
                            : 'text-slate-500'
                        )}
                      >
                        Vehicle
                      </span>
                      <span
                        className={cn(
                          'text-center w-20',
                          step === 'payment'
                            ? 'text-blue-400'
                            : 'text-slate-500'
                        )}
                      >
                        Payment
                      </span>
                    </div>
                  </div>
                )}

                <CardContent className="flex-1 overflow-y-auto pt-6 space-y-5">
                  {step === 'details' && (
                    <motion.div
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      className="space-y-5"
                    >
                      <div className="p-4 bg-slate-700/50 rounded-lg border border-slate-600">
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="text-white font-semibold">
                              {selectedLot.name}
                            </p>
                            <p className="text-slate-400 text-sm">
                              {selectedLot.address}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-white font-bold text-lg">
                              {selectedLot.price}
                            </p>
                            <p className="text-slate-400 text-xs">per hour</p>
                          </div>
                        </div>
                        <div className="flex flex-wrap gap-2 mt-3">
                          {selectedLot.features.slice(0, 3).map((f) => (
                            <span
                              key={f}
                              className="px-2 py-0.5 bg-slate-600/70 rounded text-xs text-slate-300"
                            >
                              {f}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="space-y-2">
                        <label className="text-slate-300 text-sm font-medium">
                          Date
                        </label>
                        <div className="relative">
                          <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                          <Input
                            type="date"
                            value={bookingData.date}
                            onChange={(e) =>
                              setBookingData({
                                ...bookingData,
                                date: e.target.value,
                              })
                            }
                            className={cn(
                              'pl-10 bg-slate-700 border-slate-600 text-white',
                              formErrors.date &&
                                'border-red-500 focus-visible:ring-red-500'
                            )}
                            min={new Date().toISOString().split('T')[0]}
                          />
                        </div>
                        {formErrors.date && (
                          <p className="text-red-400 text-xs">
                            {formErrors.date}
                          </p>
                        )}
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <label className="text-slate-300 text-sm font-medium">
                            Start Time
                          </label>
                          <div className="relative">
                            <Clock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                            <Input
                              type="time"
                              value={bookingData.startTime}
                              onChange={(e) =>
                                setBookingData({
                                  ...bookingData,
                                  startTime: e.target.value,
                                })
                              }
                              className={cn(
                                'pl-10 bg-slate-700 border-slate-600 text-white',
                                formErrors.startTime &&
                                  'border-red-500 focus-visible:ring-red-500'
                              )}
                            />
                          </div>
                          {formErrors.startTime && (
                            <p className="text-red-400 text-xs">
                              {formErrors.startTime}
                            </p>
                          )}
                        </div>
                        <div className="space-y-2">
                          <label className="text-slate-300 text-sm font-medium">
                            End Time
                          </label>
                          <div className="relative">
                            <Clock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                            <Input
                              type="time"
                              value={bookingData.endTime}
                              onChange={(e) =>
                                setBookingData({
                                  ...bookingData,
                                  endTime: e.target.value,
                                })
                              }
                              className={cn(
                                'pl-10 bg-slate-700 border-slate-600 text-white',
                                formErrors.endTime &&
                                  'border-red-500 focus-visible:ring-red-500'
                              )}
                            />
                          </div>
                          {formErrors.endTime && (
                            <p className="text-red-400 text-xs">
                              {formErrors.endTime}
                            </p>
                          )}
                        </div>
                      </div>

                      <div className="pt-4 border-t border-slate-700 space-y-2.5">
                        <div className="flex justify-between text-slate-300 text-sm">
                          <span>Duration</span>
                          <span className="font-medium">
                            {calculateDuration} hour(s)
                          </span>
                        </div>
                        <div className="flex justify-between text-slate-300 text-sm">
                          <span>Rate ({selectedLot.price}/hr)</span>
                          <span className="font-medium">
                            $
                            {(
                              selectedLot.pricePerHour * calculateDuration
                            ).toFixed(2)}
                          </span>
                        </div>
                        <div className="flex justify-between text-slate-400 text-sm">
                          <span>Service fee (5%)</span>
                          <span>
                            $
                            {(
                              selectedLot.pricePerHour *
                              calculateDuration *
                              0.05
                            ).toFixed(2)}
                          </span>
                        </div>
                        <div className="flex justify-between text-xl font-bold text-white pt-2 border-t border-slate-700">
                          <span>Total</span>
                          <span>${calculateAmount.toFixed(2)}</span>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {step === 'vehicle' && (
                    <motion.div
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      className="space-y-5"
                    >
                      <div className="space-y-2">
                        <label className="text-slate-300 text-sm font-medium">
                          Vehicle Type
                        </label>
                        <div className="grid grid-cols-3 gap-3">
                          {selectedLot.vehicleTypes.map((vt) => (
                            <button
                              key={vt}
                              type="button"
                              onClick={() =>
                                setBookingData({
                                  ...bookingData,
                                  vehicleType: vt,
                                })
                              }
                              className={cn(
                                'p-4 rounded-lg border-2 flex flex-col items-center gap-2 transition-all',
                                bookingData.vehicleType === vt
                                  ? 'border-blue-500 bg-blue-500/10 text-white'
                                  : 'border-slate-600 bg-slate-700/30 text-slate-300 hover:border-slate-500'
                              )}
                            >
                              <VehicleIcon type={vt} />
                              <span className="text-sm font-medium capitalize">
                                {vt}
                              </span>
                            </button>
                          ))}
                        </div>
                        {formErrors.vehicleType && (
                          <p className="text-red-400 text-xs">
                            {formErrors.vehicleType}
                          </p>
                        )}
                      </div>

                      {userVehicles.length > 0 && (
                        <div className="space-y-2">
                          <label className="text-slate-300 text-sm font-medium">
                            Saved Vehicle (optional)
                          </label>
                          <select
                            value={bookingData.vehicleId}
                            onChange={(e) => {
                              const vId = e.target.value;
                              const v = userVehicles.find(
                                (x) => String(x.id) === vId
                              );
                              setBookingData({
                                ...bookingData,
                                vehicleId: vId,
                                licensePlate:
                                  v?.license_plate ||
                                  bookingData.licensePlate,
                              });
                            }}
                            className="w-full px-4 py-2.5 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                          >
                            <option value="">
                              + Enter license plate manually
                            </option>
                            {userVehicles.map((v) => (
                              <option key={v.id} value={v.id}>
                                {v.make || 'Vehicle'} {v.model || ''} —{' '}
                                {v.license_plate}
                              </option>
                            ))}
                          </select>
                        </div>
                      )}

                      <div className="space-y-2">
                        <label className="text-slate-300 text-sm font-medium">
                          License Plate Number
                        </label>
                        <Input
                          placeholder="e.g. ABC 1234"
                          value={bookingData.licensePlate}
                          onChange={(e) =>
                            setBookingData({
                              ...bookingData,
                              licensePlate: e.target.value.toUpperCase(),
                            })
                          }
                          className={cn(
                            'bg-slate-700 border-slate-600 text-white font-mono uppercase',
                            formErrors.licensePlate &&
                              'border-red-500 focus-visible:ring-red-500'
                          )}
                        />
                        {formErrors.licensePlate && (
                          <p className="text-red-400 text-xs">
                            {formErrors.licensePlate}
                          </p>
                        )}
                      </div>

                      <div className="p-4 bg-slate-700/50 rounded-lg border border-slate-600">
                        <div className="flex items-center gap-2 mb-3">
                          <Receipt className="h-5 w-5 text-blue-400" />
                          <span className="text-white font-semibold">
                            Booking summary
                          </span>
                        </div>
                        <div className="space-y-1.5 text-sm">
                          <div className="flex justify-between text-slate-300">
                            <span>Date & Time</span>
                            <span>
                              {bookingData.date}, {bookingData.startTime} –{' '}
                              {bookingData.endTime}
                            </span>
                          </div>
                          <div className="flex justify-between text-slate-300">
                            <span>Duration</span>
                            <span>{calculateDuration}h</span>
                          </div>
                          <div className="flex justify-between text-white font-semibold pt-2 border-t border-slate-600 mt-2">
                            <span>Total payable</span>
                            <span>${calculateAmount.toFixed(2)}</span>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {step === 'payment' && (
                    <motion.div
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      className="space-y-5"
                    >
                      <div className="space-y-3">
                        <label className="text-slate-300 text-sm font-medium">
                          Payment Method
                        </label>
                        {[
                          {
                            id: 'card',
                            name: 'Credit / Debit Card',
                            icon: CreditCard,
                          },
                          {
                            id: 'wallet',
                            name: 'ParkPilot Wallet',
                            icon: DollarSign,
                          },
                          { id: 'upi', name: 'UPI', icon: Receipt },
                        ].map((method) => (
                          <button
                            key={method.id}
                            type="button"
                            onClick={() =>
                              setBookingData({
                                ...bookingData,
                                paymentMethod: method.id,
                              })
                            }
                            className={cn(
                              'w-full p-4 rounded-lg border-2 flex items-center gap-4 transition-all',
                              bookingData.paymentMethod === method.id
                                ? 'border-blue-500 bg-blue-500/10'
                                : 'border-slate-600 bg-slate-700/30 hover:border-slate-500'
                            )}
                          >
                            <method.icon
                              className={cn(
                                'h-6 w-6',
                                bookingData.paymentMethod === method.id
                                  ? 'text-blue-400'
                                  : 'text-slate-400'
                              )}
                            />
                            <span className="text-white font-medium flex-1 text-left">
                              {method.name}
                            </span>
                            <div
                              className={cn(
                                'h-5 w-5 rounded-full border-2 flex items-center justify-center',
                                bookingData.paymentMethod === method.id
                                  ? 'border-blue-500'
                                  : 'border-slate-500'
                              )}
                            >
                              {bookingData.paymentMethod === method.id && (
                                <div className="h-2.5 w-2.5 rounded-full bg-blue-500" />
                              )}
                            </div>
                          </button>
                        ))}
                        {formErrors.paymentMethod && (
                          <p className="text-red-400 text-xs">
                            {formErrors.paymentMethod}
                          </p>
                        )}
                      </div>

                      {bookingData.paymentMethod === 'card' && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          className="space-y-4 p-4 bg-slate-700/30 rounded-lg border border-slate-600"
                        >
                          <div className="space-y-2">
                            <label className="text-slate-300 text-sm font-medium">
                              Card Number
                            </label>
                            <Input
                              placeholder="1234 5678 9012 3456"
                              className="bg-slate-700 border-slate-600 text-white font-mono"
                              maxLength={19}
                              onChange={(e) => {
                                let v = e.target.value.replace(/\D/g, '');
                                v = v.match(/.{1,4}/g)?.join(' ') || v;
                                e.target.value = v;
                              }}
                            />
                          </div>
                          <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                              <label className="text-slate-300 text-sm font-medium">
                                Expiry (MM/YY)
                              </label>
                              <Input
                                placeholder="12/28"
                                className="bg-slate-700 border-slate-600 text-white font-mono"
                                maxLength={5}
                                onChange={(e) => {
                                  let v = e.target.value.replace(/\D/g, '');
                                  if (v.length >= 2)
                                    v = v.slice(0, 2) + '/' + v.slice(2, 4);
                                  e.target.value = v;
                                }}
                              />
                            </div>
                            <div className="space-y-2">
                              <label className="text-slate-300 text-sm font-medium">
                                CVV
                              </label>
                              <Input
                                placeholder="123"
                                type="password"
                                className="bg-slate-700 border-slate-600 text-white font-mono"
                                maxLength={4}
                              />
                            </div>
                          </div>
                        </motion.div>
                      )}

                      <div className="p-4 bg-gradient-to-br from-blue-600/20 to-cyan-600/20 rounded-lg border border-blue-500/30">
                        <div className="flex items-center gap-2 mb-3">
                          <ShieldCheck className="h-5 w-5 text-blue-400" />
                          <span className="text-white font-semibold">
                            Payment Summary
                          </span>
                        </div>
                        <div className="space-y-1.5 text-sm">
                          <div className="flex justify-between text-slate-300">
                            <span>
                              Parking ({calculateDuration}h × $
                              {selectedLot.pricePerHour})
                            </span>
                            <span>
                              $
                              {(
                                selectedLot.pricePerHour * calculateDuration
                              ).toFixed(2)}
                            </span>
                          </div>
                          <div className="flex justify-between text-slate-300">
                            <span>Service fee</span>
                            <span>
                              $
                              {(
                                selectedLot.pricePerHour *
                                calculateDuration *
                                0.05
                              ).toFixed(2)}
                            </span>
                          </div>
                          <div className="flex justify-between text-xl font-bold text-white pt-3 border-t border-slate-700 mt-2">
                            <span>Total</span>
                            <span>${calculateAmount.toFixed(2)}</span>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {step === 'success' && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ type: 'spring', damping: 20 }}
                      className="py-6 text-center space-y-6"
                    >
                      <div className="relative mx-auto w-24 h-24">
                        <div className="absolute inset-0 bg-green-500/20 rounded-full animate-ping" />
                        <div className="relative h-24 w-24 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center mx-auto">
                          <Check
                            className="h-12 w-12 text-white"
                            strokeWidth={3}
                          />
                        </div>
                      </div>
                      <div>
                        <h3 className="text-2xl font-bold text-white mb-1">
                          Booking Confirmed!
                        </h3>
                        <p className="text-slate-400">
                          Your slot has been reserved successfully
                        </p>
                      </div>
                      <div className="p-5 bg-slate-700/50 rounded-xl border border-slate-600 text-left max-w-sm mx-auto space-y-3">
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">Booking ID</span>
                          <span className="text-white font-mono font-semibold">
                            {lastCreatedBooking?.id
                              ? `BK-${lastCreatedBooking.id}`
                              : `BK-${Date.now()}`}
                          </span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">Location</span>
                          <span className="text-white font-medium text-right">
                            {lastCreatedBooking?.parking_lot_name ||
                              selectedLot.name}
                          </span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">Slot</span>
                          <span className="text-white font-medium">
                            {lastCreatedBooking?.slot_number ||
                              `${bookingData.vehicleType.toUpperCase()} AREA`}
                          </span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">Date</span>
                          <span className="text-white font-medium">
                            {bookingData.date}
                          </span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">Time</span>
                          <span className="text-white font-medium">
                            {bookingData.startTime} – {bookingData.endTime}
                          </span>
                        </div>
                        <div className="flex justify-between text-lg pt-3 mt-3 border-t border-slate-600">
                          <span className="text-slate-300 font-semibold">
                            Amount Paid
                          </span>
                          <span className="text-green-400 font-bold">
                            ${calculateAmount.toFixed(2)}
                          </span>
                        </div>
                      </div>
                      <p className="text-slate-500 text-sm animate-pulse">
                        Redirecting to your bookings...
                      </p>
                    </motion.div>
                  )}
                </CardContent>

                {step !== 'success' && (
                  <div className="px-6 py-4 border-t border-slate-700 flex-shrink-0 flex gap-3">
                    <Button
                      variant="outline"
                      className="flex-1 border-slate-600 text-slate-300"
                      onClick={step === 'details' ? closeModal : prevStep}
                      disabled={isBooking}
                    >
                      {step === 'details' ? (
                        'Cancel'
                      ) : (
                        <>
                          <ChevronLeft className="h-4 w-4 mr-2" />
                          Back
                        </>
                      )}
                    </Button>
                    <Button
                      className="flex-1 bg-blue-600 hover:bg-blue-700"
                      onClick={nextStep}
                      disabled={isBooking}
                    >
                      {isBooking ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Processing...
                        </>
                      ) : step === 'payment' ? (
                        <>
                          <CreditCard className="h-4 w-4 mr-2" />
                          Pay ${calculateAmount.toFixed(2)}
                        </>
                      ) : (
                        <>
                          Continue
                          <ChevronRight className="h-4 w-4 ml-2" />
                        </>
                      )}
                    </Button>
                  </div>
                )}
              </Card>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
