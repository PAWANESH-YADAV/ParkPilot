'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  MapPin,
  Star,
  Heart,
  Navigation,
  Clock
} from 'lucide-react';

export default function FavoritesPage() {
  const [favorites, setFavorites] = useState([
    {
      id: '1',
      name: 'Downtown Garage',
      address: '123 Main St, Downtown',
      rating: 4.8,
      price: '$15/hr',
      distance: '0.5 km',
    },
    {
      id: '2',
      name: 'Waterfront Parking',
      address: '789 River Rd, Waterfront',
      rating: 4.6,
      price: '$10/hr',
      distance: '2.0 km',
    },
  ]);

  const removeFavorite = (id: string) => {
    setFavorites(prev => prev.filter(f => f.id !== id));
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Favorite Locations</h1>
        <p className="text-slate-400">Your saved parking spots</p>
      </div>

      {favorites.length === 0 ? (
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-12 text-center">
            <Heart className="h-16 w-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">No favorites yet</h3>
            <p className="text-slate-400 mb-4">Start adding your favorite parking locations!</p>
            <Button className="bg-blue-600">Find Parking</Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 gap-6">
          {favorites.map((lot) => (
            <Card key={lot.id} className="bg-slate-800 border-slate-700">
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-xl text-white">{lot.name}</CardTitle>
                    <p className="text-slate-400 text-sm flex items-center gap-1">
                      <MapPin className="h-4 w-4" />
                      {lot.address}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeFavorite(lot.id)}
                    className="text-red-500"
                  >
                    <Heart className="h-5 w-5" fill="currentColor" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1 text-yellow-400">
                    <Star className="h-4 w-4" fill="currentColor" />
                    <span className="text-white font-medium">{lot.rating}</span>
                  </div>
                  <span className="text-xl font-bold text-white">{lot.price}</span>
                </div>
                <div className="flex gap-2 pt-2 border-t border-slate-700">
                  <Button variant="outline" className="flex-1 border-slate-600 text-slate-300">
                    <Navigation className="h-4 w-4 mr-2" />
                    Navigate
                  </Button>
                  <Button className="flex-1 bg-blue-600">
                    Book Now
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
