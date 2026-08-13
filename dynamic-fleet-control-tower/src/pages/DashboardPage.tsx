import React from 'react';
import { RouteNode, FleetVehicle, IncidentAlert, FleetEfficiencyStats } from '../types';
import { InteractiveMap } from '../components/InteractiveMap';

interface DashboardPageProps {
  nodes: RouteNode[];
  vehicles: FleetVehicle[];
  activeIncident: IncidentAlert | null;
  alerts: IncidentAlert[];
  efficiencyStats: FleetEfficiencyStats;
  onOpenRerouteConsole: () => void;
  onSelectVehicle: (vehicleId: string) => void;
  selectedVehicleId: string | null;
  onNavigatePage: (page: any) => void;
  activeScenarioId: string | null;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  nodes,
  vehicles,
  activeIncident,
  alerts,
  efficiencyStats,
  onOpenRerouteConsole,
  onSelectVehicle,
  selectedVehicleId,
  onNavigatePage,
  activeScenarioId,
}) => {
  return (
    <div className="flex-1 mt-16 p-6 flex gap-6 overflow-hidden relative z-10 h-[calc(100vh-64px)]">
      {/* Center-Left: Map & KPIs */}
      <div className="flex-1 flex flex-col gap-4 overflow-hidden">
        {/* KPI Header Grid */}
        <div className="grid grid-cols-5 gap-3 shrink-0">
          {/* KPI Card 1 */}
          <div className="glass-panel p-3.5 rounded-xl flex flex-col gap-1.5 shadow-lg">
            <div className="flex justify-between items-center text-[#c2c6d6]">
              <span className="text-xs">운행 중 차량</span>
              <span className="material-symbols-outlined text-base">local_shipping</span>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-[#d4e4fa] font-mono">
                {efficiencyStats.activeTrucksCount}
              </span>
              <span className="text-[11px] font-bold text-[#4edea3] flex items-center">
                <span className="material-symbols-outlined text-xs">arrow_upward</span>{' '}
                {efficiencyStats.activeTrucksDelta}
              </span>
            </div>
            {/* Sparkline */}
            <div className="h-6 w-full mt-1 rounded bg-[#1c2b3c] relative overflow-hidden">
              <div className="absolute bottom-0 left-0 w-full h-3 bg-gradient-to-t from-[#00a572]/20 to-transparent" />
              <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 30">
                <polyline fill="none" points="0,25 20,20 40,28 60,15 80,18 100,5" stroke="#4edea3" strokeWidth="2" />
              </svg>
            </div>
          </div>

          {/* KPI Card 2 */}
          <div className="glass-panel p-3.5 rounded-xl flex flex-col gap-1.5 shadow-lg">
            <div className="flex justify-between items-center text-[#c2c6d6]">
              <span className="text-xs">총 주문 건수</span>
              <span className="material-symbols-outlined text-base">inventory_2</span>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-[#d4e4fa] font-mono">
                {efficiencyStats.totalOrdersCount.toLocaleString()}
              </span>
            </div>
            <div className="h-6 w-full mt-1 rounded bg-[#1c2b3c] relative overflow-hidden">
              <div className="absolute bottom-0 left-0 w-full h-3 bg-gradient-to-t from-[#4d8eff]/20 to-transparent" />
              <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 30">
                <polyline fill="none" points="0,20 20,15 40,22 60,10 80,12 100,2" stroke="#4d8eff" strokeWidth="2" />
              </svg>
            </div>
          </div>

          {/* KPI Card 3 */}
          <div className="glass-panel p-3.5 rounded-xl flex flex-col gap-1.5 shadow-lg border-l-4 border-l-[#ffb95f]">
            <div className="flex justify-between items-center text-[#c2c6d6]">
              <span className="text-xs">경로 위험 지수</span>
              <span className="material-symbols-outlined text-base">warning</span>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-[#ffb95f]">
                {activeIncident && !activeIncident.resolved ? 'High Risk' : efficiencyStats.routeRiskIndexLevel}
              </span>
            </div>
            <div className="h-6 w-full mt-1 flex items-center">
              <div className="w-full bg-[#1c2b3c] h-1.5 rounded-full overflow-hidden flex">
                <div className="bg-[#4edea3] h-full w-1/3" />
                <div className="bg-[#ffb95f] h-full w-1/3" />
                {activeIncident && !activeIncident.resolved && (
                  <div className="bg-[#ffb4ab] h-full w-1/3 animate-pulse" />
                )}
              </div>
            </div>
          </div>

          {/* KPI Card 4 */}
          <div className="glass-panel p-3.5 rounded-xl flex flex-col gap-1.5 shadow-lg">
            <div className="flex justify-between items-center text-[#c2c6d6]">
              <span className="text-xs">총 운행 거리</span>
              <span className="material-symbols-outlined text-base">share_location</span>
            </div>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold text-[#d4e4fa] font-mono">
                {efficiencyStats.totalDistanceKmFormatted}
              </span>
              <span className="text-xs text-[#c2c6d6]">km</span>
            </div>
            <div className="h-6 w-full mt-1 rounded bg-[#1c2b3c] relative overflow-hidden">
              <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 30">
                <polyline fill="none" points="0,15 30,15 35,5 45,25 50,15 100,15" stroke="#424754" strokeWidth="2" />
              </svg>
            </div>
          </div>

          {/* KPI Card 5 */}
          <div className="glass-panel p-3.5 rounded-xl flex flex-col gap-1.5 shadow-lg">
            <div className="flex justify-between items-center text-[#c2c6d6]">
              <span className="text-xs">예상 소요 시간</span>
              <span className="material-symbols-outlined text-base">schedule</span>
            </div>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold text-[#d4e4fa] font-mono">
                {efficiencyStats.estimatedTotalHours}
              </span>
              <span className="text-xs text-[#c2c6d6]">h</span>
            </div>
            <div className="h-6 w-full mt-1 rounded bg-[#1c2b3c] flex items-center justify-center">
              <span className="text-[10px] font-bold text-[#4edea3]">정상 관제</span>
            </div>
          </div>
        </div>

        {/* Interactive Map Area */}
        <div className="flex-1 rounded-xl overflow-hidden relative shadow-2xl">
          <InteractiveMap
            nodes={nodes}
            vehicles={vehicles}
            activeIncident={activeIncident}
            selectedVehicleId={selectedVehicleId}
            onSelectVehicle={onSelectVehicle}
            onOpenRerouteConsole={onOpenRerouteConsole}
            activeScenarioId={activeScenarioId}
          />
        </div>
      </div>

      {/* Right Sidebar: Fleet Efficiency & Real-time Alerts */}
      <div className="w-[320px] flex flex-col gap-4 shrink-0 h-full overflow-hidden">
        {/* Fleet Efficiency Card */}
        <div className="glass-panel rounded-xl p-4 flex flex-col gap-3 shadow-lg">
          <h3 className="text-base font-bold text-[#d4e4fa] flex items-center gap-2">
            <span className="material-symbols-outlined text-[#4edea3]">speed</span>
            함대 효율성
          </h3>
          <div className="flex items-end justify-between">
            <div className="flex flex-col">
              <span className="text-3xl font-bold text-[#4edea3] font-mono">
                {efficiencyStats.efficiencyPercentage}%
              </span>
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#c2c6d6]">
                최적 성능
              </span>
            </div>
            {/* Circular Gauge */}
            <div className="w-12 h-12 relative flex items-center justify-center rounded-full border-4 border-[#273647]">
              <svg className="absolute inset-0 w-full h-full -rotate-90">
                <circle
                  cx="20"
                  cy="20"
                  r="18"
                  fill="none"
                  stroke="#4edea3"
                  strokeWidth="4"
                  strokeDasharray="113"
                  strokeDashoffset="7"
                />
              </svg>
            </div>
          </div>

          <div className="flex flex-col gap-1.5 pt-2 border-t border-[#424754]/20 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-[#c2c6d6]">연료 소비량 변동</span>
              <span className="text-[#4d8eff] font-mono font-bold">
                {efficiencyStats.fuelConsumptionChange}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-[#c2c6d6]">공회전 시간</span>
              <span className="text-[#4edea3] font-mono font-bold">
                {efficiencyStats.avgIdlingMinutes}분 평균
              </span>
            </div>
          </div>
        </div>

        {/* Real-time Alert Feed */}
        <div className="glass-panel rounded-xl flex-1 flex flex-col overflow-hidden border-t-2 border-[#ffb95f]/60 shadow-lg">
          <div className="p-3.5 border-b border-[#424754]/30 flex justify-between items-center bg-[#1c2b3c]/50">
            <h3 className="text-sm font-bold text-[#d4e4fa] flex items-center gap-2">
              <span className="material-symbols-outlined text-[#ffb95f] text-base">
                rss_feed
              </span>
              실시간 알림
            </h3>
            <span className="text-[10px] font-bold text-[#ffb95f] bg-[#ca8100]/20 px-2 py-0.5 rounded border border-[#ca8100]/30">
              {alerts.length}개 수집
            </span>
          </div>

          <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-2.5">
            {alerts.map((alert) => {
              const isHigh = alert.severity === 'high';
              const isMedium = alert.severity === 'medium';

              return (
                <div
                  key={alert.id}
                  className={`p-3 rounded-lg border flex gap-2.5 items-start transition-all ${
                    isHigh
                      ? 'bg-[#93000a]/20 border-[#ffb4ab]/40 shadow-sm'
                      : isMedium
                      ? 'bg-[#ca8100]/10 border-[#ffb95f]/30'
                      : 'bg-[#1c2b3c]/60 border-[#424754]/30'
                  }`}
                >
                  <div
                    className={`p-1.5 rounded-md shrink-0 mt-0.5 ${
                      isHigh
                        ? 'bg-[#93000a] text-[#ffdad6]'
                        : isMedium
                        ? 'bg-[#ca8100]/30 text-[#ffb95f]'
                        : 'bg-[#273647] text-[#4d8eff]'
                    }`}
                  >
                    <span className="material-symbols-outlined text-base">
                      {isHigh ? 'car_crash' : isMedium ? 'traffic' : 'check_circle'}
                    </span>
                  </div>

                  <div className="flex flex-col gap-1 flex-1 min-w-0">
                    <div className="flex justify-between items-baseline w-full">
                      <span
                        className={`text-xs font-bold truncate ${
                          isHigh
                            ? 'text-[#ffdad6]'
                            : isMedium
                            ? 'text-[#ffb95f]'
                            : 'text-[#d4e4fa]'
                        }`}
                      >
                        {alert.title}
                      </span>
                      <span className="text-[10px] text-[#8c909f] font-mono shrink-0 ml-1">
                        {alert.timestamp}
                      </span>
                    </div>

                    <p className="text-[11px] text-[#c2c6d6] leading-snug">
                      {alert.description}
                    </p>

                    {isHigh && (
                      <div className="mt-1 flex gap-2">
                        <button
                          onClick={() => onNavigatePage('initial-route')}
                          className="text-[10px] font-bold text-[#ffb4ab] hover:underline flex items-center gap-0.5"
                        >
                          관제 및 위험 분석 <span className="material-symbols-outlined text-[12px]">chevron_right</span>
                        </button>
                        <button
                          onClick={onOpenRerouteConsole}
                          className="text-[10px] font-bold text-[#adc6ff] hover:underline flex items-center gap-0.5"
                        >
                          재경로 설정 <span className="material-symbols-outlined text-[12px]">settings</span>
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
