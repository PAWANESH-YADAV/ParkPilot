'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Wallet,
  CreditCard,
  Plus,
  Trash2,
  ArrowUpRight,
  ArrowDownLeft,
  CheckCircle2
} from 'lucide-react';

export default function WalletPage() {
  const [balance, setBalance] = useState(250.50);
  const [showAddCard, setShowAddCard] = useState(false);

  const transactions = [
    { id: '1', type: 'credit', amount: 50, description: 'Added to wallet', date: 'Dec 18, 2024' },
    { id: '2', type: 'debit', amount: 45, description: 'Parking - Downtown Garage', date: 'Dec 18, 2024' },
    { id: '3', type: 'credit', amount: 100, description: 'Added to wallet', date: 'Dec 15, 2024' },
    { id: '4', type: 'debit', amount: 36, description: 'Parking - City Center', date: 'Dec 12, 2024' },
  ];

  const cards = [
    { id: '1', type: 'Visa', last4: '4242', expiry: '12/26', isDefault: true },
    { id: '2', type: 'Mastercard', last4: '8888', expiry: '08/25', isDefault: false },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Wallet</h1>
        <p className="text-slate-400">Manage your balance and payment methods</p>
      </div>

      {/* Balance Card */}
      <Card className="bg-gradient-to-r from-blue-600 to-cyan-600 border-none">
        <CardContent className="p-8">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-blue-100 text-sm mb-2">Available Balance</p>
              <p className="text-5xl font-bold text-white">${balance.toFixed(2)}</p>
            </div>
            <Wallet className="h-12 w-12 text-white/30" />
          </div>
          <div className="flex gap-3 mt-6">
            <Button className="bg-white text-blue-600 hover:bg-blue-50">
              Add Money
            </Button>
            <Button variant="outline" className="border-white text-white hover:bg-white/10">
              Withdraw
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Saved Cards */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader className="flex flex-row justify-between items-center">
          <CardTitle className="text-white text-xl">Saved Cards</CardTitle>
          <Button size="sm" onClick={() => setShowAddCard(!showAddCard)}>
            <Plus className="h-4 w-4 mr-2" />
            Add Card
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {cards.map((card) => (
            <div key={card.id} className="flex items-center justify-between p-4 bg-slate-700 rounded-lg">
              <div className="flex items-center gap-4">
                <div className="p-2 bg-slate-600 rounded">
                  <CreditCard className="h-6 w-6 text-white" />
                </div>
                <div>
                  <p className="text-white font-medium">{card.type} •••• {card.last4}</p>
                  <p className="text-slate-400 text-sm">Expires {card.expiry}</p>
                </div>
                {card.isDefault && (
                  <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs flex items-center gap-1">
                    <CheckCircle2 className="h-3 w-3" />
                    Default
                  </span>
                )}
              </div>
              <Button variant="ghost" size="sm" className="text-red-400">
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Transaction History */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white text-xl">Transaction History</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {transactions.map((tx) => (
            <div key={tx.id} className="flex items-center justify-between p-3">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-full ${tx.type === 'credit' ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
                  {tx.type === 'credit' ? (
                    <ArrowDownLeft className="h-5 w-5 text-green-500" />
                  ) : (
                    <ArrowUpRight className="h-5 w-5 text-red-500" />
                  )}
                </div>
                <div>
                  <p className="text-white">{tx.description}</p>
                  <p className="text-slate-400 text-sm">{tx.date}</p>
                </div>
              </div>
              <p className={`font-semibold ${tx.type === 'credit' ? 'text-green-500' : 'text-red-500'}`}>
                {tx.type === 'credit' ? '+' : '-'}$${tx.amount.toFixed(2)}
              </p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
