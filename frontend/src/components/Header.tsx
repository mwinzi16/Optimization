import { Menu, Wifi, WifiOff, Database } from 'lucide-react';
import { useUiStore } from '../stores/uiStore';
import { useDataStore } from '../stores/dataStore';

export function Header() {
  const { isConnected, toggleMobileSidebar } = useUiStore();
  const { assetCount, scenarioCount, dataSource } = useDataStore();

  return (
    <header className="flex items-center justify-between border-b border-border-base bg-bg-secondary px-4 py-3 lg:px-6">
      <div className="flex items-center gap-3">
        <button
          onClick={toggleMobileSidebar}
          className="rounded-lg p-2 text-text-secondary hover:bg-bg-elevated hover:text-text-primary lg:hidden"
        >
          <Menu size={20} />
        </button>
        <h1 className="text-lg font-bold tracking-tight text-text-primary">
          Portfolio Optimizer
        </h1>
      </div>

      <div className="flex items-center gap-4">
        {assetCount > 0 && (
          <div className="hidden items-center gap-2 rounded-lg bg-bg-elevated px-3 py-1.5 text-xs text-text-secondary sm:flex">
            <Database size={14} />
            <span>
              {assetCount} assets · {scenarioCount > 0 ? `${scenarioCount} scenarios` : 'sample'}
            </span>
            {dataSource !== 'sample' && (
              <span className="ml-1 rounded bg-accent-teal/20 px-1.5 py-0.5 text-accent-teal">
                {dataSource}
              </span>
            )}
          </div>
        )}

        <div className="flex items-center gap-2">
          {isConnected ? (
            <>
              <span className="h-2 w-2 rounded-full bg-accent-green animate-pulse-glow" />
              <Wifi size={16} className="text-accent-green" />
              <span className="hidden text-xs text-accent-green sm:inline">Connected</span>
            </>
          ) : (
            <>
              <span className="h-2 w-2 rounded-full bg-accent-coral" />
              <WifiOff size={16} className="text-accent-coral" />
              <span className="hidden text-xs text-accent-coral sm:inline">Disconnected</span>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
