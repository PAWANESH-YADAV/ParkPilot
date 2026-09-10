"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CreditCard, DollarSign, TrendingUp, Download, Eye } from "lucide-react";

interface Transaction {
  id: string;
  user: string;
  date: string;
  amount: string;
  type: "payment" | "refund";
  method: string;
  status: "success" | "pending" | "failed";
}

export default function BillingPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([
    { id: "TXN-001", user: "John Doe", date: "2024-12-20", amount: "$45.00", type: "payment", method: "Credit Card", status: "success" },
    { id: "TXN-002", user: "Jane Smith", date: "2024-12-19", amount: "$36.00", type: "payment", method: "Wallet", status: "success" },
    { id: "TXN-003", user: "Bob Wilson", date: "2024-12-18", amount: "$10.00", type: "refund", method: "Original", status: "success" },
    { id: "TXN-004", user: "Alice Brown", date: "2024-12-17", amount: "$90.00", type: "payment", method: "Credit Card", status: "success" },
  ]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Payment & Billing</h1>
        <p className="text-slate-400">View transactions and revenue</p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-6">
            <p className="text-slate-400 text-sm mb-2">Total Revenue</p>
            <p className="text-3xl font-bold text-white">$12,450.00</p>
            <p className="text-green-400 text-sm flex items-center gap-1 mt-2">
              <TrendingUp className="h-4 w-4" />
              +12.5% from last month
            </p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-6">
            <p className="text-slate-400 text-sm mb-2">Total Transactions</p>
            <p className="text-3xl font-bold text-white">342</p>
            <p className="text-blue-400 text-sm mt-2">This month</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-6">
            <p className="text-slate-400 text-sm mb-2">Refunds Issued</p>
            <p className="text-3xl font-bold text-white">$450.00</p>
            <p className="text-slate-400 text-sm mt-2">3 refunds</p>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-slate-800 border-slate-700">
        <CardContent className="p-6">
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="pb-3 text-slate-400 font-medium">Transaction ID</th>
                  <th className="pb-3 text-slate-400 font-medium">User</th>
                  <th className="pb-3 text-slate-400 font-medium">Date</th>
                  <th className="pb-3 text-slate-400 font-medium">Type</th>
                  <th className="pb-3 text-slate-400 font-medium">Method</th>
                  <th className="pb-3 text-slate-400 font-medium">Amount</th>
                  <th className="pb-3 text-slate-400 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((txn) => (
                  <tr key={txn.id} className="border-b border-slate-700/50">
                    <td className="py-4 text-white font-medium">{txn.id}</td>
                    <td className="py-4 text-slate-300">{txn.user}</td>
                    <td className="py-4 text-slate-300">{txn.date}</td>
                    <td className="py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        txn.type === "payment" ? "bg-blue-500/20 text-blue-400" : "bg-red-500/20 text-red-400"
                      }`}>
                        {txn.type}
                      </span>
                    </td>
                    <td className="py-4 text-slate-300">{txn.method}</td>
                    <td className="py-4 text-white font-bold">{txn.amount}</td>
                    <td className="py-4">
                      <div className="flex justify-end gap-2">
                        <Button variant="ghost" size="sm">
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm">
                          <Download className="h-4 w-4" />
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
    </div>
  );
}
