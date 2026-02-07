import { create } from 'zustand';
import type { TabType, Toast } from '../types';
import * as api from '../api/api';

interface UiState {
  activeTab: TabType;
  isConnected: boolean;
  showMobileSidebar: boolean;
  toasts: Toast[];

  setActiveTab: (t: TabType) => void;
  setConnected: (b: boolean) => void;
  toggleMobileSidebar: () => void;
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  checkHealth: () => Promise<void>;
}

let toastCounter = 0;

export const useUiStore = create<UiState>((set, get) => ({
  activeTab: 'distribution',
  isConnected: false,
  showMobileSidebar: false,
  toasts: [],

  setActiveTab: t => set({ activeTab: t }),
  setConnected: b => set({ isConnected: b }),
  toggleMobileSidebar: () => set(s => ({ showMobileSidebar: !s.showMobileSidebar })),

  addToast: toast => {
    const id = String(++toastCounter);
    const newToast: Toast = { id, duration: 5000, ...toast };
    set(s => ({ toasts: [...s.toasts, newToast] }));
    setTimeout(() => get().removeToast(id), newToast.duration);
  },

  removeToast: id => set(s => ({ toasts: s.toasts.filter(t => t.id !== id) })),

  checkHealth: async () => {
    try {
      const health = await api.checkHealth();
      set({ isConnected: health.status === 'healthy' });
    } catch {
      set({ isConnected: false });
    }
  },
}));