'use client';

import { useState, useEffect, useRef } from 'react';
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
  Heart,
  Wallet,
  Menu,
  X,
  LogOut,
  ChevronUp,
  ChevronDown
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
  const [profileOpen, setProfileOpen] = useState(false);
  const profileTriggerRef = useRef<HTMLButtonElement>(null);
  const profilePopupRef = useRef<HTMLDivElement>(null);

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
            w-72 flex flex-col
            ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0 lg:w-64'}
          `}
        >
          <div className="p-6 hidden lg:flex flex-shrink-0">
            <Link href="/" className="flex items-center gap-3">
              <Car className="h-8 w-8 text-blue-500" />
              <span className="text-xl font-bold text-white">ParkPilot</span>
            </Link>
          </div>
          <nav className="px-4 py-2 space-y-1 flex-1 overflow-y-auto" style={{ paddingBottom: '112px' }}>
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
          <div className="border-t border-slate-800 w-full bg-slate-900 absolute bottom-0 left-0 right-0 z-10">
            <div className="p-4 space-y-2 relative">
              <button
                type="button"
                ref={profileTriggerRef}
                onClick={() => setProfileOpen(!profileOpen)}
                className="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-slate-800 transition-colors"
              >
                <div className="h-12 w-12 rounded-full bg-blue-600 flex items-center justify-center text-white font-semibold text-lg flex-shrink-0">
                  {getInitials()}
                </div>
                <div className="flex-1 min-w-0 text-left">
                  <p className="text-sm font-semibold text-white truncate">{user.firstName} {user.lastName}</p>
                  <p className="text-xs text-slate-400 truncate">{user.email}</p>
                </div>
                <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center text-slate-400">
                  {profileOpen ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronUp className="h-4 w-4" />
                  )}
                </span>
              </button>

              <div className="absolute left-0 right-0 bottom-full mb-2">
                {profileOpen && (
                  <>
                    <div
                      className="fixed inset-0 z-30 bg-transparent"
                      onClick={() => setProfileOpen(false)}
                    />
                    <div
                      ref={profilePopupRef}
                      className="relative z-40"
                    >
                      <div className="bg-slate-800/95 backdrop-blur-sm rounded-2xl border border-slate-700 shadow-2xl overflow-hidden">
                        <div className="p-1">
                          <Link
                            href="/user/profile"
                            onClick={() => { setSidebarOpen(false); setProfileOpen(false); }}
                            className="block w-full"
                          >
                            <div
                              className="w-full min-h-[44px] h-[44px] flex flex-row items-center justify-start gap-3 px-3 py-0 text-slate-200 hover:text-white hover:bg-slate-700/60 rounded-xl transition-colors"
                            >
                              <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center text-slate-400">
                                <User className="h-5 w-5" />
                              </span>
                              <span className="text-sm font-semibold truncate flex-1 min-w-0 text-left">
                                Profile
                              </span>
                            </div>
                          </Link>
                          <Link
                            href="/user/settings"
                            onClick={() => { setSidebarOpen(false); setProfileOpen(false); }}
                            className="block w-full"
                          >
                            <div
                              className="w-full min-h-[44px] h-[44px] flex flex-row items-center justify-start gap-3 px-3 py-0 text-slate-200 hover:text-white hover:bg-slate-700/60 rounded-xl transition-colors"
                            >
                              <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center text-slate-400">
                                <Settings className="h-5 w-5" />
                              </span>
                              <span className="text-sm font-semibold truncate flex-1 min-w-0 text-left">
                                Settings
                              </span>
                            </div>
                          </Link>
                        </div>
                        <div className="border-t border-slate-700 p-1">
                          <button
                            type="button"
                            onClick={() => { setProfileOpen(false); logout(); }}
                            className="w-full min-h-[44px] h-[44px] flex flex-row items-center justify-start gap-3 px-3 py-0 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-xl transition-colors"
                          >
                            <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center">
                              <LogOut className="h-5 w-5" />
                            </span>
                            <span className="text-sm font-semibold truncate flex-1 min-w-0 text-left">
                              Sign out
                            </span>
                          </button>
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
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
            <div className="flex items-center gap-3">
              <Link href="/user/notifications" className="relative">
                <Button variant="ghost" size="sm" className="text-slate-300 hover:text-white hover:bg-slate-800">
                  <Bell className="h-5 w-5" />
                </Button>
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
              </Link>
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
