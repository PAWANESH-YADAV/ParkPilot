"use client";

import { useState, useMemo } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Car, Bike, Zap, Accessibility,
  Plus, Edit2, Trash2, Wrench,
  CheckCircle2, XCircle, X,
  AlertCircle, Hash, Layers,
  LayoutGrid, Filter, CheckCheck,
} from "lucide-react";

// ── Types ────────────────────────────────────────────────────────────────────
type SlotType = "car" | "bike" | "ev" | "disabled";
type SlotStatus = "available" | "occupied" | "maintenance";

interface Slot {
  id: string;
  number: string;
  lot: string;
  zone: string;
  type: SlotType;
  status: SlotStatus;
}

const EMPTY_FORM = {
  number: "",
  lot: "Downtown Garage",
  zone: "",
  type: "car" as SlotType,
  status: "available" as SlotStatus,
};

const LOTS = ["Downtown Garage", "City Center Parking", "Waterfront Parking"];

const TYPE_META: Record<SlotType, { label: string; icon: React.ReactNode; color: string }> = {
  car:      { label: "Car",      icon: <Car className="h-5 w-5" />,           color: "text-blue-500" },
  bike:     { label: "Bike",     icon: <Bike className="h-5 w-5" />,          color: "text-purple-500" },
  ev:       { label: "EV",       icon: <Zap className="h-5 w-5" />,           color: "text-green-500" },
  disabled: { label: "Disabled", icon: <Accessibility className="h-5 w-5" />, color: "text-orange-500" },
};

const STATUS_META: Record<SlotStatus, { label: string; bg: string; dot: string }> = {
  available:   { label: "Available",   bg: "bg-green-100 dark:bg-green-500/20 text-green-700 dark:text-green-400",   dot: "bg-green-500" },
  occupied:    { label: "Occupied",    bg: "bg-red-100 dark:bg-red-500/20 text-red-700 dark:text-red-400",           dot: "bg-red-500" },
  maintenance: { label: "Maintenance", bg: "bg-yellow-100 dark:bg-yellow-500/20 text-yellow-700 dark:text-yellow-400", dot: "bg-yellow-500" },
};

const BORDER_COLOR: Record<SlotStatus, string> = {
  available:   "border-l-green-500",
  occupied:    "border-l-red-500",
  maintenance: "border-l-yellow-500",
};

// ── Seed Data ────────────────────────────────────────────────────────────────
const SEED: Slot[] = [
  { id: "1", number: "A-01", lot: "Downtown Garage",    zone: "A", type: "car",      status: "occupied" },
  { id: "2", number: "A-02", lot: "Downtown Garage",    zone: "A", type: "car",      status: "available" },
  { id: "3", number: "A-03", lot: "Downtown Garage",    zone: "A", type: "ev",       status: "available" },
  { id: "4", number: "B-01", lot: "Downtown Garage",    zone: "B", type: "disabled", status: "available" },
  { id: "5", number: "B-02", lot: "Downtown Garage",    zone: "B", type: "bike",     status: "maintenance" },
  { id: "6", number: "C-01", lot: "City Center Parking",zone: "C", type: "car",      status: "available" },
  { id: "7", number: "X-01", lot: "City Center Parking",zone: "X", type: "ev",       status: "occupied" },
  { id: "8", number: "P-01", lot: "Waterfront Parking", zone: "P", type: "car",      status: "available" },
];

