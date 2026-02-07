import { BarChart3, PieChart, TrendingDown, Table } from 'lucide-react';
import { useUiStore } from '../stores/uiStore';
import { TABS } from '../utils/constants';
import type { TabType } from '../types';

const ICON_MAP: Record<string, React.FC<{ size?: number; className?: string }>> = {
  BarChart3,
  PieChart,
  TrendingDown,
  Table,
};

export function TabNavigation() {
  const { activeTab, setActiveTab } = useUiStore();

  return (
    <nav className="flex border-b border-border-base bg-bg-secondary px-4 lg:px-6">
      {TABS.map((tab) => {
        const Icon = ICON_MAP[tab.icon];
        const isActive = activeTab === tab.key;

        return (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors relative
              ${
                isActive
                  ? 'text-accent-teal'
                  : 'text-text-muted hover:text-text-secondary'
              }`}
          >
            {Icon && <Icon size={16} />}
            <span className="hidden sm:inline">{tab.label}</span>
            {isActive && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent-teal rounded-full" />
            )}
          </button>
        );
      })}
    </nav>
  );
}
