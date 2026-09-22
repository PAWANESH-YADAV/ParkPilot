'use client';

import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';

const TOKEN_KEY = 'parkpilot_token';

export const getToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
};

export const setToken = (token: string | null) => {
  if (typeof window === 'undefined') return;
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
};

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      setToken(null);
      if (typeof window !== 'undefined') {
        const path = window.location.pathname;
        if (!['/login', '/register'].includes(path)) {
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export interface ApiError {
  detail: string;
}

export const isNetworkError = (error: unknown): boolean => {
  if (axios.isAxiosError(error)) {
    const err = error as AxiosError;
    return !err.response && !!err.message && err.message.toLowerCase().includes('network');
  }
  return false;
};

export const extractError = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const err = error as AxiosError<ApiError>;
    if (err.response?.data?.detail) {
      return err.response.data.detail;
    }
    if (!err.response) {
      return (
        'Backend server nahi chal raha hai. Ya to start nahi hua hai ya firewall/CORS issue hai. ' +
        'Dobara register karne par Demo Mode (local storage) try kiya jayega.'
      );
    }
    if (err.message) {
      return err.message;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'Something went wrong';
};

export interface BackendUser {
  id: number;
  email: string;
  full_name?: string;
  role: 'driver' | 'admin' | 'municipality' | 'provider' | 'billing' | 'data_scientist';
  is_active: boolean;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: BackendUser;
}

export interface LogoutResponse {
  success: boolean;
  message: string;
  user?: string;
}

export const authApi = {
  login: (email: string, password: string) =>
    api.post<LoginResponse>('/auth/login', { email, password }).then((r) => r.data),
  register: (payload: { email: string; full_name: string; password: string }) =>
    api.post<BackendUser>('/auth/register', payload).then((r) => r.data),
  me: () => api.get<BackendUser>('/auth/me').then((r) => r.data),
  logout: () =>
    api
      .post<LogoutResponse>('/auth/logout')
      .then((r) => r.data)
      .catch(() => ({ success: true, message: 'Local cleanup completed' })),
  getUsers: () => api.get<BackendUser[]>('/auth/users').then((r) => r.data),
  createUser: (payload: {
    email: string;
    full_name: string;
    password: string;
    role?: string;
    is_active?: boolean;
  }) => api.post<BackendUser>('/auth/users', payload).then((r) => r.data),
  updateUser: (
    id: number,
    payload: Partial<{ full_name: string; email: string; role: string; is_active: boolean }>
  ) => api.patch<BackendUser>(`/auth/users/${id}`, payload).then((r) => r.data),
  deleteUser: (id: number) =>
    api.delete<{ success: boolean; message: string }>(`/auth/users/${id}`).then((r) => r.data),
};

export interface ParkingLot {
  id: number;
  name: string;
  address?: string;
  latitude?: number;
  longitude?: number;
  total_slots: number;
  price_per_hour: number;
  vehicle_types?: string[];
  features?: string[];
  rating?: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  available_slots: number;
  distance?: string;
}

export const parkingApi = {
  getLots: (params?: {
    search?: string;
    vehicle_type?: string;
    lat?: number;
    lon?: number;
  }) =>
    api.get<ParkingLot[]>('/parkinglots', { params }).then((r) => r.data),
  getAvailableSlot: (lotId: number) =>
    api
      .get<{ slot_id: number | null; slot_number: string | null }>(
        `/parkinglots/${lotId}/available_slot`
      )
      .then((r) => r.data),
};

export interface Vehicle {
  id: number;
  user_id: number;
  license_plate: string;
  make?: string;
  model?: string;
  year?: number;
  color?: string;
  created_at: string;
}

export const vehiclesApi = {
  list: () => api.get<Vehicle[]>('/vehicles').then((r) => r.data),
  create: (payload: {
    license_plate: string;
    make?: string;
    model?: string;
    year?: number;
    color?: string;
  }) => api.post<Vehicle>('/vehicles', payload).then((r) => r.data),
  delete: (id: number) => api.delete(`/vehicles/${id}`).then((r) => r.data),
};

export type ReservationStatus =
  | 'pending'
  | 'confirmed'
  | 'active'
  | 'completed'
  | 'cancelled';

export interface Reservation {
  id: number;
  user_id: number;
  slot_id: number;
  vehicle_id?: number;
  start_time: string;
  end_time: string;
  status: ReservationStatus;
  amount: number;
  license_plate?: string;
  vehicle_type?: 'car' | 'bike' | 'suv';
  payment_method?: 'card' | 'upi' | 'wallet';
  is_active: boolean;
  created_at: string;
  parking_lot_id?: number;
  parking_lot_name?: string;
  slot_number?: string;
}

export const reservationsApi = {
  book: (payload: {
    parking_lot_id: number;
    start_time: string;
    end_time: string;
    license_plate?: string;
    vehicle_type?: 'car' | 'bike' | 'suv';
    payment_method?: 'card' | 'upi' | 'wallet';
    vehicle_id?: number;
    amount?: number;
  }) => api.post<Reservation>('/reservations/book', payload).then((r) => r.data),
  list: (statusFilter?: ReservationStatus) =>
    api
      .get<Reservation[]>('/reservations', {
        params: statusFilter ? { status_filter: statusFilter } : undefined,
      })
      .then((r) => r.data),
  get: (id: number) => api.get<Reservation>(`/reservations/${id}`).then((r) => r.data),
  updateStatus: (id: number, status: ReservationStatus) =>
    api
      .patch<Reservation>(`/reservations/${id}`, { status })
      .then((r) => r.data),
  extend: (id: number, hours: number) =>
    api
      .post<Reservation>(`/reservations/${id}/extend`, { hours })
      .then((r) => r.data),
  cancel: (id: number) =>
    api.delete<Reservation>(`/reservations/${id}`).then((r) => r.data),
};
