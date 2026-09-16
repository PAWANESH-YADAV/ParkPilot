"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Car,
  MapPin,
  CreditCard,
  BarChart3,
  Settings,
  LayoutDashboard,
  Zap,
  LogOut,
  Users,
  Calendar,
  Tag,
  Bell,
  Shield,
  Menu,
  X,
  BatteryCharging,
  Leaf,
  Video,
  TrendingUp,
  Mic,
  ChevronDown,
  ChevronRight,
  ChevronUp,
  SlidersHorizontal,
  User,
  Sun,
  Moon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";
import { useTheme } from "@/lib/theme-context";

type NavItem =
  | {
      kind: "link";
      name: string;
      href: string;
      icon: React.ReactNode;
    }
  | {
      kind: "group";
      name: string;
      icon: React.ReactNode;
      children: { name: string; href: string; icon: React.ReactNode }[];
    };

export default function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout, isLoading } = useAuth();
  const { theme, setTheme, toggleTheme } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [groupsOpen, setGroupsOpen] = useState<Record<string, boolean>>({
    "System Configuration": true,
  });
  const [profileOpen, setProfileOpen] = useState(false);
  const profileTriggerRef = useRef<HTMLButtonElement>(null);
  const profilePopupRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isLoading) {
      if (!user) {
        router.push('/login');
      } else if (!user.isAdmin) {
        router.push('/user');
      }
    }
  }, [user, isLoading, router]);

  const navItems: NavItem[] = [
    {
      kind: "link",
      name: "Dashboard",
      href: "/dashboard",
      icon: <LayoutDashboard className="h-5 w-5" />,
    },
    {
      kind: "link",
      name: "User Management",
      href: "/dashboard/users",
      icon: <Users className="h-5 w-5" />,
    },
    {
      kind: "link",
      name: "Parking Lot Management",
      href: "/dashboard/parking-lots",
      icon: <MapPin className="h-5 w-5" />,
    },
    {
      kind: "link",
      name: "Parking Slot Management",
      href: "/dashboard/parking-slots",
      icon: <Car className="h-5 w-5" />,
    },
    {
      kind: "link",
      name: "Booking Management",
      href: "/dashboard/bookings",
      icon: <Calendar className="h-5 w-5" />,
    },
    {
      kind: "link",
      name: "Sensor & Device Monitoring",
      href: "/dashboard/sensors",
      icon: <Zap className="h-5 w-5" />,
    },
    {
      kind: "link",
      name: "Pricing Management",
      href: "/dashboard/pricing",
      icon: <Tag className="h-5 w-5" />,
    },
    {
      kind: "link",
      name: "Payment & Billing",
      href: "/dashboard/billing",
      icon: <CreditCard className="h-5 w-5" />,
    },
    {
      kind: "link",
      name: "Analytics & Reports",
      href: "/dashboard/analytics",
      icon: <BarChart3 className="h-5 w-5" />,
    },
    {
      kind: "group",
      name: "System Configuration",
      icon: <Settings className="h-5 w-5" />,
      children: [
        {
          name: "1. Audit & Security",
          href: "/dashboard/audit",
          icon: <Shield className="h-4 w-4" />,
        },
        {
          name: "2. EV Charging",
          href: "/dashboard/ev-charging",
          icon: <BatteryCharging className="h-4 w-4" />,
        },
        {
          name: "3. Carbon Tracker",
          href: "/dashboard/carbon",
          icon: <Leaf className="h-4 w-4" />,
        },
        {
          name: "4. Surveillance",
          href: "/dashboard/surveillance",
          icon: <Video className="h-4 w-4" />,
        },
        {
          name: "5. Dynamic Pricing",
          href: "/dashboard/dynamic-pricing",
          icon: <TrendingUp className="h-4 w-4" />,
        },
      ],
    },
    {
      kind: "link",
      name: "Voice Assistant",
      href: "/dashboard/voice",
      icon: <Mic className="h-5 w-5" />,
    },
  ];

  const toggleGroup = (name: string) => {
    setGroupsOpen((prev) => ({ ...prev, [name]: !prev[name] }));
  };

  const isChildActive = (group: Extract<NavItem, { kind: "group" }>) =>
    group.children.some((c) => pathname === c.href);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center">
        <div className="text-slate-900 dark:text-white text-xl font-medium">Loading...</div>
      </div>
    );
  }

  if (!user || !user.isAdmin) {
    return null;
  }

  const getInitials = () => {
    return `${user.firstName[0]}${user.lastName[0]}`.toUpperCase();
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors duration-200">
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-50 h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center px-4 justify-between">
        <Button variant="ghost" size="sm" onClick={() => setSidebarOpen(!sidebarOpen)} className="text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800">
          {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>
        <div className="flex items-center gap-2">
          <Car className="h-6 w-6 text-blue-600 dark:text-blue-500" />
          <span className="text-lg font-bold text-slate-900 dark:text-white">ParkPilot</span>
        </div>
        <div className="w-8" /> {/* Spacer */}
      </div>

      <div className="flex h-screen pt-16 lg:pt-0">
        {/* Sidebar Overlay for Mobile */}
        {sidebarOpen && (
          <div 
            className="lg:hidden fixed inset-0 bg-black/40 backdrop-blur-xs z-40" 
            onClick={() => setSidebarOpen(false)} 
          />
        )}

        {/* Sidebar */}
        <aside className={`
          fixed lg:static inset-y-0 left-0 z-50
          bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800
          transition-all duration-300 ease-in-out
          w-72 flex flex-col shadow-xs lg:shadow-none
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0 lg:w-64'}
        `}>
          <div className="p-6 hidden lg:flex flex-shrink-0">
            <Link href="/" className="flex items-center gap-3">
              <div className="p-2 bg-blue-50 dark:bg-blue-900/30 rounded-xl text-blue-600 dark:text-blue-400">
                <Car className="h-6 w-6" />
              </div>
              <span className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">ParkPilot</span>
            </Link>
          </div>
          <nav className="px-4 py-2 space-y-1 flex-1 overflow-y-auto" style={{ paddingBottom: '112px' }}>
            {navItems.map((item) => {
              if (item.kind === "link") {
                const active = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setSidebarOpen(false)}
                    className="block w-full"
                  >
                    <Button
                      variant="ghost"
                      className={`
                        w-full min-h-[44px] h-[44px] flex flex-row items-center justify-start gap-3 px-3 py-0
                        whitespace-nowrap overflow-hidden
                        ${active 
                          ? "bg-blue-600 hover:bg-blue-700 text-white font-medium shadow-xs" 
                          : "text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800"}
                        rounded-xl transition-all duration-150
                      `}
                    >
                      <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center">
                        {item.icon}
                      </span>
                      <span className="text-sm font-medium truncate flex-1 min-w-0 text-left">
                        {item.name}
                      </span>
                    </Button>
                  </Link>
                );
              }

              const open = !!groupsOpen[item.name];
              const childActive = isChildActive(item);
              return (
                <div key={item.name} className="space-y-1">
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => toggleGroup(item.name)}
                    className={`
                      w-full min-h-[44px] h-[44px] flex flex-row items-center justify-between gap-3 px-3 py-0
                      whitespace-nowrap overflow-hidden
                      rounded-xl transition-all duration-150
                      ${childActive
                        ? "bg-blue-50 text-blue-700 dark:bg-blue-600/20 dark:text-blue-300 hover:bg-blue-100/70 dark:hover:bg-blue-600/30 border border-blue-200 dark:border-blue-500/30 font-medium"
                        : "text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800"
                      }
                    `}
                  >
                    <div className="flex flex-row items-center gap-3 min-w-0 flex-1">
                      <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center">
                        {item.icon}
                      </span>
                      <span className="text-sm font-semibold truncate min-w-0 text-left">
                        {item.name}
                      </span>
                    </div>
                    <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center">
                      {open ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                    </span>
                  </Button>

                  <div
                    className={`
                      overflow-hidden transition-all duration-300 ease-in-out
                      ${open ? "max-h-[600px] opacity-100" : "max-h-0 opacity-0"}
                    `}
                  >
                    <div className="ml-4 mt-1 space-y-1 border-l-2 border-slate-200 dark:border-slate-700 pl-3">
                      {item.children.map((child) => {
                        const active = pathname === child.href;
                        return (
                          <Link
                            key={child.href}
                            href={child.href}
                            onClick={() => setSidebarOpen(false)}
                            className="block w-full"
                          >
                            <Button
                              variant="ghost"
                              className={`
                                w-full min-h-[40px] h-[40px] flex flex-row items-center justify-start gap-3 px-3 py-0
                                whitespace-nowrap overflow-hidden text-sm
                                rounded-lg transition-all duration-150
                                ${active
                                  ? "bg-blue-600 hover:bg-blue-700 text-white font-medium shadow-xs"
                                  : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800/70"
                                }
                              `}
                            >
                              <span className={`flex-shrink-0 w-4 h-4 flex items-center justify-center ${active ? "text-white" : "text-blue-500 dark:text-blue-400"}`}>
                                {child.icon}
                              </span>
                              <span className="font-medium truncate flex-1 min-w-0 text-left">
                                {child.name}
                              </span>
                            </Button>
                          </Link>
                        );
                      })}
                    </div>
                  </div>
                </div>
              );
            })}
          </nav>

          {/* Profile Section in Sidebar */}
          <div className="border-t border-slate-200 dark:border-slate-800 w-full bg-white dark:bg-slate-900 absolute bottom-0 left-0 right-0 z-10 transition-colors">
            <div className="p-4 space-y-2 relative">
              <button
                type="button"
                ref={profileTriggerRef as React.RefObject<HTMLButtonElement>}
                onClick={() => setProfileOpen(!profileOpen)}
                className="w-full flex items-center gap-3 p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-left"
              >
                <div className="h-11 w-11 rounded-full bg-blue-100 dark:bg-slate-800 border border-blue-200 dark:border-slate-700 flex items-center justify-center text-blue-700 dark:text-white font-semibold text-base flex-shrink-0">
                  {getInitials()}
                </div>
                <div className="flex-1 min-w-0 text-left">
                  <p className="text-sm font-semibold text-slate-900 dark:text-white truncate">
                    {user.firstName} {user.lastName}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                    {user.isAdmin ? "Master Admin" : "User"}
                  </p>
                </div>
                <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center text-slate-400">
                  {profileOpen ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronUp className="h-4 w-4" />
                  )}
                </span>
              </button>

              {/* Profile Popup Menu matching Screenshot */}
              <div className="absolute left-0 right-0 bottom-full mb-2 px-2">
                {profileOpen && (
                  <>
                    <div
                      className="fixed inset-0 z-30 bg-transparent"
                      onClick={() => setProfileOpen(false)}
                    />
                    <div
                      ref={profilePopupRef as React.RefObject<HTMLDivElement>}
                      className="relative z-40"
                    >
                      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-2xl overflow-hidden transition-all">
                        {/* User Header */}
                        <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
                          <p className="text-sm font-semibold text-slate-900 dark:text-white truncate">
                            {user.firstName} {user.lastName}
                          </p>
                          <p className="text-xs text-slate-500 dark:text-slate-400 truncate mt-0.5">
                            {user.email || `${user.firstName.toLowerCase()}@parkpilot.com`}
                          </p>
                        </div>

                        {/* Menu Options */}
                        <div className="p-1.5 space-y-0.5">
                          <Link
                            href="/dashboard/settings"
                            onClick={() => { setSidebarOpen(false); setProfileOpen(false); }}
                            className="block w-full"
                          >
                            <div className="w-full min-h-[40px] h-[40px] flex flex-row items-center justify-start gap-3 px-3 text-slate-700 dark:text-slate-200 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors">
                              <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center text-slate-500 dark:text-slate-400">
                                <Settings className="h-4 w-4" />
                              </span>
                              <span className="text-sm font-medium truncate flex-1 text-left">
                                Settings
                              </span>
                            </div>
                          </Link>

                          {/* Single Theme Toggle Button */}
                          <button
                            type="button"
                            onClick={() => { toggleTheme(); }}
                            className="w-full min-h-[40px] h-[40px] flex flex-row items-center justify-start gap-3 px-3 rounded-xl transition-colors cursor-pointer text-slate-700 dark:text-slate-200 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 font-medium"
                          >
                            <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center">
                              {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                            </span>
                            <span className="text-sm truncate text-left flex-1">
                              {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
                            </span>
                          </button>
                        </div>

                        {/* Logout Option */}
                        <div className="border-t border-slate-100 dark:border-slate-800 p-1.5">
                          <button
                            type="button"
                            onClick={() => { setProfileOpen(false); logout(); }}
                            className="w-full min-h-[40px] h-[40px] flex flex-row items-center justify-start gap-3 px-3 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-xl transition-colors"
                          >
                            <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center">
                              <LogOut className="h-4 w-4" />
                            </span>
                            <span className="text-sm font-medium truncate flex-1 text-left">
                              Logout
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
          <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-6 hidden lg:flex transition-colors">
            <div className="flex items-center gap-3">
              <Button variant="ghost" size="sm" onClick={() => setSidebarOpen(!sidebarOpen)} className="text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800">
                <Menu className="h-5 w-5" />
              </Button>
              <span className="text-sm font-medium text-slate-500 dark:text-slate-400 capitalize">
                {pathname === "/dashboard" ? "Home" : pathname.replace("/dashboard/", "").replace("-", " ")}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <Link href="/dashboard/notifications" className="relative">
                <Button variant="ghost" size="sm" className="text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800">
                  <Bell className="h-5 w-5" />
                </Button>
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
              </Link>
            </div>
          </header>

          <main className="flex-1 overflow-auto p-4 lg:p-6 bg-slate-50 dark:bg-slate-950 transition-colors">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
