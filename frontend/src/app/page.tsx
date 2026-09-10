'use client';

import { useEffect } from 'react';
import Link from "next/link";
import { useRouter } from 'next/navigation';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Car, Zap, MapPin, TrendingUp, Shield, Camera, Database, DollarSign } from "lucide-react";
import { motion } from "framer-motion";
import { useAuth } from '@/lib/auth-context';

export default function Home() {
  const router = useRouter();
  const { user, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && user) {
      if (user.isAdmin) {
        router.push('/dashboard');
      } else {
        router.push('/user');
      }
    }
  }, [user, isLoading, router]);

  const features = [
    {
      icon: <Car className="h-8 w-8 text-blue-500" />,
      title: "Vehicle Detection",
      description: "AI-powered vehicle detection using YOLOv8 for real-time monitoring"
    },
    {
      icon: <Camera className="h-8 w-8 text-cyan-500" />,
      title: "ANPR System",
      description: "Automatic Number Plate Recognition for entry/exit management"
    },
    {
      icon: <Zap className="h-8 w-8 text-yellow-500" />,
      title: "IoT Sensors",
      description: "Real-time parking slot occupancy detection with IoT integration"
    },
    {
      icon: <TrendingUp className="h-8 w-8 text-green-500" />,
      title: "AI Analytics",
      description: "Predictive parking demand and dynamic pricing using ML"
    },
    {
      icon: <MapPin className="h-8 w-8 text-purple-500" />,
      title: "Smart Parking Maps",
      description: "Interactive maps showing real-time parking availability"
    },
    {
      icon: <Shield className="h-8 w-8 text-red-500" />,
      title: "Security & Monitoring",
      description: "CCTV integration and 24/7 surveillance of parking areas"
    },
  ];

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
      <nav className="fixed top-0 left-0 right-0 bg-slate-900/80 backdrop-blur-md border-b border-slate-800 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <Car className="h-8 w-8 text-blue-500" />
              <span className="text-xl font-bold text-white">ParkPilot</span>
            </div>
            <div className="hidden md:flex items-center gap-6">
              <Link href="#features" className="text-slate-300 hover:text-white transition">Features</Link>
              <Link href="/dashboard" className="text-slate-300 hover:text-white transition">Admin Dashboard</Link>
            </div>
            <div className="flex items-center gap-4">
              <Link href="/login">
                <Button variant="ghost" className="text-white">Sign In</Button>
              </Link>
              <Link href="/register">
                <Button className="bg-blue-600 hover:bg-blue-700">Get Started</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <section className="pt-32 pb-20 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 rounded-full border border-slate-700 mb-8">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-sm text-slate-300">Autonomous Parking System</span>
            </div>
            <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
              Smart Parking with
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-cyan-500">
                {" "}AI & IoT
              </span>
            </h1>
            <p className="text-xl text-slate-400 mb-10 max-w-3xl mx-auto">
              Revolutionize parking management with real-time vehicle detection, ANPR, 
              smart sensors, and AI-powered analytics for optimized parking experiences.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/register">
                <Button size="lg" className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 text-lg px-8">
                  Get Started - Free
                </Button>
              </Link>
              <Link href="#features">
                <Button size="lg" variant="outline" className="w-full sm:w-auto text-lg px-8 border-slate-700 hover:bg-slate-800">
                  Learn More
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      <section id="features" className="py-20 px-4 bg-slate-900/50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4">Features</h2>
            <p className="text-slate-400 max-w-2xl mx-auto">
              Comprehensive parking solution powered by cutting-edge technology
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <Card className="bg-slate-800/50 border-slate-700 hover:border-slate-600 transition-all hover:shadow-lg hover:shadow-blue-500/10">
                  <CardHeader>
                    <div className="mb-4">{feature.icon}</div>
                    <CardTitle className="text-white text-xl">{feature.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-slate-400">{feature.description}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-3 gap-8 text-center">
            {[
              { icon: <Database className="h-10 w-10 mx-auto text-blue-500" />, number: "500+", label: "Parking Slots" },
              { icon: <DollarSign className="h-10 w-10 mx-auto text-green-500" />, number: "30%", label: "Cost Reduction" },
              { icon: <Car className="h-10 w-10 mx-auto text-cyan-500" />, number: "24/7", label: "Autonomous" }
            ].map((stat, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.15 }}
                viewport={{ once: true }}
              >
                <Card className="bg-slate-800/30 border-slate-700 p-8">
                  {stat.icon}
                  <div className="text-5xl font-bold text-white my-4">{stat.number}</div>
                  <p className="text-slate-400">{stat.label}</p>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <footer className="py-12 px-4 border-t border-slate-800">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Car className="h-6 w-6 text-blue-500" />
              <span className="font-semibold text-white">ParkPilot</span>
            </div>
            <p className="text-slate-500 text-sm">
              © 2024 ParkPilot. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
