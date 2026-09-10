"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Users, UserPlus, Edit2, Trash2, Eye, ShieldCheck, Ban, Search } from "lucide-react";

interface User {
  id: string;
  name: string;
  email: string;
  phone: string;
  role: "user" | "admin";
  status: "active" | "inactive";
  joinDate: string;
}

export default function UserManagementPage() {
  const [users, setUsers] = useState<User[]>([
    { id: "1", name: "John Doe", email: "john@example.com", phone: "+1234567890", role: "user", status: "active", joinDate: "2024-01-15" },
    { id: "2", name: "Jane Smith", email: "jane@example.com", phone: "+1987654321", role: "user", status: "active", joinDate: "2024-02-20" },
    { id: "3", name: "Bob Wilson", email: "bob@example.com", phone: "+1122334455", role: "user", status: "inactive", joinDate: "2024-03-10" },
  ]);
  const [searchQuery, setSearchQuery] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);

  const filteredUsers = users.filter(user =>
    user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">User Management</h1>
          <p className="text-slate-400">Manage all system users</p>
        </div>
        <Button onClick={() => setShowAddModal(true)}>
          <UserPlus className="h-4 w-4 mr-2" />
          Add New User
        </Button>
      </div>

      <Card className="bg-slate-800 border-slate-700">
        <CardContent className="p-6">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
            <Input
              placeholder="Search users..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-slate-700 border-slate-600 text-white"
            />
          </div>
        </CardContent>
      </Card>

      <Card className="bg-slate-800 border-slate-700">
        <CardContent className="p-6">
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="pb-3 text-slate-400 font-medium">User</th>
                  <th className="pb-3 text-slate-400 font-medium">Role</th>
                  <th className="pb-3 text-slate-400 font-medium">Status</th>
                  <th className="pb-3 text-slate-400 font-medium">Join Date</th>
                  <th className="pb-3 text-slate-400 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map((user) => (
                  <tr key={user.id} className="border-b border-slate-700/50">
                    <td className="py-4">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-medium">
                          {user.name[0]}
                        </div>
                        <div>
                          <p className="text-white font-medium">{user.name}</p>
                          <p className="text-slate-400 text-sm">{user.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        user.role === "admin" ? "bg-purple-500/20 text-purple-400" : "bg-blue-500/20 text-blue-400"
                      }`}>
                        {user.role}
                      </span>
                    </td>
                    <td className="py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        user.status === "active" ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
                      }`}>
                        {user.status}
                      </span>
                    </td>
                    <td className="py-4 text-slate-300">{user.joinDate}</td>
                    <td className="py-4">
                      <div className="flex justify-end gap-2">
                        <Button variant="ghost" size="sm">
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm">
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm">
                          <ShieldCheck className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm" className="text-red-400">
                          <Ban className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="bg-slate-800 border-slate-700 w-full max-w-md mx-4">
            <CardHeader>
              <CardTitle className="text-white text-xl">Add New User</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input placeholder="Full Name" className="bg-slate-700 border-slate-600 text-white" />
              <Input placeholder="Email Address" type="email" className="bg-slate-700 border-slate-600 text-white" />
              <Input placeholder="Phone Number" className="bg-slate-700 border-slate-600 text-white" />
              <Input placeholder="Password" type="password" className="bg-slate-700 border-slate-600 text-white" />
              <div className="flex gap-2 justify-end pt-4">
                <Button variant="ghost" onClick={() => setShowAddModal(false)}>Cancel</Button>
                <Button>Add User</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
