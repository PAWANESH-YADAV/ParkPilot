"use client"

import { useEffect, useRef } from "react"

declare global {
  interface Window {
    google: any
  }
}

export default function ParkingMap() {
  const mapRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!window.google || !mapRef.current) return

    const map = new window.google.maps.Map(mapRef.current, {
      center: { lat: 40.7128, lng: -74.0060 }, // Example: NYC
      zoom: 14,
      styles: [
        {
          "elementType": "geometry",
          "stylers": [{ "color": "#242f3e" }]
        },
        {
          "elementType": "labels.text.stroke",
          "stylers": [{ "color": "#242f3e" }]
        },
        {
          "elementType": "labels.text.fill",
          "stylers": [{ "color": "#746855" }]
        },
        {
          "featureType": "administrative.locality",
          "elementType": "labels.text.fill",
          "stylers": [{ "color": "#d59563" }]
        },
        {
          "featureType": "poi",
          "elementType": "labels.text.fill",
          "stylers": [{ "color": "#d59563" }]
        },
        {
          "featureType": "poi.park",
          "elementType": "geometry",
          "stylers": [{ "color": "#263c3f" }]
        },
        {
          "featureType": "poi.park",
          "elementType": "labels.text.fill",
          "stylers": [{ "color": "#6b9a76" }]
        },
        {
          "featureType": "road",
          "elementType": "geometry",
          "stylers": [{ "color": "#38414e" }]
        },
        {
          "featureType": "road",
          "elementType": "geometry.stroke",
          "stylers": [{ "color": "#212a37" }]
        },
        {
          "featureType": "road",
          "elementType": "labels.text.fill",
          "stylers": [{ "color": "#9ca5b3" }]
        },
        {
          "featureType": "road.highway",
          "elementType": "geometry",
          "stylers": [{ "color": "#746855" }]
        },
        {
          "featureType": "road.highway",
          "elementType": "geometry.stroke",
          "stylers": [{ "color": "#1f2835" }]
        },
        {
          "featureType": "transit",
          "elementType": "labels.text.fill",
          "stylers": [{ "color": "#9ca5b3" }]
        },
        {
          "featureType": "water",
          "elementType": "geometry",
          "stylers": [{ "color": "#17263c" }]
        }
      ]
    })

    // Example parking lot markers
    const parkingLots = [
      { lat: 40.7128, lng: -74.0060, name: "Downtown Garage", available: 45, total: 150 },
      { lat: 40.7228, lng: -73.9960, name: "City Center Parking", available: 23, total: 100 },
      { lat: 40.7028, lng: -74.0160, name: "Waterfront Parking", available: 67, total: 200 },
    ]

    parkingLots.forEach((lot) => {
      new window.google.maps.Marker({
        position: { lat: lot.lat, lng: lot.lng },
        map: map,
        title: lot.name,
        icon: {
          path: window.google.maps.SymbolPath.CIRCLE,
          scale: 10,
          fillColor: lot.available > 30 ? "#10b981" : lot.available > 10 ? "#f59e0b" : "#ef4444",
          fillOpacity: 0.8,
          strokeWeight: 2,
          strokeColor: "#fff"
        }
      })
    })
  }, [])

  return (
    <div ref={mapRef} className="w-full h-96 rounded-lg overflow-hidden border border-slate-700" />
  )
}
