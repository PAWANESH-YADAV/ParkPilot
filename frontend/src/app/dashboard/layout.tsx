"use client";

import { useState, useEffect } from "react";
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
  QrCode,
  TrendingUp,
  Mic,
  ChevronDown,
  ChevronRight,
  SlidersHorizontal,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";

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
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [groupsOpen, setGroupsOpen] = useState<Record<string, boolean>>({
    "System Configuration": true,
  });

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
      kind: "link",
      name: "Notification Management",
      href: "/dashboard/notifications",
      icon: <Bell className="h-5 w-5" />,
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
          name: "5. QR Code System",
          href: "/dashboard/qr-system",
          icon: <QrCode className="h-4 w-4" />,
        },
        {
          name: "6. Dynamic Pricing",
          href: "/dashboard/dynamic-pricing",
          icon: <TrendingUp className="h-4 w-4" />,
        },
      ],
    },
    {
      kind: "link",
      name: "General Settings",
      href: "/dashboard/config",
      icon: <SlidersHorizontal className="h-5 w-5" />,
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
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
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
        <div className="w-8" /> {/* Spacer */}
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
        <aside className={`
          fixed lg:static inset-y-0 left-0 z-50
          bg-slate-900 border-r border-slate-800
          transition-all duration-300 ease-in-out
          w-72
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0 lg:w-64'}
        `}>
          <div className="p-6 hidden lg:flex">
            <Link href="/" className="flex items-center gap-3">
              <Car className="h-8 w-8 text-blue-500" />
              <span className="text-xl font-bold text-white">ParkPilot</span>
            </Link>
          </div>
          <nav className="px-4 py-2 space-y-1 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 180px)' }}>
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
                      variant={active ? "default" : "ghost"}
                      className={`
                        w-full min-h-[44px] h-[44px] flex flex-row items-center justify-start gap-3 px-3 py-0
                        whitespace-nowrap overflow-hidden
                        ${active ? "bg-blue-600 hover:bg-blue-700 text-white" : "text-slate-300 hover:text-white hover:bg-slate-800"}
                        rounded-lg transition-all duration-200
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
                      rounded-lg transition-all duration-200
                      ${childActive
                        ? "bg-blue-600/20 text-blue-300 hover:bg-blue-600/30 border border-blue-500/30"
                        : "text-slate-300 hover:text-white hover:bg-slate-800"
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
                    <div className="ml-4 mt-1 space-y-1 border-l-2 border-slate-700 pl-3">
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
                              variant={active ? "default" : "ghost"}
                              className={`
                                w-full min-h-[40px] h-[40px] flex flex-row items-center justify-start gap-3 px-3 py-0
                                whitespace-nowrap overflow-hidden text-sm
                                rounded-lg transition-all duration-200
                                ${active
                                  ? "bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-600/20"
                                  : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/70"
                                }
                              `}
                            >
                              <span className={`flex-shrink-0 w-4 h-4 flex items-center justify-center ${active ? "text-white" : "text-blue-400"}`}>
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
          <div className="p-4 border-t border-slate-800 mt-auto">
            <Button
              variant="ghost"
              onClick={() => logout()}
              className="w-full min-h-[44px] h-[44px] flex flex-row items-center justify-start gap-3 px-3 py-0 whitespace-nowrap overflow-hidden text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg"
            >
              <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center">
                <LogOut className="h-5 w-5" />
              </span>
              <span className="text-sm font-medium truncate flex-1 min-w-0 text-left">
                Logout
              </span>
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
              <div className="text-right">
                <p className="text-sm font-medium text-white">{user.firstName} {user.lastName}</p>
                <p className="text-xs text-slate-500">Administrator</p>
              </div>
              <div className="h-10 w-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-semibold">
                {getInitials()}
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
