'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  QrCode,
  Clock,
  RefreshCw,
  Info
} from 'lucide-react';

export default function QrCodePage() {
  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-white mb-2">QR Code Entry</h1>
        <p className="text-slate-400">Scan this QR code for quick entry and exit</p>
      </div>

      <Card className="bg-slate-800 border-slate-700">
        <CardContent className="p-8">
          <div className="flex flex-col items-center">
            {/* QR Code Placeholder */}
            <div className="w-64 h-64 bg-white rounded-lg p-4 mb-6 flex items-center justify-center">
              <QrCode className="w-full h-full text-slate-800" />
            </div>

            <div className="text-center mb-6">
              <p className="text-white font-semibold text-lg">John Doe</p>
              <p className="text-slate-400">User ID: JD-12345</p>
            </div>

            <div className="flex items-center gap-2 text-yellow-400 mb-6">
              <Clock className="h-5 w-5" />
              <span>Expires in 30 minutes</span>
            </div>

            <button className="flex items-center gap-2 text-blue-400 hover:text-blue-300">
              <RefreshCw className="h-5 w-5" />
              Refresh QR Code
            </button>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Info className="h-5 w-5 text-blue-500" />
            How to use
          </CardTitle>
        </CardHeader>
        <CardContent className="text-slate-300 space-y-2">
          <p>1. Approach the parking lot entrance</p>
          <p>2. Scan this QR code at the entry gate</p>
          <p>3. The gate will open automatically</p>
          <p>4. Use the same QR code for exit</p>
        </CardContent>
      </Card>
    </div>
  );
}
