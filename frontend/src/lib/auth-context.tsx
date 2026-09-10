'use client';

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
  useCallback,
} from 'react';
import {
  authApi,
  setToken,
  getToken,
  BackendUser,
  extractError,
  isNetworkError,
} from '@/lib/api';

interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  fullName: string;
  phone: string;
  isAdmin: boolean;
  role: string;
  backendId: number;
}

interface AuthContextType {
  user: User | null;
  login: (
    email: string,
    password: string
  ) => Promise<{ success: boolean; isAdmin: boolean; error?: string }>;
  register: (userData: {
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
    password: string;
  }) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  isLoading: boolean;
  refreshUser: () => Promise<void>;
}

const ADMIN_EMAIL = 'Admin9936@gmail.com';
const ADMIN_PASSWORD = '9936313819';

const USER_KEY = 'parkpilot_user';
const DEMO_USERS_KEY = 'parkpilot_demo_users';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const toFrontendUser = (u: BackendUser): User => {
  const full = u.full_name || '';
  const parts = full.split(' ');
  const firstName = parts[0] || '';
  const lastName = parts.slice(1).join(' ') || '';
  const isAdmin =
    u.role === 'admin' || u.role === 'provider' || u.role === 'billing';
  return {
    id: `user-${u.id}`,
    backendId: u.id,
    email: u.email,
    firstName,
    lastName,
    fullName: full,
    phone: '',
    isAdmin,
    role: u.role,
  };
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const persistUser = (u: User | null) => {
    if (u) {
      localStorage.setItem(USER_KEY, JSON.stringify(u));
    } else {
      localStorage.removeItem(USER_KEY);
    }
  };

  const getDemoUsers = (): Array<{
    email: string;
    password: string;
    firstName: string;
    lastName: string;
    phone: string;
  }> => {
    try {
      return JSON.parse(localStorage.getItem(DEMO_USERS_KEY) || '[]');
    } catch {
      return [];
    }
  };

  const saveDemoUser = (u: {
    email: string;
    password: string;
    firstName: string;
    lastName: string;
    phone: string;
  }) => {
    const users = getDemoUsers();
    users.push(u);
    localStorage.setItem(DEMO_USERS_KEY, JSON.stringify(users));
  };

  const refreshUser = useCallback(async () => {
    const token = getToken();
    if (!token) {
      setUser(null);
      persistUser(null);
      return;
    }
    try {
      const me = await authApi.me();
      const fe = toFrontendUser(me);
      setUser(fe);
      persistUser(fe);
    } catch (err) {
      setToken(null);
      setUser(null);
      persistUser(null);
    }
  }, []);

  useEffect(() => {
    const bootstrap = async () => {
      const savedUser = localStorage.getItem(USER_KEY);
      if (savedUser) {
        try {
          setUser(JSON.parse(savedUser));
        } catch {
          // ignore
        }
      }
      if (getToken()) {
        await refreshUser();
      }
      setIsLoading(false);
    };
    bootstrap();
  }, [refreshUser]);

  const login = async (
    email: string,
    password: string
  ): Promise<{ success: boolean; isAdmin: boolean; error?: string }> => {
    setIsLoading(true);

    const adminMatch = email.toLowerCase() === ADMIN_EMAIL.toLowerCase() && password === ADMIN_PASSWORD;

    try {
      const res = await authApi.login(email.trim(), password);
      setToken(res.access_token);
      const fe = toFrontendUser(res.user);
      if (adminMatch && !fe.isAdmin) {
        fe.isAdmin = true;
        fe.role = 'admin';
      }
      setUser(fe);
      persistUser(fe);
      setIsLoading(false);
      return { success: true, isAdmin: fe.isAdmin };
    } catch (err) {
      if (isNetworkError(err) || adminMatch) {
        if (adminMatch) {
          const adminUser: User = {
            id: 'admin-1',
            backendId: 0,
            email: ADMIN_EMAIL,
            firstName: 'Admin',
            lastName: 'ParkPilot',
            fullName: 'Admin ParkPilot',
            phone: 'N/A',
            isAdmin: true,
            role: 'admin',
          };
          setToken('demo-admin-token');
          setUser(adminUser);
          persistUser(adminUser);
          setIsLoading(false);
          return { success: true, isAdmin: true };
        }

        const demoUsers = getDemoUsers();
        const found = demoUsers.find(
          (u) => u.email.toLowerCase() === email.toLowerCase() && u.password === password
        );
        if (found) {
          const demoUser: User = {
            id: `demo-${Date.now()}`,
            backendId: 0,
            email: found.email,
            firstName: found.firstName,
            lastName: found.lastName,
            fullName: `${found.firstName} ${found.lastName}`,
            phone: found.phone,
            isAdmin: false,
            role: 'driver',
          };
          setToken('demo-user-token');
          setUser(demoUser);
          persistUser(demoUser);
          setIsLoading(false);
          return { success: true, isAdmin: false };
        }
      }

      setIsLoading(false);
      const msg = extractError(err);
      return { success: false, isAdmin: false, error: msg };
    }
  };

  const register = async (userData: {
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
    password: string;
  }): Promise<{ success: boolean; error?: string }> => {
    setIsLoading(true);
    try {
      const full_name = `${userData.firstName} ${userData.lastName}`.trim();
      const created = await authApi.register({
        email: userData.email.trim(),
        full_name,
        password: userData.password,
      });

      const loginRes = await authApi.login(
        userData.email.trim(),
        userData.password
      );
      setToken(loginRes.access_token);
      const fe = toFrontendUser(loginRes.user);
      setUser(fe);
      persistUser(fe);
      setIsLoading(false);
      return { success: true };
    } catch (err) {
      if (isNetworkError(err)) {
        const demoUsers = getDemoUsers();
        if (demoUsers.some((u) => u.email.toLowerCase() === userData.email.toLowerCase())) {
          setIsLoading(false);
          return { success: false, error: 'Yeh email already registered hai (Demo Mode)' };
        }

        saveDemoUser({
          email: userData.email.trim(),
          password: userData.password,
          firstName: userData.firstName,
          lastName: userData.lastName,
          phone: userData.phone,
        });

        const demoUser: User = {
          id: `demo-${Date.now()}`,
          backendId: 0,
          email: userData.email.trim(),
          firstName: userData.firstName,
          lastName: userData.lastName,
          fullName: `${userData.firstName} ${userData.lastName}`,
          phone: userData.phone,
          isAdmin: false,
          role: 'driver',
        };
        setToken('demo-user-token');
        setUser(demoUser);
        persistUser(demoUser);
        setIsLoading(false);
        return { success: true };
      }

      setIsLoading(false);
      const msg = extractError(err);
      return { success: false, error: msg };
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    persistUser(null);
  };

  return (
    <AuthContext.Provider
      value={{ user, login, register, logout, isLoading, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
