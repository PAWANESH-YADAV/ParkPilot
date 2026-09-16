"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  MapPin, Plus, Edit2, Trash2, Clock, Users, Car,
  X, CheckCircle2, AlertCircle, Building2, Hash, Layers,
} from "lucide-react";

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

const EMPTY_FORM = {
  name: "",
  address: "",
  capacity: "",
  operatingHours: "",
  status: "active" as "active" | "inactive",
  zones: "",
};

export default function ParkingLotManagementPage() {
  const [lots, setLots] = useState<ParkingLot[]>([
    { id: "1", name: "Downtown Garage", address: "123 Main St", capacity: 150, occupied: 98, status: "active", operatingHours: "24/7", zones: ["A", "B", "C"] },
    { id: "2", name: "City Center Parking", address: "456 Oak Ave", capacity: 100, occupied: 45, status: "active", operatingHours: "6AM - 12AM", zones: ["X", "Y"] },
    { id: "3", name: "Waterfront Parking", address: "789 River Rd", capacity: 200, occupied: 120, status: "active", operatingHours: "24/7", zones: ["P", "Q", "R", "S"] },
  ]);

  const [modalOpen, setModalOpen] = useState(false);
  const [editingLot, setEditingLot] = useState<ParkingLot | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [successMsg, setSuccessMsg] = useState("");

  // ── Open Add Modal ──────────────────────────────────────────────
  const openAddModal = () => {
    setEditingLot(null);
    setForm(EMPTY_FORM);
    setErrors({});
    setModalOpen(true);
  };

  // ── Open Edit Modal ─────────────────────────────────────────────
  const openEditModal = (lot: ParkingLot) => {
    setEditingLot(lot);
    setForm({
      name: lot.name,
      address: lot.address,
      capacity: String(lot.capacity),
      operatingHours: lot.operatingHours,
      status: lot.status,
      zones: lot.zones.join(", "),
    });
    setErrors({});
    setModalOpen(true);
  };

  // ── Validate ────────────────────────────────────────────────────
  const validate = () => {
    const e: Record<string, string> = {};
    if (!form.name.trim()) e.name = "Lot name is required.";
    if (!form.address.trim()) e.address = "Address is required.";
    if (!form.capacity || isNaN(Number(form.capacity)) || Number(form.capacity) <= 0)
      e.capacity = "Enter a valid capacity (number > 0).";
    if (!form.operatingHours.trim()) e.operatingHours = "Operating hours are required.";
    if (!form.zones.trim()) e.zones = "Enter at least one zone (e.g. A, B, C).";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  // ── Save (Add or Edit) ──────────────────────────────────────────
  const handleSave = () => {
    if (!validate()) return;
    const zonesArr = form.zones
      .split(",")
      .map((z) => z.trim().toUpperCase())
      .filter(Boolean);

    if (editingLot) {
      setLots((prev) =>
        prev.map((l) =>
          l.id === editingLot.id
            ? {
                ...l,
                name: form.name.trim(),
                address: form.address.trim(),
                capacity: Number(form.capacity),
                operatingHours: form.operatingHours.trim(),
                status: form.status,
                zones: zonesArr,
              }
            : l
        )
      );
      flash("Parking lot updated successfully!");
    } else {
      const newLot: ParkingLot = {
        id: Date.now().toString(),
        name: form.name.trim(),
        address: form.address.trim(),
        capacity: Number(form.capacity),
        occupied: 0,
        status: form.status,
        operatingHours: form.operatingHours.trim(),
        zones: zonesArr,
      };
      setLots((prev) => [newLot, ...prev]);
      flash("New parking lot added successfully!");
    }
    setModalOpen(false);
  };

  // ── Delete ──────────────────────────────────────────────────────
  const handleDelete = (id: string) => {
    setLots((prev) => prev.filter((l) => l.id !== id));
    setDeleteId(null);
    flash("Parking lot deleted.");
  };

  const flash = (msg: string) => {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(""), 3000);
  };

  return (
    <div className="space-y-6 relative">

      {/* ── Success Toast ─────────────────────────────────────── */}
      {successMsg && (
        <div className="fixed top-6 right-6 z-50 flex items-center gap-3 bg-green-500 text-white px-5 py-3 rounded-2xl shadow-2xl animate-in slide-in-from-top-4 duration-300">
          <CheckCircle2 className="h-5 w-5 flex-shrink-0" />
          <span className="text-sm font-medium">{successMsg}</span>
        </div>
      )}

      {/* ── Page Header ──────────────────────────────────────── */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
            Parking Lot Management
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Manage all parking locations
          </p>
        </div>
        <Button
          onClick={openAddModal}
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-5 py-2.5 rounded-xl shadow-lg flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Add New Lot
        </Button>
      </div>

      {/* ── Lot Cards ────────────────────────────────────────── */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {lots.map((lot) => {
          const pct = Math.round((lot.occupied / lot.capacity) * 100);
          return (
            <Card
              key={lot.id}
              className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-sm hover:shadow-md transition-shadow"
            >
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-lg font-bold text-slate-900 dark:text-white">
                      {lot.name}
                    </CardTitle>
                    <p className="text-slate-500 dark:text-slate-400 text-sm flex items-center gap-1 mt-1">
                      <MapPin className="h-3.5 w-3.5" />
                      {lot.address}
                    </p>
                  </div>
                  <span
                    className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                      lot.status === "active"
                        ? "bg-green-100 dark:bg-green-500/20 text-green-700 dark:text-green-400"
                        : "bg-red-100 dark:bg-red-500/20 text-red-700 dark:text-red-400"
                    }`}
                  >
                    {lot.status}
                  </span>
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                {/* Stats */}
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="flex items-center gap-2">
                    <Car className="h-4 w-4 text-blue-500" />
                    <span className="text-slate-500 dark:text-slate-400">Capacity:</span>
                    <span className="font-semibold text-slate-900 dark:text-white">{lot.capacity}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-green-500" />
                    <span className="text-slate-500 dark:text-slate-400">Occupied:</span>
                    <span className="font-semibold text-slate-900 dark:text-white">{lot.occupied}</span>
                  </div>
                </div>

                {/* Occupancy Bar */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400">
                    <span>Occupancy</span>
                    <span className={pct >= 80 ? "text-red-500 font-semibold" : pct >= 50 ? "text-yellow-500 font-semibold" : "text-green-500 font-semibold"}>
                      {pct}%
                    </span>
                  </div>
                  <div className="h-2 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        pct >= 80 ? "bg-red-500" : pct >= 50 ? "bg-yellow-500" : "bg-green-500"
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>

                {/* Hours */}
                <div className="flex items-center gap-2 text-sm">
                  <Clock className="h-4 w-4 text-yellow-500" />
                  <span className="text-slate-500 dark:text-slate-400">Hours:</span>
                  <span className="text-slate-900 dark:text-white font-medium">{lot.operatingHours}</span>
                </div>

                {/* Zones */}
                <div className="flex flex-wrap gap-1.5">
                  {lot.zones.map((zone) => (
                    <span
                      key={zone}
                      className="px-2.5 py-0.5 bg-slate-100 dark:bg-slate-700 rounded-full text-xs font-medium text-slate-600 dark:text-slate-300"
                    >
                      Zone {zone}
                    </span>
                  ))}
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-2 border-t border-slate-100 dark:border-slate-700">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => openEditModal(lot)}
                    className="flex-1 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-500/10 hover:text-blue-700 dark:hover:text-blue-300 rounded-xl"
                  >
                    <Edit2 className="h-4 w-4 mr-1.5" />
                    Edit
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setDeleteId(lot.id)}
                    className="flex-1 text-red-500 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 hover:text-red-700 dark:hover:text-red-300 rounded-xl"
                  >
                    <Trash2 className="h-4 w-4 mr-1.5" />
                    Delete
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* ══════════════════════════════════════════════════════════
          ADD / EDIT MODAL
      ══════════════════════════════════════════════════════════ */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setModalOpen(false)}
          />

          {/* Modal Card */}
          <div className="relative z-10 w-full max-w-lg bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-700 overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/60">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 dark:bg-blue-600/20 rounded-xl">
                  <Building2 className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                    {editingLot ? "Edit Parking Lot" : "Add New Parking Lot"}
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {editingLot ? "Update the details below" : "Fill in the details to create a new lot"}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setModalOpen(false)}
                className="p-2 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="px-6 py-5 space-y-4 max-h-[70vh] overflow-y-auto">

              {/* Lot Name */}
              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                  <Building2 className="h-3.5 w-3.5 text-blue-500" />
                  Lot Name <span className="text-red-500">*</span>
                </label>
                <Input
                  placeholder="e.g. Downtown Garage"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className={`rounded-xl border ${errors.name ? "border-red-400 focus:ring-red-400" : "border-slate-200 dark:border-slate-700"} bg-white dark:bg-slate-800 text-slate-900 dark:text-white`}
                />
                {errors.name && (
                  <p className="text-xs text-red-500 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />{errors.name}
                  </p>
                )}
              </div>

              {/* Address */}
              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                  <MapPin className="h-3.5 w-3.5 text-blue-500" />
                  Address <span className="text-red-500">*</span>
                </label>
                <Input
                  placeholder="e.g. 123 Main Street"
                  value={form.address}
                  onChange={(e) => setForm({ ...form, address: e.target.value })}
                  className={`rounded-xl border ${errors.address ? "border-red-400" : "border-slate-200 dark:border-slate-700"} bg-white dark:bg-slate-800 text-slate-900 dark:text-white`}
                />
                {errors.address && (
                  <p className="text-xs text-red-500 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />{errors.address}
                  </p>
                )}
              </div>

              {/* Capacity + Status row */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                    <Hash className="h-3.5 w-3.5 text-blue-500" />
                    Capacity <span className="text-red-500">*</span>
                  </label>
                  <Input
                    type="number"
                    min="1"
                    placeholder="e.g. 150"
                    value={form.capacity}
                    onChange={(e) => setForm({ ...form, capacity: e.target.value })}
                    className={`rounded-xl border ${errors.capacity ? "border-red-400" : "border-slate-200 dark:border-slate-700"} bg-white dark:bg-slate-800 text-slate-900 dark:text-white`}
                  />
                  {errors.capacity && (
                    <p className="text-xs text-red-500 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />{errors.capacity}
                    </p>
                  )}
                </div>

                <div className="space-y-1.5">
                  <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                    Status
                  </label>
                  <select
                    value={form.status}
                    onChange={(e) => setForm({ ...form, status: e.target.value as "active" | "inactive" })}
                    className="w-full h-10 px-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                  </select>
                </div>
              </div>

              {/* Operating Hours */}
              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5 text-blue-500" />
                  Operating Hours <span className="text-red-500">*</span>
                </label>
                <Input
                  placeholder="e.g. 24/7  or  6AM - 12AM"
                  value={form.operatingHours}
                  onChange={(e) => setForm({ ...form, operatingHours: e.target.value })}
                  className={`rounded-xl border ${errors.operatingHours ? "border-red-400" : "border-slate-200 dark:border-slate-700"} bg-white dark:bg-slate-800 text-slate-900 dark:text-white`}
                />
                {errors.operatingHours && (
                  <p className="text-xs text-red-500 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />{errors.operatingHours}
                  </p>
                )}
              </div>

              {/* Zones */}
              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                  <Layers className="h-3.5 w-3.5 text-blue-500" />
                  Zones <span className="text-red-500">*</span>
                </label>
                <Input
                  placeholder="e.g. A, B, C  (comma-separated)"
                  value={form.zones}
                  onChange={(e) => setForm({ ...form, zones: e.target.value })}
                  className={`rounded-xl border ${errors.zones ? "border-red-400" : "border-slate-200 dark:border-slate-700"} bg-white dark:bg-slate-800 text-slate-900 dark:text-white`}
                />
                {errors.zones && (
                  <p className="text-xs text-red-500 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />{errors.zones}
                  </p>
                )}
                {form.zones.trim() && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {form.zones.split(",").map((z, i) =>
                      z.trim() ? (
                        <span key={i} className="px-2.5 py-0.5 bg-blue-100 dark:bg-blue-600/20 rounded-full text-xs font-medium text-blue-700 dark:text-blue-300">
                          Zone {z.trim().toUpperCase()}
                        </span>
                      ) : null
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40">
              <Button
                variant="ghost"
                onClick={() => setModalOpen(false)}
                className="rounded-xl px-5 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
              >
                Cancel
              </Button>
              <Button
                onClick={handleSave}
                className="rounded-xl px-6 bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow"
              >
                {editingLot ? "Save Changes" : "Add Lot"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════
          DELETE CONFIRM MODAL
      ══════════════════════════════════════════════════════════ */}
      {deleteId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setDeleteId(null)}
          />
          <div className="relative z-10 w-full max-w-sm bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-700 p-6 space-y-5">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-red-100 dark:bg-red-500/20 rounded-xl">
                <Trash2 className="h-5 w-5 text-red-600 dark:text-red-400" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900 dark:text-white text-lg">Delete Parking Lot</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400">This action cannot be undone.</p>
              </div>
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-300">
              Are you sure you want to delete{" "}
              <span className="font-semibold text-slate-900 dark:text-white">
                {lots.find((l) => l.id === deleteId)?.name}
              </span>
              ?
            </p>
            <div className="flex gap-3">
              <Button
                variant="ghost"
                className="flex-1 rounded-xl border border-slate-200 dark:border-slate-700"
                onClick={() => setDeleteId(null)}
              >
                Cancel
              </Button>
              <Button
                className="flex-1 rounded-xl bg-red-600 hover:bg-red-700 text-white font-semibold"
                onClick={() => handleDelete(deleteId)}
              >
                Delete
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
