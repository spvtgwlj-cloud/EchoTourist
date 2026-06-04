'use client';

import { create } from 'zustand';
import { api } from '@/lib/api';
import type { User, AuthResponse } from '@/lib/types';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  googleLogin: (credential: string) => Promise<void>;
  logout: () => void;
  loadFromStorage: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: false,

  login: async (email: string, password: string) => {
    set({ isLoading: true });
    try {
      const res = await api.post<AuthResponse>('/auth/login', { email, password });
      localStorage.setItem('auth_token', res.access_token);
      set({ user: res.user, token: res.access_token, isAuthenticated: true });
    } finally {
      set({ isLoading: false });
    }
  },

  register: async (email: string, password: string, name: string) => {
    set({ isLoading: true });
    try {
      const res = await api.post<AuthResponse>('/auth/register', { email, password, name });
      localStorage.setItem('auth_token', res.access_token);
      set({ user: res.user, token: res.access_token, isAuthenticated: true });
    } finally {
      set({ isLoading: false });
    }
  },

  googleLogin: async (credential: string) => {
    set({ isLoading: true });
    try {
      const res = await api.post<AuthResponse>('/auth/google', { credential });
      localStorage.setItem('auth_token', res.access_token);
      set({ user: res.user, token: res.access_token, isAuthenticated: true });
    } finally {
      set({ isLoading: false });
    }
  },

  logout: () => {
    localStorage.removeItem('auth_token');
    set({ user: null, token: null, isAuthenticated: false });
  },

  loadFromStorage: () => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      // Fetch user info on page load
      api.get<User>('/auth/me')
        .then((user) => set({ user, token, isAuthenticated: true }))
        .catch(() => {
          localStorage.removeItem('auth_token');
          set({ user: null, token: null, isAuthenticated: false });
        });
    }
  },
}));
