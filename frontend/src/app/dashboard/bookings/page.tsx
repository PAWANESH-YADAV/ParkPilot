"use client";

import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Calendar, Clock, MapPin, CheckCircle2, XCircle, Eye, Search, Filter, User, Car, CreditCard, ArrowUpDown, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useToast } from "@/lib/toast-context";

interface Booking {
  id: string;
  userId: string;
  userName: string;
  userEmail: string;
  lotId: string;
  lotName: string;
  lotAddress: string;
  slotId: string;
  slotNumber: string;
  date: string;
  startTime: string;
  endTime: string;
  durationHours: number;
  status: "pending" | "confirmed" | "active" | "completed" | "cancelled";
  amount: number;
  paymentMethod: "card" | "upi" | "wallet";
  vehicleType: "car" | "bike" | "suv";
  licensePlate: string;
  createdAt: string;
}

interface DBUser {
  id: string;
  name: string;
  email: string;
}

type StatusFilter = "all" | Booking["status"];
type SortKey = "newest" | "oldest" | "amount-high" | "amount-low";

const statusLabels: Record<Booking["status"], string> = {
  pending: "Pending",
  confirmed: "Confirmed",
  active: "Active",
  completed: "Completed",
  cancelled: "Cancelled",
};

const statusColors: Record<Booking["status"], string> = {
  pending: "bg-yellow-500/15 text-yellow-400 border-yellow-500/30",
  confirmed: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  active: "bg-green-500/15 text-green-400 border-green-500/30",
  completed: "bg-slate-500/15 text-slate-400 border-slate-500/30",
  cancelled: "bg-red-500/15 text-red-400 border-red-500/30",
};

const statusDots: Record<Booking["status"], string> = {
  pending: "bg-yellow-400",
  confirmed: "bg-blue-400",
  active: "bg-green-400",
  completed: "bg-slate-400",
  cancelled: "bg-red-400",
};

const vehicleIcons: Record<Booking["vehicleType"], string> = {
  car: "🚗",
  bike: "🏍️",
  suv: "🚙",
};

const paymentLabels: Record<Booking["paymentMethod"], string> = {
  card: "💳 Card",
  upi: "📱 UPI",
  wallet: "👛 Wallet",
};

const rupee = (n: number) => `₹${n.toFixed(2)}`;

const fmtDate = (iso: string) => {
  try {
    return new Date(iso).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
  } catch { return iso; }
};

const fmtTime = (iso: string) => {
  try {
    return new Date(iso).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: true });
  } catch { return iso; }
};

