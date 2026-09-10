'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Car, Mail, Lock, Eye, EyeOff, AlertCircle } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';

export default function LoginPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const { login, isLoading } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!formData.email || !formData.password) {
      setError('Please fill in all fields');
      return;
    }

    const result = await login(formData.email, formData.password);
    if (result.success) {
      if (result.isAdmin) {
        router.push('/dashboard');
      } else {
        router.push('/user');
      }
    } else {
      setError(result.error || 'Invalid email or password');
    }
  };

  const fillCreds = (email: string, password: string) => {
    setFormData({ email, password });
    setError('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-slate-800 border-slate-700">
        <CardHeader className="text-center">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Car className="h-10 w-10 text-blue-500" />
            <span className="text-3xl font-bold text-white">ParkPilot</span>
          </div>
          <CardTitle className="text-2xl text-white">Welcome Back!</CardTitle>
          <p className="text-slate-400">Sign in to your account</p>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <div className="p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-400 text-sm flex items-start gap-2">
              <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg space-y-2">
            <p className="text-blue-300 text-xs font-medium">Demo Accounts</p>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => fillCreds('user@parkpilot.com', 'User@123')}
                className="text-xs bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 px-2.5 py-1 rounded-md transition-colors"
              >
                User: user@parkpilot.com
              </button>
              <button
                type="button"
                onClick={() => fillCreds('admin@parkpilot.com', 'Admin@123')}
                className="text-xs bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 px-2.5 py-1 rounded-md transition-colors"
              >
                Admin: admin@parkpilot.com
              </button>
            </div>
            <p className="text-blue-400/70 text-[11px]">Click to auto-fill credentials</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label className="text-slate-300 text-sm">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                <Input
                  type="email"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="pl-10 bg-slate-700 border-slate-600 text-white placeholder:text-slate-500"
                  autoComplete="email"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-slate-300 text-sm">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                <Input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="pl-10 pr-10 bg-slate-700 border-slate-600 text-white placeholder:text-slate-500"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-300"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full bg-blue-600 hover:bg-blue-700"
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>

          <div className="text-center pt-4">
            <p className="text-slate-400">
              Don&apos;t have an account?{' '}
              <Link href="/register" className="text-blue-400 hover:text-blue-300 font-medium">
                Sign Up
              </Link>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
