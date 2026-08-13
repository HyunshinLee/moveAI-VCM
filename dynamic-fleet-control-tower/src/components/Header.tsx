import React from 'react';

interface HeaderProps {
  searchQuery: string;
  onSearchChange: (q: string) => void;
  unreadAlertsCount: number;
  onToggleNotifications: () => void;
  onRefreshData: () => void;
  onSimulateDisruption: () => void;
  isDisruptionActive: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  searchQuery,
  onSearchChange,
  unreadAlertsCount,
  onToggleNotifications,
  onRefreshData,
  onSimulateDisruption,
  isDisruptionActive,
}) => {
  return (
    <header className="flex justify-between items-center w-[calc(100%-260px)] left-[260px] px-6 bg-[#051424]/80 backdrop-blur-md border-b border-[#424754]/30 fixed top-0 h-16 z-40">
      {/* Search Bar on Left */}
      <div className="flex items-center gap-4 flex-1">
        <div className="relative w-full max-w-md">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[#c2c6d6] text-[20px]">
            search
          </span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search fleet, routes, or incidents..."
            className="w-full bg-[#1c2b3c] border border-[#424754]/40 rounded-full py-1.5 pl-10 pr-4 text-xs text-[#d4e4fa] focus:outline-none focus:ring-2 focus:ring-[#4d8eff]/50 placeholder-[#8c909f]"
          />
        </div>
      </div>

      {/* Product Name (Center) */}
      <div className="absolute left-1/2 -translate-x-1/2 flex items-center gap-2">
        <span className="text-base font-bold text-[#d4e4fa] tracking-wide">
          Dynamic Fleet Control
        </span>
      </div>

      {/* Trailing Actions & Profile */}
      <div className="flex items-center gap-4">
        {/* Quick Demo Trigger for Hackathon / Evaluation */}
        <button
          onClick={onSimulateDisruption}
          className={`px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 transition-all shadow-sm ${
            isDisruptionActive
              ? 'bg-[#93000a] text-[#ffdad6] border border-[#ffb4ab]/50 animate-pulse'
              : 'bg-[#ca8100]/20 text-[#ffb95f] border border-[#ca8100]/40 hover:bg-[#ca8100]/30'
          }`}
          title="Simulate or Reset Traffic Disruption for Demo"
        >
          <span className="material-symbols-outlined text-sm">
            {isDisruptionActive ? 'warning' : 'bolt'}
          </span>
          {isDisruptionActive ? '돌발상황 진행 중 (리셋)' : '돌발상황 발생 시뮬레이션'}
        </button>

        <div className="flex items-center gap-2 bg-[#122131] px-2.5 py-1 rounded-full border border-[#424754]/30">
          <div className="w-2 h-2 rounded-full bg-[#4edea3] animate-pulse"></div>
          <span className="text-xs text-[#c2c6d6]">Connected</span>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={onRefreshData}
            title="Refresh Fleet Telemetry"
            className="p-1.5 text-[#c2c6d6] hover:text-[#adc6ff] hover:bg-[#1c2b3c] rounded-lg transition-colors"
          >
            <span className="material-symbols-outlined text-[20px]">sync</span>
          </button>

          <button
            onClick={onToggleNotifications}
            title="Notifications"
            className="p-1.5 text-[#c2c6d6] hover:text-[#adc6ff] hover:bg-[#1c2b3c] rounded-lg transition-colors relative"
          >
            <span className="material-symbols-outlined text-[20px]">notifications</span>
            {unreadAlertsCount > 0 && (
              <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-[#ffb4ab] rounded-full border border-[#051424] animate-ping" />
            )}
            {unreadAlertsCount > 0 && (
              <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-[#ffb4ab] rounded-full border border-[#051424]" />
            )}
          </button>
        </div>

        <div className="w-8 h-8 rounded-full border border-[#424754]/50 overflow-hidden bg-[#273647] flex items-center justify-center shrink-0 shadow-sm">
          <span className="material-symbols-outlined text-[#adc6ff] text-base">
            admin_panel_settings
          </span>
        </div>
      </div>
    </header>
  );
};