// ── Component ─────────────────────────────────────────────────────────────────
export default function ParkingSlotManagementPage() {
  const [slots, setSlots] = useState<Slot[]>(SEED);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingSlot, setEditingSlot] = useState<Slot | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [successMsg, setSuccessMsg] = useState("");

  // Filters
  const [filterLot, setFilterLot] = useState("All");
  const [filterStatus, setFilterStatus] = useState("All");
  const [filterType, setFilterType] = useState("All");

  // ── Filter slots ────────────────────────────────────────────────
  const filtered = useMemo(() => {
    return slots.filter((s) => {
      if (filterLot !== "All" && s.lot !== filterLot) return false;
      if (filterStatus !== "All" && s.status !== filterStatus) return false;
      if (filterType !== "All" && s.type !== filterType) return false;
      return true;
    });
  }, [slots, filterLot, filterStatus, filterType]);

  // Stats
  const total = slots.length;
  const available = slots.filter((s) => s.status === "available").length;
  const occupied = slots.filter((s) => s.status === "occupied").length;
  const maintenance = slots.filter((s) => s.status === "maintenance").length;

  // ── Open modals ─────────────────────────────────────────────────
  const openAdd = () => {
    setEditingSlot(null);
    setForm(EMPTY_FORM);
    setErrors({});
    setModalOpen(true);
  };

  const openEdit = (slot: Slot) => {
    setEditingSlot(slot);
    setForm({ number: slot.number, lot: slot.lot, zone: slot.zone, type: slot.type, status: slot.status });
    setErrors({});
    setModalOpen(true);
  };

  // ── Validate ────────────────────────────────────────────────────
  const validate = () => {
    const e: Record<string, string> = {};
    if (!form.number.trim()) e.number = "Slot number is required.";
    else if (slots.some((s) => s.number.toLowerCase() === form.number.trim().toLowerCase() && s.id !== editingSlot?.id))
      e.number = "Slot number already exists.";
    if (!form.zone.trim()) e.zone = "Zone is required.";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  // ── Save ────────────────────────────────────────────────────────
  const handleSave = () => {
    if (!validate()) return;
    if (editingSlot) {
      setSlots((prev) =>
        prev.map((s) =>
          s.id === editingSlot.id
            ? { ...s, number: form.number.trim().toUpperCase(), lot: form.lot, zone: form.zone.trim().toUpperCase(), type: form.type, status: form.status }
            : s
        )
      );
      flash("Slot updated successfully!");
    } else {
      setSlots((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          number: form.number.trim().toUpperCase(),
          lot: form.lot,
          zone: form.zone.trim().toUpperCase(),
          type: form.type,
          status: form.status,
        },
      ]);
      flash("New slot added successfully!");
    }
    setModalOpen(false);
  };

  // ── Delete ──────────────────────────────────────────────────────
  const handleDelete = (id: string) => {
    setSlots((prev) => prev.filter((s) => s.id !== id));
    setDeleteId(null);
    flash("Slot deleted.");
  };

  const flash = (msg: string) => {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(""), 3000);
  };

  // ── Render ───────────────────────────────────────────────────────
  return (
    <div className="space-y-6 relative">

      {/* Toast */}
      {successMsg && (
        <div className="fixed top-6 right-6 z-50 flex items-center gap-3 bg-green-500 text-white px-5 py-3 rounded-2xl shadow-2xl">
          <CheckCheck className="h-5 w-5 flex-shrink-0" />
          <span className="text-sm font-medium">{successMsg}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Parking Slot Management</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">Manage individual parking slots</p>
        </div>
        <Button
          onClick={openAdd}
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-5 py-2.5 rounded-xl shadow-lg flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Add New Slot
        </Button>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: "Total Slots", value: total, color: "bg-blue-50 dark:bg-blue-600/10 text-blue-700 dark:text-blue-300", dot: "bg-blue-500" },
          { label: "Available",   value: available,   color: "bg-green-50 dark:bg-green-600/10 text-green-700 dark:text-green-300", dot: "bg-green-500" },
          { label: "Occupied",    value: occupied,    color: "bg-red-50 dark:bg-red-600/10 text-red-700 dark:text-red-300", dot: "bg-red-500" },
          { label: "Maintenance", value: maintenance, color: "bg-yellow-50 dark:bg-yellow-600/10 text-yellow-700 dark:text-yellow-300", dot: "bg-yellow-500" },
        ].map((s) => (
          <div key={s.label} className={`flex items-center gap-3 px-4 py-3 rounded-xl ${s.color} border border-current/10`}>
            <span className={`w-2.5 h-2.5 rounded-full ${s.dot} flex-shrink-0`} />
            <div>
              <p className="text-xl font-bold leading-none">{s.value}</p>
              <p className="text-xs font-medium opacity-70 mt-0.5">{s.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center p-4 bg-white dark:bg-slate-800/60 rounded-2xl border border-slate-200 dark:border-slate-700">
        <Filter className="h-4 w-4 text-slate-400 flex-shrink-0" />
        <div className="flex flex-wrap gap-2 flex-1">
          {/* Lot filter */}
          <select
            value={filterLot}
            onChange={(e) => setFilterLot(e.target.value)}
            className="h-8 px-3 rounded-lg text-sm border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="All">All Lots</option>
            {LOTS.map((l) => <option key={l}>{l}</option>)}
          </select>
          {/* Status filter */}
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="h-8 px-3 rounded-lg text-sm border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="All">All Status</option>
            <option value="available">Available</option>
            <option value="occupied">Occupied</option>
            <option value="maintenance">Maintenance</option>
          </select>
          {/* Type filter */}
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="h-8 px-3 rounded-lg text-sm border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="All">All Types</option>
            <option value="car">Car</option>
            <option value="bike">Bike</option>
            <option value="ev">EV</option>
            <option value="disabled">Disabled</option>
          </select>
        </div>
        <span className="text-xs text-slate-400 font-medium">{filtered.length} slot{filtered.length !== 1 ? "s" : ""}</span>
      </div>

      {/* Slot Grid */}
      {filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-slate-400 dark:text-slate-500">
          <LayoutGrid className="h-12 w-12 mb-3 opacity-30" />
          <p className="text-lg font-medium">No slots found</p>
          <p className="text-sm">Try changing the filters or add a new slot.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {filtered.map((slot) => {
            const sm = STATUS_META[slot.status];
            const tm = TYPE_META[slot.type];
            return (
              <Card
                key={slot.id}
                className={`bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 border-l-4 ${BORDER_COLOR[slot.status]} rounded-xl shadow-sm hover:shadow-md transition-shadow`}
              >
                <CardContent className="p-4 text-center space-y-2">
                  {/* Status icon */}
                  <div className="flex justify-center">
                    {slot.status === "available"
                      ? <CheckCircle2 className="h-6 w-6 text-green-500" />
                      : slot.status === "occupied"
                      ? <XCircle className="h-6 w-6 text-red-500" />
                      : <Wrench className="h-6 w-6 text-yellow-500" />}
                  </div>

                  {/* Slot number */}
                  <p className="font-bold text-base text-slate-900 dark:text-white tracking-wide">{slot.number}</p>

                  {/* Status badge */}
                  <span className={`inline-block text-xs font-semibold px-2 py-0.5 rounded-full ${sm.bg}`}>
                    {sm.label}
                  </span>

                  {/* Type + Zone */}
                  <div className="flex items-center justify-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                    <span className={tm.color}>{tm.icon}</span>
                    <span>{tm.label}</span>
                    <span className="text-slate-300 dark:text-slate-600">•</span>
                    <span>Z-{slot.zone}</span>
                  </div>

                  {/* Lot name (truncated) */}
                  <p className="text-[10px] text-slate-400 dark:text-slate-500 truncate px-1">{slot.lot}</p>

                  {/* Actions */}
                  <div className="flex gap-1 justify-center pt-1">
                    <button
                      onClick={() => openEdit(slot)}
                      className="flex-1 h-7 flex items-center justify-center rounded-lg text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-500/10 transition-colors"
                    >
                      <Edit2 className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => setDeleteId(slot.id)}
                      className="flex-1 h-7 flex items-center justify-center rounded-lg text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════
          ADD / EDIT MODAL
      ══════════════════════════════════════════════════════════ */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setModalOpen(false)} />

          <div className="relative z-10 w-full max-w-md bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-700 overflow-hidden">

            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/60">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 dark:bg-blue-600/20 rounded-xl">
                  <Car className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                    {editingSlot ? "Edit Parking Slot" : "Add New Parking Slot"}
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {editingSlot ? "Update slot details below" : "Fill in the details to create a new slot"}
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
            <div className="px-6 py-5 space-y-4 max-h-[65vh] overflow-y-auto">

              {/* Slot Number */}
              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                  <Hash className="h-3.5 w-3.5 text-blue-500" />
                  Slot Number <span className="text-red-500">*</span>
                </label>
                <Input
                  placeholder="e.g. A-01 or B-12"
                  value={form.number}
                  onChange={(e) => setForm({ ...form, number: e.target.value })}
                  className={`rounded-xl border ${errors.number ? "border-red-400" : "border-slate-200 dark:border-slate-700"} bg-white dark:bg-slate-800 text-slate-900 dark:text-white uppercase`}
                />
                {errors.number && (
                  <p className="text-xs text-red-500 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />{errors.number}
                  </p>
                )}
              </div>

              {/* Parking Lot */}
              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                  <Layers className="h-3.5 w-3.5 text-blue-500" />
                  Parking Lot <span className="text-red-500">*</span>
                </label>
                <select
                  value={form.lot}
                  onChange={(e) => setForm({ ...form, lot: e.target.value })}
                  className="w-full h-10 px-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {LOTS.map((l) => <option key={l}>{l}</option>)}
                </select>
              </div>

              {/* Zone + Type row */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                    <Layers className="h-3.5 w-3.5 text-blue-500" />
                    Zone <span className="text-red-500">*</span>
                  </label>
                  <Input
                    placeholder="e.g. A"
                    value={form.zone}
                    onChange={(e) => setForm({ ...form, zone: e.target.value })}
                    className={`rounded-xl border ${errors.zone ? "border-red-400" : "border-slate-200 dark:border-slate-700"} bg-white dark:bg-slate-800 text-slate-900 dark:text-white uppercase`}
                  />
                  {errors.zone && (
                    <p className="text-xs text-red-500 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />{errors.zone}
                    </p>
                  )}
                </div>

                <div className="space-y-1.5">
                  <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                    Slot Type
                  </label>
                  <select
                    value={form.type}
                    onChange={(e) => setForm({ ...form, type: e.target.value as SlotType })}
                    className="w-full h-10 px-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="car">🚗 Car</option>
                    <option value="bike">🏍️ Bike</option>
                    <option value="ev">⚡ EV</option>
                    <option value="disabled">♿ Disabled</option>
                  </select>
                </div>
              </div>

              {/* Status */}
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                  Status
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {(["available", "occupied", "maintenance"] as SlotStatus[]).map((s) => {
                    const meta = STATUS_META[s];
                    const selected = form.status === s;
                    return (
                      <button
                        key={s}
                        type="button"
                        onClick={() => setForm({ ...form, status: s })}
                        className={`flex items-center justify-center gap-1.5 h-10 rounded-xl text-xs font-semibold border-2 transition-all ${
                          selected
                            ? "border-blue-500 bg-blue-50 dark:bg-blue-600/20 text-blue-700 dark:text-blue-300"
                            : "border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 hover:border-slate-300"
                        }`}
                      >
                        <span className={`w-2 h-2 rounded-full ${meta.dot}`} />
                        {meta.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Preview Card */}
              {form.number && (
                <div className="mt-2 p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                  <p className="text-xs text-slate-400 font-medium mb-2 uppercase tracking-wider">Preview</p>
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg bg-white dark:bg-slate-700 ${TYPE_META[form.type].color}`}>
                      {TYPE_META[form.type].icon}
                    </div>
                    <div>
                      <p className="font-bold text-slate-900 dark:text-white">{form.number.toUpperCase() || "—"}</p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">{form.lot} · Zone {form.zone.toUpperCase() || "—"}</p>
                    </div>
                    <span className={`ml-auto text-xs font-semibold px-2.5 py-1 rounded-full ${STATUS_META[form.status].bg}`}>
                      {STATUS_META[form.status].label}
                    </span>
                  </div>
                </div>
              )}
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
                {editingSlot ? "Save Changes" : "Add Slot"}
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
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setDeleteId(null)} />
          <div className="relative z-10 w-full max-w-sm bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-700 p-6 space-y-5">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-red-100 dark:bg-red-500/20 rounded-xl">
                <Trash2 className="h-5 w-5 text-red-600 dark:text-red-400" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900 dark:text-white text-lg">Delete Slot</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400">This cannot be undone.</p>
              </div>
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-300">
              Delete slot{" "}
              <span className="font-bold text-slate-900 dark:text-white">
                {slots.find((s) => s.id === deleteId)?.number}
              </span>?
            </p>
            <div className="flex gap-3">
              <Button variant="ghost" className="flex-1 rounded-xl border border-slate-200 dark:border-slate-700" onClick={() => setDeleteId(null)}>
                Cancel
              </Button>
              <Button className="flex-1 rounded-xl bg-red-600 hover:bg-red-700 text-white font-semibold" onClick={() => handleDelete(deleteId)}>
                Delete
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
