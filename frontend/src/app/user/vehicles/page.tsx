'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Car,
  Plus,
  Trash2,
  CheckCircle2,
  X,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/lib/auth-context';
import { useToast } from '@/lib/toast-context';
import { vehiclesApi, Vehicle as BackendVehicle, extractError } from '@/lib/api';

interface VehicleUI {
  id: string;
  licensePlate: string;
  make: string;
  model: string;
  year: number | null;
  color: string;
}

const backendToUi = (v: BackendVehicle): VehicleUI => ({
  id: String(v.id),
  licensePlate: v.license_plate,
  make: v.make ?? '',
  model: v.model ?? '',
  year: v.year ?? null,
  color: v.color ?? '',
});

const loadLocalVehicles = (userId: string): VehicleUI[] => {
  if (typeof window === 'undefined') return [];
  const raw = localStorage.getItem(`parkpilot_vehicles_${userId}`);
  if (!raw) return [];
  try {
    return JSON.parse(raw);
  } catch {
    return [];
  }
};

const saveLocalVehicles = (userId: string, list: VehicleUI[]) => {
  if (typeof window === 'undefined') return;
  localStorage.setItem(`parkpilot_vehicles_${userId}`, JSON.stringify(list));
};

export default function VehiclesPage() {
  const { user } = useAuth();
  const toast = useToast();
  const [vehicles, setVehicles] = useState<VehicleUI[]>([]);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [serverFallback, setServerFallback] = useState(false);
  const [form, setForm] = useState({
    license_plate: '',
    make: '',
    model: '',
    year: '',
    color: '',
  });
  const [formError, setFormError] = useState('');

  useEffect(() => {
    loadVehicles();
  }, [user]);

  const loadVehicles = async () => {
    if (!user) return;
    setIsLoading(true);
    try {
      const list = await vehiclesApi.list();
      setVehicles(list.map(backendToUi));
      setServerFallback(false);
    } catch (err) {
      setVehicles(loadLocalVehicles(user.id));
      setServerFallback(true);
    } finally {
      setIsLoading(false);
    }
  };

  const deleteVehicle = async (id: string) => {
    try {
      setIsProcessing(true);
      if (serverFallback) {
        const updated = vehicles.filter((v) => v.id !== id);
        setVehicles(updated);
        saveLocalVehicles(user!.id, updated);
      } else {
        await vehiclesApi.delete(parseInt(id, 10));
        await loadVehicles();
      }
      toast.success('Vehicle removed', 'Vehicle has been removed from your garage');
    } catch (err) {
      toast.error('Failed to delete', extractError(err));
    } finally {
      setIsProcessing(false);
    }
  };

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    if (!form.license_plate.trim()) {
      setFormError('License plate is required');
      return;
    }
    setIsProcessing(true);
    try {
      const payload = {
        license_plate: form.license_plate.trim().toUpperCase(),
        make: form.make.trim() || undefined,
        model: form.model.trim() || undefined,
        year: form.year ? parseInt(form.year, 10) : undefined,
        color: form.color.trim() || undefined,
      };
      if (serverFallback) {
        await new Promise((r) => setTimeout(r, 400));
        const newVehicle: VehicleUI = {
          id: `local_${Date.now()}`,
          licensePlate: payload.license_plate,
          make: payload.make ?? '',
          model: payload.model ?? '',
          year: payload.year ?? null,
          color: payload.color ?? '',
        };
        const updated = [...vehicles, newVehicle];
        setVehicles(updated);
        saveLocalVehicles(user!.id, updated);
      } else {
        await vehiclesApi.create(payload);
        await loadVehicles();
      }
      toast.success('Vehicle added', `${payload.license_plate} added to your vehicles`);
      setIsAddModalOpen(false);
      setForm({ license_plate: '', make: '', model: '', year: '', color: '' });
    } catch (err) {
      setFormError(extractError(err));
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">My Vehicles</h1>
          <p className="text-slate-400">Manage your registered vehicles</p>
        </div>
        <Button
          className="bg-blue-600 hover:bg-blue-700"
          onClick={() => {
            setFormError('');
            setForm({ license_plate: '', make: '', model: '', year: '', color: '' });
            setIsAddModalOpen(true);
          }}
        >
          <Plus className="h-5 w-5 mr-2" />
          Add Vehicle
        </Button>
      </div>

      {serverFallback && (
        <div className="flex items-start gap-3 p-4 rounded-xl bg-yellow-500/10 border border-yellow-500/30">
          <AlertCircle className="h-5 w-5 text-yellow-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="text-yellow-300 font-medium">Demo mode — using local data</p>
            <p className="text-yellow-400/80">
              Backend server is unreachable. Your vehicles are stored locally.
            </p>
          </div>
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-6">
        {isLoading ? (
          Array.from({ length: 2 }).map((_, i) => (
            <Card key={i} className="bg-slate-800 border-slate-700">
              <CardContent className="p-8 space-y-4">
                <div className="h-6 bg-slate-700 rounded w-1/2 animate-pulse" />
                <div className="h-4 bg-slate-700 rounded w-1/3 animate-pulse" />
                <div className="h-4 bg-slate-700 rounded w-2/3 animate-pulse" />
              </CardContent>
            </Card>
          ))
        ) : vehicles.length === 0 ? (
          <Card className="bg-slate-800 border-slate-700 md:col-span-2">
            <CardContent className="p-12 text-center">
              <Car className="h-16 w-16 text-slate-600 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-white mb-2">No Vehicles Yet</h3>
              <p className="text-slate-400 mb-6 max-w-md mx-auto">
                Add your first vehicle to speed up booking.
              </p>
              <Button
                className="bg-blue-600 hover:bg-blue-700"
                onClick={() => setIsAddModalOpen(true)}
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Vehicle
              </Button>
            </CardContent>
          </Card>
        ) : (
          vehicles.map((vehicle) => (
            <motion.div
              key={vehicle.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              layout
            >
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="pb-3">
                  <div className="flex justify-between items-start">
                    <div className="flex items-center gap-3">
                      <div className="p-3 bg-blue-500/10 rounded-lg">
                        <Car className="h-8 w-8 text-blue-500" />
                      </div>
                      <div>
                        <CardTitle className="text-xl text-white">
                          {vehicle.make || 'Vehicle'}
                          {vehicle.make && vehicle.model ? ` ${vehicle.model}` : vehicle.model || ''}
                        </CardTitle>
                        <p className="text-slate-400 text-sm font-mono">
                          {vehicle.licensePlate}
                        </p>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    {vehicle.year !== null && (
                      <div>
                        <p className="text-slate-400">Year</p>
                        <p className="text-white font-medium">{vehicle.year}</p>
                      </div>
                    )}
                    {vehicle.color && (
                      <div>
                        <p className="text-slate-400">Color</p>
                        <p className="text-white font-medium">{vehicle.color}</p>
                      </div>
                    )}
                    {!vehicle.year && !vehicle.color && (
                      <div className="col-span-2">
                        <p className="text-slate-500 text-sm">No additional details</p>
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2 pt-2 border-t border-slate-700">
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-red-500 text-red-500 ml-auto"
                      onClick={() => deleteVehicle(vehicle.id)}
                      disabled={isProcessing}
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))
        )}
      </div>

      <AnimatePresence>
        {isAddModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
            onClick={() => !isProcessing && setIsAddModalOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.95, y: 20, opacity: 0 }}
              animate={{ scale: 1, y: 0, opacity: 1 }}
              exit={{ scale: 0.95, y: 20, opacity: 0 }}
              className="w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
            >
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-2xl text-white">Add New Vehicle</CardTitle>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsAddModalOpen(false)}
                    disabled={isProcessing}
                    className="text-slate-400 hover:text-white"
                  >
                    <X className="h-5 w-5" />
                  </Button>
                </CardHeader>
                <CardContent className="space-y-4 pt-2">
                  {formError && (
                    <div className="p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-400 text-sm flex items-start gap-2">
                      <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                      {formError}
                    </div>
                  )}
                  <form onSubmit={handleAddSubmit} className="space-y-4">
                    <div className="space-y-1.5">
                      <Label className="text-slate-300">License Plate *</Label>
                      <Input
                        placeholder="e.g. ABC-1234"
                        value={form.license_plate}
                        onChange={(e) =>
                          setForm({ ...form, license_plate: e.target.value })
                        }
                        className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-500 uppercase"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-1.5">
                        <Label className="text-slate-300">Make</Label>
                        <Input
                          placeholder="e.g. Toyota"
                          value={form.make}
                          onChange={(e) => setForm({ ...form, make: e.target.value })}
                          className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-500"
                        />
                      </div>
                      <div className="space-y-1.5">
                        <Label className="text-slate-300">Model</Label>
                        <Input
                          placeholder="e.g. Camry"
                          value={form.model}
                          onChange={(e) => setForm({ ...form, model: e.target.value })}
                          className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-500"
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-1.5">
                        <Label className="text-slate-300">Year</Label>
                        <Input
                          type="number"
                          min={1900}
                          max={2100}
                          placeholder="2024"
                          value={form.year}
                          onChange={(e) => setForm({ ...form, year: e.target.value })}
                          className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-500"
                        />
                      </div>
                      <div className="space-y-1.5">
                        <Label className="text-slate-300">Color</Label>
                        <Input
                          placeholder="e.g. Silver"
                          value={form.color}
                          onChange={(e) => setForm({ ...form, color: e.target.value })}
                          className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-500"
                        />
                      </div>
                    </div>
                    <div className="flex gap-3 pt-2">
                      <Button
                        type="button"
                        variant="outline"
                        className="flex-1 border-slate-600 text-slate-300"
                        onClick={() => setIsAddModalOpen(false)}
                        disabled={isProcessing}
                      >
                        Cancel
                      </Button>
                      <Button
                        type="submit"
                        className="flex-1 bg-blue-600 hover:bg-blue-700"
                        disabled={isProcessing}
                      >
                        {isProcessing ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Adding...
                          </>
                        ) : (
                          <>
                            <CheckCircle2 className="h-4 w-4 mr-2" />
                            Add Vehicle
                          </>
                        )}
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
