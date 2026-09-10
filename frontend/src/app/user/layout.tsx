'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  Car,
  MapPin,
  CreditCard,
  History,
  Bell,
  User,
  Settings,
  LayoutDashboard,
  QrCode,
  Heart,
  Wallet,
  Menu,
  X,
  LogOut
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/lib/auth-context';

export default function UserLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout, isLoading } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    if (!isLoading) {
      if (!user) {
        router.push('/login');
      } else if (user.isAdmin) {
        router.push('/dashboard');
      }
    }
  }, [user, isLoading, router]);

  const navItems = [
    { name: 'Dashboard', href: '/user', icon: <LayoutDashboard className="h-5 w-5" /> },
    { name: 'Find Parking', href: '/user/find-parking', icon: <MapPin className="h-5 w-5" /> },
    { name: 'My Bookings', href: '/user/bookings', icon: <Car className="h-5 w-5" /> },
    { name: 'My Vehicles', href: '/user/vehicles', icon: <Car className="h-5 w-5" /> },
    { name: 'Wallet', href: '/user/wallet', icon: <Wallet className="h-5 w-5" /> },
    { name: 'Payment History', href: '/user/payments', icon: <CreditCard className="h-5 w-5" /> },
    { name: 'Parking History', href: '/user/history', icon: <History className="h-5 w-5" /> },
    { name: 'Favorites', href: '/user/favorites', icon: <Heart className="h-5 w-5" /> },
    { name: 'QR Code', href: '/user/qr-code', icon: <QrCode className="h-5 w-5" /> },
    { name: 'Profile', href: '/user/profile', icon: <User className="h-5 w-5" /> },
    { name: 'Notifications', href: '/user/notifications', icon: <Bell className="h-5 w-5" /> },
    { name: 'Settings', href: '/user/settings', icon: <Settings className="h-5 w-5" /> },
  ];

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  const getInitials = () => {
    return `${user.firstName[0]}${user.lastName[0]}`.toUpperCase();
  };

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-50 h-16 bg-slate-900 border-b border-slate-800 flex items-center px-4 justify-between">
        <Button variant="ghost" size="sm" onClick={() => setSidebarOpen(!sidebarOpen)}>
          {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>
        <div className="flex items-center gap-2">
          <Car className="h-6 w-6 text-blue-500" />
          <span className="text-lg font-bold text-white">ParkPilot</span>
        </div>
        <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
          <Bell className="h-5 w-5" />
        </Button>
      </div>

      <div className="flex h-screen pt-16 lg:pt-0">
        {/* Sidebar Overlay for Mobile */}
        {sidebarOpen && (
          <div 
            className="lg:hidden fixed inset-0 bg-black/50 z-40" 
            onClick={() => setSidebarOpen(false)} 
          />
        )}

        {/* Sidebar */}
        <aside
          className={`
            fixed lg:static inset-y-0 left-0 z-50
            bg-slate-900 border-r border-slate-800
            transition-all duration-300 ease-in-out
            w-72
            ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0 lg:w-64'}
          `}
        >
          <div className="p-6 hidden lg:flex">
            <Link href="/" className="flex items-center gap-3">
              <Car className="h-8 w-8 text-blue-500" />
              <span className="text-xl font-bold text-white">ParkPilot</span>
            </Link>
          </div>
          <nav className="px-4 py-2 space-y-1 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 180px)' }}>
            {navItems.map((item) => (
              <Link key={item.href} href={item.href} onClick={() => setSidebarOpen(false)}>
                <Button
                  variant={pathname === item.href ? 'default' : 'ghost'}
                  className={`
                    w-full justify-start gap-3 py-3 h-auto
                    ${
                      pathname === item.href
                        ? 'bg-blue-600 hover:bg-blue-700 text-white'
                        : 'text-slate-300 hover:text-white hover:bg-slate-800'
                    }
                    rounded-lg transition-all duration-200
                  `}
                >
                  {item.icon}
                  <span className="text-sm font-medium truncate">{item.name}</span>
                </Button>
              </Link>
            ))}
          </nav>
          <div className="p-4 border-t border-slate-800 mt-auto">
            <Button
              variant="ghost"
              onClick={() => logout()}
              className="w-full justify-start gap-3 py-3 h-auto text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg"
            >
              <LogOut className="h-5 w-5" />
              <span className="text-sm font-medium">Logout</span>
            </Button>
          </div>
        </aside>

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <header className="h-16 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-6 hidden lg:flex">
            <div className="flex items-center gap-3">
              <Button variant="ghost" size="sm" onClick={() => setSidebarOpen(!sidebarOpen)}>
                <Menu className="h-5 w-5" />
              </Button>
            </div>
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
                <Bell className="h-5 w-5" />
              </Button>
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <p className="text-sm font-medium text-white">{user.firstName} {user.lastName}</p>
                  <p className="text-xs text-slate-500">{user.email}</p>
                </div>
                <div className="h-10 w-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-semibold">
                  {getInitials()}
                </div>
              </div>
            </div>
          </header>

          <main className="flex-1 overflow-auto p-4 lg:p-6">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
