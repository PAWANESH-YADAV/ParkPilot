'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  CreditCard,
  Download,
  MapPin,
  Calendar,
  CheckCircle2
} from 'lucide-react';

export default function PaymentsPage() {
  const payments = [
    {
      id: 'PAY-12345',
      date: 'Dec 18, 2024',
      amount: '$45.00',
      location: 'Downtown Garage',
      status: 'Completed',
      method: 'Visa •••• 4242',
    },
    {
      id: 'PAY-12344',
      date: 'Dec 12, 2024',
      amount: '$36.00',
      location: 'City Center Parking',
      status: 'Completed',
      method: 'Wallet',
    },
    {
      id: 'PAY-12343',
      date: 'Dec 10, 2024',
      amount: '$90.00',
      location: 'Waterfront Parking',
      status: 'Completed',
      method: 'Mastercard •••• 8888',
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Payment History</h1>
        <p className="text-slate-400">View and download your payment receipts</p>
      </div>

      {/* Summary */}
      <div className="grid md:grid-cols-3 gap-4">
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-6">
            <p className="text-slate-400 text-sm mb-2">Total Spent</p>
            <p className="text-3xl font-bold text-white">$1,245.00</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-6">
            <p className="text-slate-400 text-sm mb-2">This Month</p>
            <p className="text-3xl font-bold text-white">$171.00</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-6">
            <p className="text-slate-400 text-sm mb-2">Total Payments</p>
            <p className="text-3xl font-bold text-white">24</p>
          </CardContent>
        </Card>
      </div>

      {/* Payments List */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white text-xl">All Payments</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {payments.map((payment) => (
            <div key={payment.id} className="p-4 bg-slate-700 rounded-lg">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <p className="text-white font-semibold text-lg">{payment.location}</p>
                    <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs flex items-center gap-1">
                      <CheckCircle2 className="h-3 w-3" />
                      {payment.status}
                    </span>
                  </div>
                  <p className="text-slate-400 text-sm flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    {payment.date}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-white">{payment.amount}</p>
                  <p className="text-slate-400 text-sm flex items-center gap-1 justify-end">
                    <CreditCard className="h-4 w-4" />
                    {payment.method}
                  </p>
                </div>
              </div>
              <div className="flex justify-end pt-2 border-t border-slate-600">
                <Button variant="outline" size="sm" className="border-slate-600 text-slate-300">
                  <Download className="h-4 w-4 mr-2" />
                  Download Receipt
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
