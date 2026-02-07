import { useEffect } from 'react';
import { X, CheckCircle, AlertTriangle, AlertCircle, Info } from 'lucide-react';
import { useUiStore } from '../stores/uiStore';
import type { Toast } from '../types';

const TOAST_ICONS: Record<Toast['type'], React.FC<{ size?: number }>> = {
  success: CheckCircle,
  error: AlertCircle,
  warning: AlertTriangle,
  info: Info,
};

const TOAST_STYLES: Record<Toast['type'], string> = {
  success: 'border-accent-green/40 bg-accent-green/10 text-accent-green',
  error: 'border-accent-coral/40 bg-accent-coral/10 text-accent-coral',
  warning: 'border-accent-gold/40 bg-accent-gold/10 text-accent-gold',
  info: 'border-accent-blue/40 bg-accent-blue/10 text-accent-blue',
};

function ToastItem({ toast }: { toast: Toast }) {
  const { removeToast } = useUiStore();
  const Icon = TOAST_ICONS[toast.type];

  return (
    <div
      className={`animate-slide-in flex items-start gap-3 rounded-lg border px-4 py-3 shadow-lg backdrop-blur-sm ${TOAST_STYLES[toast.type]}`}
    >
      <Icon size={18} className="mt-0.5 shrink-0" />
      <p className="flex-1 text-sm font-medium text-text-primary">{toast.message}</p>
      <button
        onClick={() => removeToast(toast.id)}
        className="shrink-0 rounded p-0.5 transition-colors hover:bg-white/10"
      >
        <X size={14} />
      </button>
    </div>
  );
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const { toasts } = useUiStore();

  return (
    <>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex w-80 flex-col gap-2">
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} />
        ))}
      </div>
    </>
  );
}
