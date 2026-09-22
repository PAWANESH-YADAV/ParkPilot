export interface SystemUser {
  id: string;
  name: string;
  email: string;
  phone: string;
  role: 'user' | 'admin';
  status: 'active' | 'inactive';
  joinDate: string;
  backendId?: number;
}

const USERS_STORAGE_KEY = 'parkpilot_registered_users';

const DEFAULT_USERS: SystemUser[] = [
  {
    id: 'usr-admin-1',
    name: 'ParkPilot Admin',
    email: 'admin@parkpilot.com',
    phone: '+91 9936313819',
    role: 'admin',
    status: 'active',
    joinDate: '2024-01-10',
  },
  {
    id: 'usr-user-1',
    name: 'Test Driver',
    email: 'user@parkpilot.com',
    phone: '+91 9876543210',
    role: 'user',
    status: 'active',
    joinDate: '2024-02-15',
  },
  {
    id: 'usr-user-2',
    name: 'John Doe',
    email: 'john@example.com',
    phone: '+1 234-567-8901',
    role: 'user',
    status: 'active',
    joinDate: '2024-03-01',
  },
  {
    id: 'usr-user-3',
    name: 'Jane Smith',
    email: 'jane@example.com',
    phone: '+1 987-654-3210',
    role: 'user',
    status: 'active',
    joinDate: '2024-03-12',
  },
];

function notifyUsersChange() {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('parkpilot_users_updated'));
  }
}

export function getStoredUsers(): SystemUser[] {
  if (typeof window === 'undefined') return DEFAULT_USERS;
  try {
    const raw = localStorage.getItem(USERS_STORAGE_KEY);
    if (!raw) {
      localStorage.setItem(USERS_STORAGE_KEY, JSON.stringify(DEFAULT_USERS));
      return DEFAULT_USERS;
    }
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed) || parsed.length === 0) {
      localStorage.setItem(USERS_STORAGE_KEY, JSON.stringify(DEFAULT_USERS));
      return DEFAULT_USERS;
    }
    return parsed;
  } catch {
    return DEFAULT_USERS;
  }
}

export function saveStoredUsers(users: SystemUser[]): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(USERS_STORAGE_KEY, JSON.stringify(users));
    notifyUsersChange();
  } catch (err) {
    console.error('Failed to save users to localStorage', err);
  }
}

export function recordUserLogin(userData: {
  name?: string;
  email: string;
  phone?: string;
  role?: string;
  backendId?: number;
}): SystemUser {
  const currentUsers = getStoredUsers();
  const normalizedEmail = userData.email.trim().toLowerCase();

  const existingIndex = currentUsers.findIndex(
    (u) => u.email.trim().toLowerCase() === normalizedEmail
  );

  const role: 'user' | 'admin' =
    userData.role === 'admin' || normalizedEmail.includes('admin') ? 'admin' : 'user';

  if (existingIndex >= 0) {
    const existing = currentUsers[existingIndex];
    const updated: SystemUser = {
      ...existing,
      name: userData.name && userData.name.trim() ? userData.name.trim() : existing.name,
      phone: userData.phone || existing.phone,
      role: existing.role || role,
      backendId: userData.backendId ?? existing.backendId,
    };
    currentUsers[existingIndex] = updated;
    saveStoredUsers(currentUsers);
    return updated;
  }

  const displayName =
    userData.name && userData.name.trim()
      ? userData.name.trim()
      : normalizedEmail.split('@')[0].replace(/[._]/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

  const newUser: SystemUser = {
    id: `usr-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
    name: displayName,
    email: userData.email.trim(),
    phone: userData.phone || '+91 9800000000',
    role,
    status: 'active',
    joinDate: new Date().toISOString().split('T')[0],
    backendId: userData.backendId,
  };

  const updated = [newUser, ...currentUsers];
  saveStoredUsers(updated);
  return newUser;
}

export function addStoredUser(user: {
  name: string;
  email: string;
  phone?: string;
  role: 'user' | 'admin';
  status?: 'active' | 'inactive';
  backendId?: number;
}): SystemUser {
  const currentUsers = getStoredUsers();
  const normalizedEmail = user.email.trim().toLowerCase();

  const existing = currentUsers.find(
    (u) => u.email.trim().toLowerCase() === normalizedEmail
  );
  if (existing) {
    return existing;
  }

  const newUser: SystemUser = {
    id: `usr-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
    name: user.name.trim(),
    email: user.email.trim(),
    phone: user.phone?.trim() || '+91 9800000000',
    role: user.role,
    status: user.status || 'active',
    joinDate: new Date().toISOString().split('T')[0],
    backendId: user.backendId,
  };

  const updated = [newUser, ...currentUsers];
  saveStoredUsers(updated);
  return newUser;
}

export function updateStoredUser(
  id: string,
  updates: Partial<Omit<SystemUser, 'id'>>
): boolean {
  const currentUsers = getStoredUsers();
  const index = currentUsers.findIndex((u) => u.id === id);
  if (index === -1) return false;

  currentUsers[index] = {
    ...currentUsers[index],
    ...updates,
  };
  saveStoredUsers(currentUsers);
  return true;
}

export function deleteStoredUser(id: string): boolean {
  const currentUsers = getStoredUsers();
  const filtered = currentUsers.filter((u) => u.id !== id);
  if (filtered.length === currentUsers.length) return false;

  saveStoredUsers(filtered);
  return true;
}
