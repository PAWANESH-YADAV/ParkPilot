"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Users,
  UserPlus,
  Edit2,
  Trash2,
  Eye,
  ShieldCheck,
  Ban,
  CheckCircle2,
  Search,
  RefreshCw,
  Phone,
  Mail,
  Calendar,
  X,
  User as UserIcon,
  Shield,
  AlertTriangle,
} from "lucide-react";
import { authApi, BackendUser } from "@/lib/api";
import {
  SystemUser,
  getStoredUsers,
  addStoredUser,
  updateStoredUser,
  deleteStoredUser,
  saveStoredUsers,
} from "@/lib/user-registry";

export default function UserManagementPage() {
  const [users, setUsers] = useState<SystemUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState<"all" | "user" | "admin">("all");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "inactive">("all");

  // Modals state
  const [showAddModal, setShowAddModal] = useState(false);
  const [viewingUser, setViewingUser] = useState<SystemUser | null>(null);
  const [editingUser, setEditingUser] = useState<SystemUser | null>(null);
  const [deletingUser, setDeletingUser] = useState<SystemUser | null>(null);

  // Toast alert
  const [toastMessage, setToastMessage] = useState<{
    text: string;
    type: "success" | "error" | "info";
  } | null>(null);

  const showToast = (text: string, type: "success" | "error" | "info" = "success") => {
    setToastMessage({ text, type });
    setTimeout(() => setToastMessage(null), 3500);
  };

  // New user form state
  const [newUserData, setNewUserData] = useState({
    name: "",
    email: "",
    phone: "",
    password: "",
    role: "user" as "user" | "admin",
    status: "active" as "active" | "inactive",
  });
  const [addError, setAddError] = useState("");

  // Edit form state
  const [editFormData, setEditFormData] = useState({
    name: "",
    email: "",
    phone: "",
    role: "user" as "user" | "admin",
    status: "active" as "active" | "inactive",
  });

  // Load and merge users from backend & local store
  const loadUsers = useCallback(async () => {
    setIsLoading(true);
    const localUsers = getStoredUsers();

    try {
      const backendUsers = await authApi.getUsers();
      if (Array.isArray(backendUsers) && backendUsers.length > 0) {
        const merged: SystemUser[] = [...localUsers];

        backendUsers.forEach((bu: BackendUser) => {
          const matchIdx = merged.findIndex(
            (u) =>
              u.backendId === bu.id ||
              u.email.toLowerCase() === bu.email.toLowerCase()
          );
          const role: "user" | "admin" =
            bu.role === "admin" ? "admin" : "user";
          const status: "active" | "inactive" = bu.is_active
            ? "active"
            : "inactive";
          const joinDate = bu.created_at
            ? bu.created_at.split("T")[0]
            : new Date().toISOString().split("T")[0];

          if (matchIdx >= 0) {
            merged[matchIdx] = {
              ...merged[matchIdx],
              name: bu.full_name || merged[matchIdx].name,
              backendId: bu.id,
              role,
              status,
            };
          } else {
            merged.unshift({
              id: `usr-be-${bu.id}`,
              name: bu.full_name || bu.email.split("@")[0],
              email: bu.email,
              phone: "+91 9800000000",
              role,
              status,
              joinDate,
              backendId: bu.id,
            });
          }
        });

        saveStoredUsers(merged);
        setUsers(merged);
        setIsLoading(false);
        return;
      }
    } catch {
      // Backend offline, fallback to local users
    }

    setUsers(localUsers);
    setIsLoading(false);
  }, []);

  useEffect(() => {
    loadUsers();

    const handleUsersUpdated = () => {
      setUsers(getStoredUsers());
    };

    window.addEventListener("parkpilot_users_updated", handleUsersUpdated);
    window.addEventListener("storage", handleUsersUpdated);

    return () => {
      window.removeEventListener("parkpilot_users_updated", handleUsersUpdated);
      window.removeEventListener("storage", handleUsersUpdated);
    };
  }, [loadUsers]);

  // Filters
  const filteredUsers = users.filter((user) => {
    const matchesSearch =
      user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.phone.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.role.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesRole = roleFilter === "all" || user.role === roleFilter;
    const matchesStatus =
      statusFilter === "all" || user.status === statusFilter;

    return matchesSearch && matchesRole && matchesStatus;
  });

  // Top Metrics
  const totalUsersCount = users.length;
  const activeUsersCount = users.filter((u) => u.status === "active").length;
  const adminUsersCount = users.filter((u) => u.role === "admin").length;
  const inactiveUsersCount = users.filter((u) => u.status === "inactive").length;

  // Handle Create User
  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setAddError("");

    if (!newUserData.name.trim() || !newUserData.email.trim()) {
      setAddError("Please fill in Name and Email.");
      return;
    }

    if (
      users.some(
        (u) => u.email.toLowerCase() === newUserData.email.trim().toLowerCase()
      )
    ) {
      setAddError("A user with this email already exists.");
      return;
    }

    let backendId: number | undefined = undefined;
    try {
      const created = await authApi.createUser({
        email: newUserData.email.trim(),
        full_name: newUserData.name.trim(),
        password: newUserData.password || "Password@123",
        role: newUserData.role,
        is_active: newUserData.status === "active",
      });
      backendId = created.id;
    } catch {
      // Handled via local storage
    }

    const added = addStoredUser({
      name: newUserData.name.trim(),
      email: newUserData.email.trim(),
      phone: newUserData.phone.trim() || "+91 9876543210",
      role: newUserData.role,
      status: newUserData.status,
      backendId,
    });

    setUsers(getStoredUsers());
    setShowAddModal(false);
    setNewUserData({
      name: "",
      email: "",
      phone: "",
      password: "",
      role: "user",
      status: "active",
    });
    showToast(`User "${added.name}" added successfully!`);
  };

  // Open Edit Modal
  const startEdit = (user: SystemUser) => {
    setEditingUser(user);
    setEditFormData({
      name: user.name,
      email: user.email,
      phone: user.phone,
      role: user.role,
      status: user.status,
    });
  };

  // Handle Update User
  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) return;

    if (editingUser.backendId) {
      try {
        await authApi.updateUser(editingUser.backendId, {
          full_name: editFormData.name,
          email: editFormData.email,
          role: editFormData.role,
          is_active: editFormData.status === "active",
        });
      } catch {
        // Continue with local save
      }
    }

    updateStoredUser(editingUser.id, {
      name: editFormData.name,
      email: editFormData.email,
      phone: editFormData.phone,
      role: editFormData.role,
      status: editFormData.status,
    });

    setUsers(getStoredUsers());
    setEditingUser(null);
    showToast(`User "${editFormData.name}" updated successfully!`);
  };

  // Toggle Role (User <-> Admin)
  const handleToggleRole = async (user: SystemUser) => {
    const newRole = user.role === "admin" ? "user" : "admin";
    if (user.backendId) {
      try {
        await authApi.updateUser(user.backendId, { role: newRole });
      } catch {
        // local update
      }
    }
    updateStoredUser(user.id, { role: newRole });
    setUsers(getStoredUsers());
    showToast(
      `Role for ${user.name} changed to ${newRole.toUpperCase()}!`,
      "info"
    );
  };

  // Toggle Status (Active <-> Inactive / Ban)
  const handleToggleStatus = async (user: SystemUser) => {
    const newStatus = user.status === "active" ? "inactive" : "active";
    if (user.backendId) {
      try {
        await authApi.updateUser(user.backendId, {
          is_active: newStatus === "active",
        });
      } catch {
        // local update
      }
    }
    updateStoredUser(user.id, { status: newStatus });
    setUsers(getStoredUsers());
    showToast(
      `User ${user.name} is now ${newStatus === "active" ? "ACTIVE" : "SUSPENDED"}!`,
      newStatus === "active" ? "success" : "error"
    );
  };

  // Handle Delete
  const handleConfirmDelete = async () => {
    if (!deletingUser) return;
    if (deletingUser.backendId) {
      try {
        await authApi.deleteUser(deletingUser.backendId);
      } catch {
        // local delete
      }
    }
    deleteStoredUser(deletingUser.id);
    setUsers(getStoredUsers());
    showToast(`User ${deletingUser.name} has been removed.`, "error");
    setDeletingUser(null);
  };

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {toastMessage && (
        <div
          className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 text-sm font-medium transition-all ${
            toastMessage.type === "success"
              ? "bg-emerald-600 text-white shadow-emerald-900/30"
              : toastMessage.type === "error"
              ? "bg-rose-600 text-white shadow-rose-900/30"
              : "bg-blue-600 text-white shadow-blue-900/30"
          }`}
        >
          {toastMessage.type === "success" ? (
            <CheckCircle2 className="h-4 w-4" />
          ) : toastMessage.type === "error" ? (
            <AlertTriangle className="h-4 w-4" />
          ) : (
            <ShieldCheck className="h-4 w-4" />
          )}
          <span>{toastMessage.text}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Users className="h-8 w-8 text-blue-500" />
            User Management
          </h1>
          <p className="text-slate-400 mt-1">
            Monitor, manage, and verify all registered users & drivers in real-time
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={loadUsers}
            disabled={isLoading}
            className="border-slate-700 bg-slate-800 text-slate-300 hover:bg-slate-700"
          >
            <RefreshCw
              className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
          <Button
            onClick={() => setShowAddModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            <UserPlus className="h-4 w-4 mr-2" />
            Add New User
          </Button>
        </div>
      </div>

      {/* Metric Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-slate-800/80 border-slate-700">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                Total Users
              </p>
              <h3 className="text-2xl font-bold text-white mt-1">
                {totalUsersCount}
              </h3>
            </div>
            <div className="h-11 w-11 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
              <Users className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/80 border-slate-700">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                Active Users
              </p>
              <h3 className="text-2xl font-bold text-emerald-400 mt-1">
                {activeUsersCount}
              </h3>
            </div>
            <div className="h-11 w-11 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <CheckCircle2 className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/80 border-slate-700">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                Administrators
              </p>
              <h3 className="text-2xl font-bold text-purple-400 mt-1">
                {adminUsersCount}
              </h3>
            </div>
            <div className="h-11 w-11 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
              <Shield className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/80 border-slate-700">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                Suspended / Inactive
              </p>
              <h3 className="text-2xl font-bold text-rose-400 mt-1">
                {inactiveUsersCount}
              </h3>
            </div>
            <div className="h-11 w-11 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
              <Ban className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filter and Search Bar */}
      <Card className="bg-slate-800 border-slate-700">
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Search by name, email, phone..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 bg-slate-700/70 border-slate-600 text-white placeholder:text-slate-400 focus:border-blue-500"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <div className="flex items-center gap-1.5 bg-slate-700/50 p-1 rounded-lg border border-slate-600/50">
                <span className="text-xs text-slate-400 px-2 font-medium">Role:</span>
                <button
                  type="button"
                  onClick={() => setRoleFilter("all")}
                  className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors ${
                    roleFilter === "all"
                      ? "bg-blue-600 text-white"
                      : "text-slate-300 hover:bg-slate-600"
                  }`}
                >
                  All
                </button>
                <button
                  type="button"
                  onClick={() => setRoleFilter("user")}
                  className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors ${
                    roleFilter === "user"
                      ? "bg-blue-600 text-white"
                      : "text-slate-300 hover:bg-slate-600"
                  }`}
                >
                  Drivers
                </button>
                <button
                  type="button"
                  onClick={() => setRoleFilter("admin")}
                  className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors ${
                    roleFilter === "admin"
                      ? "bg-purple-600 text-white"
                      : "text-slate-300 hover:bg-slate-600"
                  }`}
                >
                  Admins
                </button>
              </div>

              <div className="flex items-center gap-1.5 bg-slate-700/50 p-1 rounded-lg border border-slate-600/50">
                <span className="text-xs text-slate-400 px-2 font-medium">Status:</span>
                <button
                  type="button"
                  onClick={() => setStatusFilter("all")}
                  className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors ${
                    statusFilter === "all"
                      ? "bg-blue-600 text-white"
                      : "text-slate-300 hover:bg-slate-600"
                  }`}
                >
                  All
                </button>
                <button
                  type="button"
                  onClick={() => setStatusFilter("active")}
                  className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors ${
                    statusFilter === "active"
                      ? "bg-emerald-600 text-white"
                      : "text-slate-300 hover:bg-slate-600"
                  }`}
                >
                  Active
                </button>
                <button
                  type="button"
                  onClick={() => setStatusFilter("inactive")}
                  className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors ${
                    statusFilter === "inactive"
                      ? "bg-rose-600 text-white"
                      : "text-slate-300 hover:bg-slate-600"
                  }`}
                >
                  Inactive
                </button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card className="bg-slate-800 border-slate-700 overflow-hidden">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-slate-700 bg-slate-800/90">
                  <th className="py-3.5 px-6 text-slate-400 font-semibold text-xs uppercase tracking-wider">
                    User Details
                  </th>
                  <th className="py-3.5 px-6 text-slate-400 font-semibold text-xs uppercase tracking-wider">
                    Contact Phone
                  </th>
                  <th className="py-3.5 px-6 text-slate-400 font-semibold text-xs uppercase tracking-wider">
                    Role
                  </th>
                  <th className="py-3.5 px-6 text-slate-400 font-semibold text-xs uppercase tracking-wider">
                    Status
                  </th>
                  <th className="py-3.5 px-6 text-slate-400 font-semibold text-xs uppercase tracking-wider">
                    Registered On
                  </th>
                  <th className="py-3.5 px-6 text-slate-400 font-semibold text-xs uppercase tracking-wider text-right">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/60">
                {filteredUsers.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-slate-400">
                      <Users className="h-10 w-10 mx-auto mb-2 text-slate-500 opacity-60" />
                      <p className="text-base font-medium">No users found</p>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Try adjusting your search query or role/status filters.
                      </p>
                    </td>
                  </tr>
                ) : (
                  filteredUsers.map((user) => (
                    <tr
                      key={user.id}
                      className="hover:bg-slate-700/40 transition-colors"
                    >
                      <td className="py-4 px-6">
                        <div className="flex items-center gap-3">
                          <div
                            className={`h-10 w-10 rounded-full flex items-center justify-center text-white font-bold text-sm shadow-sm ${
                              user.role === "admin"
                                ? "bg-gradient-to-br from-purple-500 to-indigo-600"
                                : "bg-gradient-to-br from-blue-500 to-cyan-600"
                            }`}
                          >
                            {user.name ? user.name.charAt(0).toUpperCase() : "U"}
                          </div>
                          <div>
                            <p className="text-white font-medium text-sm flex items-center gap-1.5">
                              {user.name}
                              {user.role === "admin" && (
                                <Shield className="h-3.5 w-3.5 text-purple-400" />
                              )}
                            </p>
                            <p className="text-slate-400 text-xs flex items-center gap-1 mt-0.5">
                              <Mail className="h-3 w-3 text-slate-500" />
                              {user.email}
                            </p>
                          </div>
                        </div>
                      </td>

                      <td className="py-4 px-6 text-slate-300 text-sm">
                        <span className="flex items-center gap-1 text-slate-300">
                          <Phone className="h-3.5 w-3.5 text-slate-500" />
                          {user.phone || "—"}
                        </span>
                      </td>

                      <td className="py-4 px-6">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ${
                            user.role === "admin"
                              ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                              : "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                          }`}
                        >
                          {user.role}
                        </span>
                      </td>

                      <td className="py-4 px-6">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            user.status === "active"
                              ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                              : "bg-rose-500/15 text-rose-400 border border-rose-500/30"
                          }`}
                        >
                          <span
                            className={`h-1.5 w-1.5 rounded-full ${
                              user.status === "active"
                                ? "bg-emerald-400 animate-pulse"
                                : "bg-rose-400"
                            }`}
                          />
                          {user.status === "active" ? "Active" : "Inactive"}
                        </span>
                      </td>

                      <td className="py-4 px-6 text-slate-400 text-xs">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3.5 w-3.5 text-slate-500" />
                          {user.joinDate || "Recent"}
                        </span>
                      </td>

                      <td className="py-4 px-6 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {/* View Details */}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setViewingUser(user)}
                            className="h-8 w-8 p-0 text-slate-300 hover:text-blue-400 hover:bg-slate-700"
                            title="View User Details"
                          >
                            <Eye className="h-4 w-4" />
                          </Button>

                          {/* Edit User */}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => startEdit(user)}
                            className="h-8 w-8 p-0 text-slate-300 hover:text-amber-400 hover:bg-slate-700"
                            title="Edit User"
                          >
                            <Edit2 className="h-4 w-4" />
                          </Button>

                          {/* Toggle Admin / User Role */}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleToggleRole(user)}
                            className={`h-8 w-8 p-0 hover:bg-slate-700 ${
                              user.role === "admin"
                                ? "text-purple-400 hover:text-purple-300"
                                : "text-slate-400 hover:text-purple-400"
                            }`}
                            title={
                              user.role === "admin"
                                ? "Demote to Driver/User"
                                : "Promote to Admin"
                            }
                          >
                            <ShieldCheck className="h-4 w-4" />
                          </Button>

                          {/* Toggle Active / Inactive Status */}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleToggleStatus(user)}
                            className={`h-8 w-8 p-0 hover:bg-slate-700 ${
                              user.status === "active"
                                ? "text-slate-400 hover:text-rose-400"
                                : "text-emerald-400 hover:text-emerald-300"
                            }`}
                            title={
                              user.status === "active"
                                ? "Deactivate / Ban User"
                                : "Reactivate User"
                            }
                          >
                            {user.status === "active" ? (
                              <Ban className="h-4 w-4" />
                            ) : (
                              <CheckCircle2 className="h-4 w-4" />
                            )}
                          </Button>

                          {/* Delete User */}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setDeletingUser(user)}
                            className="h-8 w-8 p-0 text-slate-400 hover:text-rose-400 hover:bg-slate-700"
                            title="Delete User"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* MODAL 1: ADD NEW USER */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <Card className="bg-slate-800 border-slate-700 w-full max-w-lg shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <CardHeader className="flex flex-row items-center justify-between border-b border-slate-700 pb-4">
              <div className="flex items-center gap-2">
                <UserPlus className="h-5 w-5 text-blue-500" />
                <CardTitle className="text-white text-xl">Add New User</CardTitle>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </Button>
            </CardHeader>
            <form onSubmit={handleAddUser}>
              <CardContent className="space-y-4 pt-4">
                {addError && (
                  <div className="p-3 bg-rose-500/20 border border-rose-500/40 rounded-lg text-rose-300 text-xs flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 flex-shrink-0" />
                    <span>{addError}</span>
                  </div>
                )}

                <div>
                  <label className="text-xs text-slate-300 font-medium block mb-1.5">
                    Full Name *
                  </label>
                  <Input
                    placeholder="e.g. Rahul Sharma"
                    value={newUserData.name}
                    onChange={(e) =>
                      setNewUserData({ ...newUserData, name: e.target.value })
                    }
                    className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-400"
                    required
                  />
                </div>

                <div>
                  <label className="text-xs text-slate-300 font-medium block mb-1.5">
                    Email Address *
                  </label>
                  <Input
                    type="email"
                    placeholder="user@example.com"
                    value={newUserData.email}
                    onChange={(e) =>
                      setNewUserData({ ...newUserData, email: e.target.value })
                    }
                    className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-400"
                    required
                  />
                </div>

                <div>
                  <label className="text-xs text-slate-300 font-medium block mb-1.5">
                    Phone Number
                  </label>
                  <Input
                    placeholder="+91 9876543210"
                    value={newUserData.phone}
                    onChange={(e) =>
                      setNewUserData({ ...newUserData, phone: e.target.value })
                    }
                    className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-400"
                  />
                </div>

                <div>
                  <label className="text-xs text-slate-300 font-medium block mb-1.5">
                    Initial Password
                  </label>
                  <Input
                    type="password"
                    placeholder="Temporary Password (optional)"
                    value={newUserData.password}
                    onChange={(e) =>
                      setNewUserData({ ...newUserData, password: e.target.value })
                    }
                    className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-400"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-slate-300 font-medium block mb-1.5">
                      System Role
                    </label>
                    <select
                      value={newUserData.role}
                      onChange={(e) =>
                        setNewUserData({
                          ...newUserData,
                          role: e.target.value as "user" | "admin",
                        })
                      }
                      className="w-full h-10 px-3 rounded-md bg-slate-700 border border-slate-600 text-white text-sm focus:outline-none focus:border-blue-500"
                    >
                      <option value="user">User / Driver</option>
                      <option value="admin">Administrator</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs text-slate-300 font-medium block mb-1.5">
                      Status
                    </label>
                    <select
                      value={newUserData.status}
                      onChange={(e) =>
                        setNewUserData({
                          ...newUserData,
                          status: e.target.value as "active" | "inactive",
                        })
                      }
                      className="w-full h-10 px-3 rounded-md bg-slate-700 border border-slate-600 text-white text-sm focus:outline-none focus:border-blue-500"
                    >
                      <option value="active">Active</option>
                      <option value="inactive">Inactive</option>
                    </select>
                  </div>
                </div>

                <div className="flex gap-2 justify-end pt-4 border-t border-slate-700">
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => setShowAddModal(false)}
                    className="text-slate-400 hover:text-white"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    Create User
                  </Button>
                </div>
              </CardContent>
            </form>
          </Card>
        </div>
      )}

      {/* MODAL 2: EDIT USER */}
      {editingUser && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <Card className="bg-slate-800 border-slate-700 w-full max-w-lg shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <CardHeader className="flex flex-row items-center justify-between border-b border-slate-700 pb-4">
              <div className="flex items-center gap-2">
                <Edit2 className="h-5 w-5 text-amber-500" />
                <CardTitle className="text-white text-xl">
                  Edit User: {editingUser.name}
                </CardTitle>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setEditingUser(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </Button>
            </CardHeader>
            <form onSubmit={handleSaveEdit}>
              <CardContent className="space-y-4 pt-4">
                <div>
                  <label className="text-xs text-slate-300 font-medium block mb-1.5">
                    Full Name
                  </label>
                  <Input
                    value={editFormData.name}
                    onChange={(e) =>
                      setEditFormData({ ...editFormData, name: e.target.value })
                    }
                    className="bg-slate-700 border-slate-600 text-white"
                    required
                  />
                </div>

                <div>
                  <label className="text-xs text-slate-300 font-medium block mb-1.5">
                    Email Address
                  </label>
                  <Input
                    type="email"
                    value={editFormData.email}
                    onChange={(e) =>
                      setEditFormData({ ...editFormData, email: e.target.value })
                    }
                    className="bg-slate-700 border-slate-600 text-white"
                    required
                  />
                </div>

                <div>
                  <label className="text-xs text-slate-300 font-medium block mb-1.5">
                    Phone Number
                  </label>
                  <Input
                    value={editFormData.phone}
                    onChange={(e) =>
                      setEditFormData({ ...editFormData, phone: e.target.value })
                    }
                    className="bg-slate-700 border-slate-600 text-white"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-slate-300 font-medium block mb-1.5">
                      System Role
                    </label>
                    <select
                      value={editFormData.role}
                      onChange={(e) =>
                        setEditFormData({
                          ...editFormData,
                          role: e.target.value as "user" | "admin",
                        })
                      }
                      className="w-full h-10 px-3 rounded-md bg-slate-700 border border-slate-600 text-white text-sm focus:outline-none focus:border-blue-500"
                    >
                      <option value="user">User / Driver</option>
                      <option value="admin">Administrator</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs text-slate-300 font-medium block mb-1.5">
                      Status
                    </label>
                    <select
                      value={editFormData.status}
                      onChange={(e) =>
                        setEditFormData({
                          ...editFormData,
                          status: e.target.value as "active" | "inactive",
                        })
                      }
                      className="w-full h-10 px-3 rounded-md bg-slate-700 border border-slate-600 text-white text-sm focus:outline-none focus:border-blue-500"
                    >
                      <option value="active">Active</option>
                      <option value="inactive">Inactive</option>
                    </select>
                  </div>
                </div>

                <div className="flex gap-2 justify-end pt-4 border-t border-slate-700">
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => setEditingUser(null)}
                    className="text-slate-400 hover:text-white"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    className="bg-amber-600 hover:bg-amber-700 text-white"
                  >
                    Save Changes
                  </Button>
                </div>
              </CardContent>
            </form>
          </Card>
        </div>
      )}

      {/* MODAL 3: VIEW USER DETAILS */}
      {viewingUser && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <Card className="bg-slate-800 border-slate-700 w-full max-w-md shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <CardHeader className="flex flex-row items-center justify-between border-b border-slate-700 pb-4">
              <div className="flex items-center gap-2">
                <Eye className="h-5 w-5 text-blue-400" />
                <CardTitle className="text-white text-xl">User Profile</CardTitle>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setViewingUser(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-6 pt-6">
              <div className="flex items-center gap-4">
                <div
                  className={`h-16 w-16 rounded-full flex items-center justify-center text-white text-2xl font-bold shadow-lg ${
                    viewingUser.role === "admin"
                      ? "bg-gradient-to-br from-purple-500 to-indigo-600"
                      : "bg-gradient-to-br from-blue-500 to-cyan-600"
                  }`}
                >
                  {viewingUser.name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">
                    {viewingUser.name}
                  </h2>
                  <p className="text-sm text-slate-400 flex items-center gap-1.5 mt-0.5">
                    <Mail className="h-3.5 w-3.5 text-slate-500" />
                    {viewingUser.email}
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <span
                      className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase ${
                        viewingUser.role === "admin"
                          ? "bg-purple-500/20 text-purple-300 border border-purple-500/40"
                          : "bg-blue-500/20 text-blue-300 border border-blue-500/40"
                      }`}
                    >
                      {viewingUser.role}
                    </span>
                    <span
                      className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        viewingUser.status === "active"
                          ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                          : "bg-rose-500/20 text-rose-400 border border-rose-500/40"
                      }`}
                    >
                      {viewingUser.status.toUpperCase()}
                    </span>
                  </div>
                </div>
              </div>

              <div className="space-y-3 bg-slate-900/60 p-4 rounded-lg border border-slate-700/60 text-sm">
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400 flex items-center gap-1.5">
                    <Phone className="h-4 w-4 text-slate-500" /> Phone
                  </span>
                  <span className="text-white font-medium">
                    {viewingUser.phone || "Not provided"}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400 flex items-center gap-1.5">
                    <Calendar className="h-4 w-4 text-slate-500" /> Member Since
                  </span>
                  <span className="text-white font-medium">
                    {viewingUser.joinDate || "Recent"}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400 flex items-center gap-1.5">
                    <UserIcon className="h-4 w-4 text-slate-500" /> System Identifier
                  </span>
                  <span className="text-slate-300 font-mono text-xs">
                    {viewingUser.id}
                  </span>
                </div>
                {viewingUser.backendId && (
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">Database Record ID</span>
                    <span className="text-emerald-400 font-mono text-xs">
                      #{viewingUser.backendId}
                    </span>
                  </div>
                )}
              </div>

              <div className="flex gap-2 justify-end pt-2">
                <Button
                  variant="outline"
                  onClick={() => {
                    const target = viewingUser;
                    setViewingUser(null);
                    startEdit(target);
                  }}
                  className="border-slate-600 bg-slate-700 text-white hover:bg-slate-600"
                >
                  <Edit2 className="h-4 w-4 mr-1.5" /> Edit Profile
                </Button>
                <Button
                  onClick={() => setViewingUser(null)}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  Close
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* MODAL 4: DELETE CONFIRMATION */}
      {deletingUser && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <Card className="bg-slate-800 border-slate-700 w-full max-w-md shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <CardHeader className="flex flex-row items-center gap-3 border-b border-slate-700 pb-4">
              <div className="h-10 w-10 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center flex-shrink-0">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <CardTitle className="text-white text-lg">Delete User Account</CardTitle>
                <p className="text-slate-400 text-xs mt-0.5">
                  This action will permanently delete the user account.
                </p>
              </div>
            </CardHeader>
            <CardContent className="space-y-4 pt-4">
              <p className="text-slate-300 text-sm">
                Are you sure you want to delete user{" "}
                <span className="font-semibold text-white">
                  "{deletingUser.name}" ({deletingUser.email})
                </span>
                ? This action cannot be undone.
              </p>

              <div className="flex gap-2 justify-end pt-2">
                <Button
                  variant="ghost"
                  onClick={() => setDeletingUser(null)}
                  className="text-slate-400 hover:text-white"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleConfirmDelete}
                  className="bg-rose-600 hover:bg-rose-700 text-white"
                >
                  <Trash2 className="h-4 w-4 mr-1.5" /> Yes, Delete User
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