export default function AdminBookingsPage() {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [users, setUsers] = useState<DBUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [sort, setSort] = useState<SortKey>("newest");
  const [viewing, setViewing] = useState<Booking | null>(null);
  const [confirmAction, setConfirmAction] = useState<{ booking: Booking; type: "approve" | "reject" } | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const toast = useToast();

  useEffect(() => {
    try {
      const rawB = localStorage.getItem("parkpilot_bookings");
      const rawU = localStorage.getItem("parkpilot_users");
      const allB: Booking[] = rawB ? JSON.parse(rawB) : [];
      const allU: DBUser[] = rawU ? JSON.parse(rawU) : [];
      const userMap = new Map(allU.map(u => [u.id, u]));
      const enriched: Booking[] = allB.map(b => {
        const u = userMap.get(b.userId);
        return {
          ...b,
          userName: b.userName || u?.name || "Unknown",
          userEmail: b.userEmail || u?.email || "—",
        };
      }).sort((a, z) => new Date(z.createdAt || z.id).getTime() - new Date(a.createdAt || a.id).getTime());
      setBookings(enriched);
      setUsers(allU);
    } catch (e) {
      console.error(e);
    } finally {
      setTimeout(() => setLoading(false), 350);
    }
  }, []);

  const persistAll = (next: Booking[]) => {
    setBookings(next);
    localStorage.setItem("parkpilot_bookings", JSON.stringify(next));
  };

  const counts = useMemo(() => {
    const c = { all: bookings.length, pending: 0, confirmed: 0, active: 0, completed: 0, cancelled: 0 };
    bookings.forEach(b => { if (b.status in c) c[b.status]++; });
    return c;
  }, [bookings]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    let arr = bookings;
    if (statusFilter !== "all") arr = arr.filter(b => b.status === statusFilter);
    if (q) {
      arr = arr.filter(b =>
        b.id.toLowerCase().includes(q) ||
        b.userName.toLowerCase().includes(q) ||
        b.userEmail.toLowerCase().includes(q) ||
        b.lotName.toLowerCase().includes(q) ||
        b.licensePlate.toLowerCase().includes(q)
      );
    }
    const sorted = [...arr];
    switch (sort) {
      case "newest": sorted.sort((a, z) => new Date(z.createdAt || z.id).getTime() - new Date(a.createdAt || a.id).getTime()); break;
      case "oldest": sorted.sort((a, z) => new Date(a.createdAt || a.id).getTime() - new Date(z.createdAt || z.id).getTime()); break;
      case "amount-high": sorted.sort((a, z) => z.amount - a.amount); break;
      case "amount-low": sorted.sort((a, z) => a.amount - z.amount); break;
    }
    return sorted;
  }, [bookings, search, statusFilter, sort]);

  const totalRevenue = useMemo(
    () => bookings.filter(b => b.status === "completed" || b.status === "active" || b.status === "confirmed").reduce((s, b) => s + b.amount, 0),
    [bookings]
  );

  const doApprove = (b: Booking) => {
    if (b.status !== "pending") {
      toast.error("Invalid action", "Only pending bookings can be approved.");
      return;
    }
    setActionLoading(true);
    setTimeout(() => {
      const next = bookings.map(x => x.id === b.id ? { ...x, status: "confirmed" as const } : x);
      persistAll(next);
      toast.success("Booking approved", `${b.id} is now confirmed for ${b.userName}.`);
      setConfirmAction(null);
      setActionLoading(false);
    }, 500);
  };

  const doReject = (b: Booking) => {
    if (b.status !== "pending") {
      toast.error("Invalid action", "Only pending bookings can be rejected.");
      return;
    }
    setActionLoading(true);
    setTimeout(() => {
      const next = bookings.map(x => x.id === b.id ? { ...x, status: "cancelled" as const } : x);
      persistAll(next);
      toast.warning("Booking rejected", `${b.id} cancelled. Full refund of ${rupee(b.amount)} initiated.`);
      setConfirmAction(null);
      setActionLoading(false);
    }, 500);
  };

  return (
    <div className="space-y-6 min-h-screen">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Booking Management</h1>
          <p className="text-slate-400 mt-1">Approve, reject, and monitor all reservations across the platform.</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          Live synced with parkpilot_bookings · {bookings.length} total
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
        <StatCard label="Total" value={counts.all} accent="text-white" dot="bg-slate-400" onClick={() => setStatusFilter("all")} active={statusFilter === "all"} />
        <StatCard label="Pending" value={counts.pending} accent="text-yellow-400" dot="bg-yellow-400" onClick={() => setStatusFilter("pending")} active={statusFilter === "pending"} />
        <StatCard label="Confirmed" value={counts.confirmed} accent="text-blue-400" dot="bg-blue-400" onClick={() => setStatusFilter("confirmed")} active={statusFilter === "confirmed"} />
        <StatCard label="Active" value={counts.active} accent="text-green-400" dot="bg-green-400" onClick={() => setStatusFilter("active")} active={statusFilter === "active"} />
        <StatCard label="Completed" value={counts.completed} accent="text-slate-400" dot="bg-slate-400" onClick={() => setStatusFilter("completed")} active={statusFilter === "completed"} />
        <StatCard label="Cancelled" value={counts.cancelled} accent="text-red-400" dot="bg-red-400" onClick={() => setStatusFilter("cancelled")} active={statusFilter === "cancelled"} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <Card className="bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700">
          <CardContent className="p-5">
            <p className="text-slate-400 text-xs uppercase tracking-wider">Total Revenue</p>
            <p className="text-3xl font-bold text-emerald-400 mt-1">{rupee(totalRevenue)}</p>
            <p className="text-slate-500 text-xs mt-2">Confirmed + Active + Completed</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/60 border-slate-700">
          <CardContent className="p-5">
            <p className="text-slate-400 text-xs uppercase tracking-wider">Registered Users</p>
            <p className="text-3xl font-bold text-white mt-1">{users.length}</p>
            <p className="text-slate-500 text-xs mt-2">From parkpilot_users store</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/60 border-slate-700">
          <CardContent className="p-5">
            <p className="text-slate-400 text-xs uppercase tracking-wider">Approval Rate</p>
            <p className="text-3xl font-bold text-white mt-1">
              {counts.all ? Math.round(((counts.confirmed + counts.active + counts.completed) / counts.all) * 100) : 0}%
            </p>
            <p className="text-slate-500 text-xs mt-2">Reservations not rejected/cancelled</p>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-slate-800 border-slate-700">
        <CardHeader className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-5 border-b border-slate-700/60">
          <CardTitle className="text-white text-lg">All Bookings <span className="text-slate-500 font-normal text-sm ml-2">({filtered.length})</span></CardTitle>
          <div className="flex flex-col sm:flex-row gap-2 w-full md:w-auto">
            <div className="relative">
              <Search className="h-4 w-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <Input
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search ID, user, email, lot, plate…"
                className="pl-9 bg-slate-900 border-slate-700 text-white placeholder:text-slate-500 w-full sm:w-72"
              />
            </div>
            <div className="relative">
              <Filter className="h-4 w-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <select
                value={sort}
                onChange={e => setSort(e.target.value as SortKey)}
                className="appearance-none w-full sm:w-48 h-10 pl-9 pr-8 rounded-md bg-slate-900 border border-slate-700 text-white text-sm focus:ring-2 focus:ring-emerald-500/40 outline-none"
              >
                <option value="newest">Newest first</option>
                <option value="oldest">Oldest first</option>
                <option value="amount-high">Amount: High → Low</option>
                <option value="amount-low">Amount: Low → High</option>
              </select>
              <ArrowUpDown className="h-3.5 w-3.5 text-slate-500 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="py-20 flex flex-col items-center gap-3 text-slate-400">
              <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
              Loading bookings…
            </div>
          ) : filtered.length === 0 ? (
            <div className="py-20 flex flex-col items-center gap-2 text-center">
              <div className="h-14 w-14 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center">
                <Calendar className="h-6 w-6 text-slate-500" />
              </div>
              <p className="text-white font-medium">No bookings found</p>
              <p className="text-slate-400 text-sm max-w-sm">Try clearing the search bar or switching the status filter above.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-slate-900/40">
                  <tr className="text-slate-400">
                    <th className="px-5 py-3 font-medium whitespace-nowrap">Booking</th>
                    <th className="px-5 py-3 font-medium whitespace-nowrap">User</th>
                    <th className="px-5 py-3 font-medium whitespace-nowrap">Lot & Slot</th>
                    <th className="px-5 py-3 font-medium whitespace-nowrap">Schedule</th>
                    <th className="px-5 py-3 font-medium whitespace-nowrap">Vehicle</th>
                    <th className="px-5 py-3 font-medium whitespace-nowrap">Status</th>
                    <th className="px-5 py-3 font-medium whitespace-nowrap text-right">Amount</th>
                    <th className="px-5 py-3 font-medium whitespace-nowrap text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((b, i) => (
                    <motion.tr
                      key={b.id}
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.2, delay: i * 0.015 }}
                      className="border-t border-slate-700/50 hover:bg-slate-900/30 transition-colors"
                    >
                      <td className="px-5 py-4 align-top">
                        <p className="text-white font-semibold font-mono">{b.id}</p>
                        <p className="text-slate-500 text-xs mt-1">Created {fmtDate(b.createdAt)}</p>
                      </td>
                      <td className="px-5 py-4 align-top">
                        <div className="flex items-center gap-2">
                          <div className="h-8 w-8 rounded-full bg-gradient-to-br from-emerald-500/30 to-teal-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-300">
                            <User className="h-4 w-4" />
                          </div>
                          <div className="min-w-0">
                            <p className="text-white truncate max-w-[160px]">{b.userName}</p>
                            <p className="text-slate-500 text-xs truncate max-w-[160px]">{b.userEmail}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-4 align-top">
                        <p className="text-white flex items-center gap-1.5">
                          <MapPin className="h-3.5 w-3.5 text-emerald-400" />
                          {b.lotName}
                        </p>
                        <p className="text-slate-500 text-xs mt-1">Slot <span className="text-slate-300 font-mono">{b.slotNumber || b.slotId}</span></p>
                      </td>
                      <td className="px-5 py-4 align-top">
                        <p className="text-slate-200 flex items-center gap-1.5">
                          <Calendar className="h-3.5 w-3.5 text-slate-500" />
                          {fmtDate(b.date)}
                        </p>
                        <p className="text-slate-500 text-xs mt-1 flex items-center gap-1.5">
                          <Clock className="h-3.5 w-3.5" />
                          {fmtTime(b.startTime)} – {fmtTime(b.endTime)}
                        </p>
                        <p className="text-slate-500 text-xs mt-0.5">{b.durationHours?.toFixed(1) || "—"} hrs</p>
                      </td>
                      <td className="px-5 py-4 align-top">
                        <div className="flex items-center gap-2">
                          <span className="text-lg">{vehicleIcons[b.vehicleType] || "🚗"}</span>
                          <div>
                            <p className="text-white font-mono text-sm">{b.licensePlate}</p>
                            <p className="text-slate-500 text-xs capitalize">{b.vehicleType}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-4 align-top">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${statusColors[b.status]}`}>
                          <span className={`h-1.5 w-1.5 rounded-full ${statusDots[b.status]} ${b.status === "active" ? "animate-pulse" : ""}`} />
                          {statusLabels[b.status]}
                        </span>
                      </td>
                      <td className="px-5 py-4 align-top text-right">
                        <p className="text-white font-bold whitespace-nowrap">{rupee(b.amount)}</p>
                        <p className="text-slate-500 text-xs whitespace-nowrap">{paymentLabels[b.paymentMethod]}</p>
                      </td>
                      <td className="px-5 py-4 align-top">
                        <div className="flex justify-end gap-1.5">
                          <Button variant="ghost" size="sm" onClick={() => setViewing(b)} className="text-slate-300 hover:text-white hover:bg-slate-700/60">
                            <Eye className="h-4 w-4" />
                            <span className="sr-only">View</span>
                          </Button>
                          {b.status === "pending" && (
                            <>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setConfirmAction({ booking: b, type: "approve" })}
                                className="text-green-400 hover:text-green-300 hover:bg-green-500/10"
                              >
                                <CheckCircle2 className="h-4 w-4" />
                                <span className="hidden sm:inline ml-1">Approve</span>
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setConfirmAction({ booking: b, type: "reject" })}
                                className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                              >
                                <XCircle className="h-4 w-4" />
                                <span className="hidden sm:inline ml-1">Reject</span>
                              </Button>
                            </>
                          )}
                        </div>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <AnimatePresence>
        {viewing && (
          <ModalShell onClose={() => setViewing(null)}>
            <div className="p-6 space-y-5 max-w-lg">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-slate-400 text-xs uppercase tracking-wider">Booking Details</p>
                  <h3 className="text-2xl font-bold text-white font-mono mt-0.5">{viewing.id}</h3>
                </div>
                <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${statusColors[viewing.status]}`}>
                  <span className={`h-1.5 w-1.5 rounded-full ${statusDots[viewing.status]}`} />
                  {statusLabels[viewing.status]}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <InfoTile icon={<User className="h-4 w-4" />} label="Driver" primary={viewing.userName} secondary={viewing.userEmail} />
                <InfoTile icon={<Car className="h-4 w-4" />} label="Vehicle" primary={`${vehicleIcons[viewing.vehicleType]} ${viewing.vehicleType.toUpperCase()}`} secondary={viewing.licensePlate} />
                <InfoTile icon={<MapPin className="h-4 w-4" />} label="Parking Lot" primary={viewing.lotName} secondary={viewing.lotAddress || `Slot ${viewing.slotNumber || viewing.slotId}`} />
                <InfoTile icon={<CreditCard className="h-4 w-4" />} label="Payment" primary={rupee(viewing.amount)} secondary={`${paymentLabels[viewing.paymentMethod]} · ${viewing.durationHours?.toFixed(1) || "—"} hrs`} />
              </div>

              <Card className="bg-slate-900 border-slate-700/60">
                <CardContent className="p-4 space-y-2 text-sm">
                  <Row k="Date" v={fmtDate(viewing.date)} />
                  <Row k="Start" v={fmtTime(viewing.startTime)} />
                  <Row k="End" v={fmtTime(viewing.endTime)} />
                  <Row k="Duration" v={`${viewing.durationHours?.toFixed(1) || "—"} hours`} />
                  <Row k="Created At" v={`${fmtDate(viewing.createdAt)} ${fmtTime(viewing.createdAt)}`} />
                </CardContent>
              </Card>

              <div className="flex flex-col-reverse sm:flex-row justify-end gap-2 pt-2">
                <Button variant="ghost" onClick={() => setViewing(null)} className="text-slate-300 hover:bg-slate-700/60">Close</Button>
                {viewing.status === "pending" && (
                  <>
                    <Button onClick={() => { setViewing(null); setConfirmAction({ booking: viewing, type: "reject" }); }} variant="destructive" className="bg-red-600/80 hover:bg-red-600">
                      <XCircle className="h-4 w-4 mr-1.5" /> Reject
                    </Button>
                    <Button onClick={() => { setViewing(null); setConfirmAction({ booking: viewing, type: "approve" }); }} className="bg-emerald-600 hover:bg-emerald-500 text-white">
                      <CheckCircle2 className="h-4 w-4 mr-1.5" /> Approve
                    </Button>
                  </>
                )}
              </div>
            </div>
          </ModalShell>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {confirmAction && (
          <ModalShell onClose={() => !actionLoading && setConfirmAction(null)}>
            <div className="p-6 max-w-md space-y-5">
              <div className="flex items-start gap-4">
                <div className={`h-11 w-11 shrink-0 rounded-full flex items-center justify-center ${confirmAction.type === "approve" ? "bg-green-500/15 text-green-400 border border-green-500/30" : "bg-red-500/15 text-red-400 border border-red-500/30"}`}>
                  {confirmAction.type === "approve" ? <CheckCircle2 className="h-6 w-6" /> : <XCircle className="h-6 w-6" />}
                </div>
                <div className="min-w-0">
                  <h3 className="text-xl font-bold text-white">
                    {confirmAction.type === "approve" ? "Approve booking?" : "Reject booking?"}
                  </h3>
                  <p className="text-slate-400 text-sm mt-1">
                    {confirmAction.type === "approve"
                      ? `Confirming ${confirmAction.booking.id} will reserve slot ${confirmAction.booking.slotNumber || confirmAction.booking.slotId} for ${confirmAction.booking.userName}.`
                      : `Rejecting ${confirmAction.booking.id} will cancel the reservation and issue a full refund of ${rupee(confirmAction.booking.amount)}.`}
                  </p>
                </div>
              </div>

              <Card className="bg-slate-900 border-slate-700/60">
                <CardContent className="p-4 text-sm space-y-1.5">
                  <Row k="Lot" v={confirmAction.booking.lotName} />
                  <Row k="Driver" v={confirmAction.booking.userName} />
                  <Row k="Date / Time" v={`${fmtDate(confirmAction.booking.date)} · ${fmtTime(confirmAction.booking.startTime)}`} />
                  <Row k="Amount" v={rupee(confirmAction.booking.amount)} />
                </CardContent>
              </Card>

              <div className="flex flex-col-reverse sm:flex-row justify-end gap-2">
                <Button variant="ghost" disabled={actionLoading} onClick={() => setConfirmAction(null)} className="text-slate-300 hover:bg-slate-700/60">Cancel</Button>
                <Button
                  disabled={actionLoading}
                  onClick={() => confirmAction.type === "approve" ? doApprove(confirmAction.booking) : doReject(confirmAction.booking)}
                  className={confirmAction.type === "approve" ? "bg-emerald-600 hover:bg-emerald-500 text-white" : "bg-red-600/90 hover:bg-red-600 text-white"}
                >
                  {actionLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                  {confirmAction.type === "approve" ? "Confirm Approve" : "Confirm Reject"}
                </Button>
              </div>
            </div>
          </ModalShell>
        )}
      </AnimatePresence>
    </div>
  );
}

function StatCard({ label, value, accent, dot, onClick, active }: {
  label: string; value: number; accent: string; dot: string; onClick?: () => void; active?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className={`text-left p-4 rounded-lg border transition-all ${active ? "bg-slate-800 border-emerald-500/40 shadow-[0_0_0_1px_rgba(16,185,129,0.15)]" : "bg-slate-800/50 border-slate-700 hover:border-slate-600 hover:bg-slate-800"}`}
    >
      <div className="flex items-center gap-2">
        <span className={`h-2 w-2 rounded-full ${dot}`} />
        <span className="text-xs text-slate-400 uppercase tracking-wider">{label}</span>
      </div>
      <p className={`text-2xl font-bold mt-2 ${accent}`}>{value}</p>
    </button>
  );
}

function InfoTile({ icon, label, primary, secondary }: { icon: React.ReactNode; label: string; primary: string; secondary?: string; }) {
  return (
    <div className="rounded-lg bg-slate-900 border border-slate-700/60 p-3">
      <div className="flex items-center gap-1.5 text-slate-500 text-xs uppercase tracking-wider mb-1.5">
        <span className="text-emerald-400">{icon}</span>
        {label}
      </div>
      <p className="text-white font-medium truncate">{primary}</p>
      {secondary && <p className="text-slate-400 text-xs truncate mt-0.5">{secondary}</p>}
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between items-center gap-4 py-0.5">
      <span className="text-slate-500">{k}</span>
      <span className="text-slate-200 text-right truncate">{v}</span>
    </div>
  );
}

function ModalShell({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  return (
    <motion.div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
    >
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <motion.div
        role="dialog"
        onClick={e => e.stopPropagation()}
        initial={{ opacity: 0, y: 10, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 6, scale: 0.98 }}
        transition={{ type: "spring", stiffness: 260, damping: 24 }}
        className="relative w-full max-w-lg rounded-xl bg-slate-800 border border-slate-700 shadow-2xl shadow-black/50"
      >
        {children}
      </motion.div>
    </motion.div>
  );
}
