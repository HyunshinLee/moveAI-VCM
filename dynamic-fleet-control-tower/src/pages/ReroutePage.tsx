import React from 'react';
import { RouteNode, FleetVehicle, IncidentAlert } from '../types';
import { InteractiveMap } from '../components/InteractiveMap';

interface ReroutePageProps {
  nodes: RouteNode[];
  vehicles: FleetVehicle[];
  activeIncident: IncidentAlert | null;
  onOpenRerouteConsole: () => void;
  onSelectVehicle: (vehicleId: string) => void;
  selectedVehicleId: string | null;
  activeScenarioId: string | null;
}

export const ReroutePage: React.FC<ReroutePageProps> = ({
  nodes,
  vehicles,
  activeIncident,
  onOpenRerouteConsole,
  onSelectVehicle,
  selectedVehicleId,
  activeScenarioId,
}) => {
  return (
    <div className="flex-1 mt-16 p-6 flex gap-6 overflow-hidden relative z-10 h-[calc(100vh-64px)]">
      {/* Left Panel: Risk Vehicles List */}
      <div className="w-[340px] flex flex-col gap-4 shrink-0 h-full pointer-events-auto overflow-hidden">
        {/* Header */}
        <div className="glass-panel rounded-xl p-4 flex items-center justify-between shadow-lg">
          <div>
            <h2 className="text-base font-bold text-[#d4e4fa] m-0">재경로 관리</h2>
            <p className="text-xs text-[#8c909f] mt-0.5">Re-routing Management</p>
          </div>
          <span className="material-symbols-outlined text-[#8c909f]">tune</span>
        </div>

        {/* Risk Vehicles List */}
        <div className="glass-panel rounded-xl flex-1 overflow-hidden flex flex-col shadow-lg border-t-2 border-[#ffb4ab]/60">
          <div className="p-3.5 border-b border-[#424754]/30 flex justify-between items-center bg-[#1c2b3c]/50">
            <h3 className="text-xs font-bold text-[#d4e4fa] flex items-center gap-2">
              <span className="material-symbols-outlined text-[#ffb95f] text-base">
                warning
              </span>
              위험 감지 차량
            </h3>
            <span className="bg-[#93000a]/30 text-[#ffb4ab] border border-[#ffb4ab]/30 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold">
              3 ACTIVE
            </span>
          </div>

          <div className="overflow-y-auto p-3 flex flex-col gap-3 flex-1">
            {/* Truck T02 (Active Risk) */}
            <div
              onClick={() => {
                onSelectVehicle('TRK-T02');
                onOpenRerouteConsole();
              }}
              className="bg-[#93000a]/15 border border-[#ffb4ab]/40 rounded-xl p-4 cursor-pointer hover:bg-[#93000a]/25 transition-all relative overflow-hidden group shadow-md"
            >
              <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#ffb4ab]" />
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[#d4e4fa]">
                    local_shipping
                  </span>
                  <span className="font-mono text-[#d4e4fa] font-bold text-sm">
                    TRK-T02
                  </span>
                </div>
                <span className="bg-[#93000a] text-[#ffdad6] px-2 py-0.5 rounded text-[10px] font-bold flex items-center gap-1 border border-[#ffb4ab]/30">
                  <span className="material-symbols-outlined text-[13px]">error</span>
                  위험 감지
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs mt-3 font-sans">
                <div className="text-[#8c909f]">
                  위치: <span className="text-[#d4e4fa] font-mono">C03 ➔ C07</span>
                </div>
                <div className="text-[#8c909f]">
                  지연 예상: <span className="text-[#ffb4ab] font-mono font-bold">+45min</span>
                </div>
                <div className="text-[#8c909f] col-span-2">
                  원인: <span className="text-[#ffb4ab] font-semibold">Traffic Disruption (사고)</span>
                </div>
              </div>

              <div className="mt-3 pt-2 border-t border-[#ffb4ab]/20 flex justify-end">
                <span className="text-[10px] font-bold text-[#adc6ff] flex items-center gap-1 group-hover:underline">
                  3가지 대응 시나리오 비교 <span className="material-symbols-outlined text-xs">arrow_forward</span>
                </span>
              </div>
            </div>

            {/* Truck T14 (Warning) */}
            <div
              onClick={() => onSelectVehicle('TRK-T14')}
              className="bg-[#122131]/60 border border-[#424754]/30 rounded-xl p-4 hover:border-[#ffb95f]/40 transition-colors relative cursor-pointer"
            >
              <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#ffb95f] opacity-60" />
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[#d4e4fa]">
                    local_shipping
                  </span>
                  <span className="font-mono text-[#d4e4fa] font-semibold text-sm">
                    TRK-T14
                  </span>
                </div>
                <span className="bg-[#ca8100]/20 text-[#ffb95f] px-2 py-0.5 rounded text-[10px] font-bold border border-[#ca8100]/30">
                  경고
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs text-[#8c909f] mt-2 font-sans">
                <div>
                  위치: <span className="text-[#d4e4fa] font-mono">N12 ➔ N15</span>
                </div>
                <div>
                  지연 예상: <span className="text-[#ffb95f] font-mono font-bold">+12min</span>
                </div>
              </div>
            </div>

            {/* Truck T08 (Warning) */}
            <div
              onClick={() => onSelectVehicle('TRK-T08')}
              className="bg-[#122131]/60 border border-[#424754]/30 rounded-xl p-4 hover:border-[#ffb95f]/40 transition-colors relative cursor-pointer"
            >
              <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#ffb95f] opacity-60" />
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[#d4e4fa]">
                    local_shipping
                  </span>
                  <span className="font-mono text-[#d4e4fa] font-semibold text-sm">
                    TRK-T08
                  </span>
                </div>
                <span className="bg-[#ca8100]/20 text-[#ffb95f] px-2 py-0.5 rounded text-[10px] font-bold border border-[#ca8100]/30">
                  경고
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs text-[#8c909f] mt-2 font-sans">
                <div>
                  위치: <span className="text-[#d4e4fa] font-mono">S01 ➔ S04</span>
                </div>
                <div>
                  지연 예상: <span className="text-[#ffb95f] font-mono font-bold">+08min</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Center Map Area */}
      <div className="flex-1 rounded-xl overflow-hidden relative shadow-2xl border border-[#424754]/30">
        <InteractiveMap
          nodes={nodes}
          vehicles={vehicles}
          activeIncident={activeIncident}
          selectedVehicleId={selectedVehicleId}
          onOpenRerouteConsole={onOpenRerouteConsole}
          onSelectVehicle={onSelectVehicle}
          activeScenarioId={activeScenarioId}
        />

        {/* Action Button Banner Over Map */}
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-20 pointer-events-auto">
          <button
            onClick={onOpenRerouteConsole}
            className="px-6 py-3 bg-[#4d8eff] hover:bg-[#d8e2ff] text-[#00285d] font-bold rounded-xl shadow-2xl flex items-center gap-2 text-sm transition-all border border-[#adc6ff]/50 animate-bounce"
          >
            <span className="material-symbols-outlined text-xl">psychology</span>
            TRK-T02 재경로 의사소통 콘솔 열기
          </button>
        </div>
      </div>

      {/* Right Panel: Analytics */}
      <div className="w-[320px] flex flex-col gap-4 shrink-0 h-full pointer-events-auto">
        <div className="glass-panel rounded-xl flex flex-col overflow-hidden shadow-2xl border-t-2 border-[#4d8eff]">
          <div className="p-4 border-b border-[#424754]/30 flex items-center gap-2 bg-[#1c2b3c]/50">
            <span className="material-symbols-outlined text-[#4d8eff] text-lg">
              analytics
            </span>
            <h3 className="text-sm font-bold text-[#d4e4fa]">플릿 분석</h3>
          </div>

          <div className="p-5 flex flex-col gap-5">
            {/* Metric 1 */}
            <div className="flex flex-col gap-1">
              <span className="text-[10px] font-bold uppercase text-[#8c909f] tracking-wider">
                ACTIVE REROUTES
              </span>
              <div className="flex items-end justify-between">
                <span className="text-2xl font-bold font-mono text-[#4d8eff]">12</span>
                <span className="text-xs font-bold text-[#4edea3] flex items-center">
                  <span className="material-symbols-outlined text-xs">arrow_upward</span> 2
                </span>
              </div>
              {/* Sparkbar */}
              <div className="h-6 w-full mt-1 flex items-end gap-1 opacity-70">
                <div className="w-full bg-[#4d8eff]/30 h-[20%] rounded-t-sm" />
                <div className="w-full bg-[#4d8eff]/30 h-[40%] rounded-t-sm" />
                <div className="w-full bg-[#4d8eff]/50 h-[30%] rounded-t-sm" />
                <div className="w-full bg-[#4d8eff]/70 h-[70%] rounded-t-sm" />
                <div className="w-full bg-[#4d8eff] h-[90%] rounded-t-sm" />
              </div>
            </div>

            <div className="h-px w-full bg-[#424754]/30" />

            {/* Metric 2 */}
            <div className="flex flex-col gap-1">
              <span className="text-[10px] font-bold uppercase text-[#8c909f] tracking-wider">
                NETWORK DELAY
              </span>
              <div className="flex items-end justify-between">
                <span className="text-2xl font-bold font-mono text-[#ffb4ab]">+45 min</span>
                <span className="text-xs font-bold text-[#ffb4ab] flex items-center">
                  <span className="material-symbols-outlined text-xs">trending_up</span>
                </span>
              </div>
            </div>

            <div className="h-px w-full bg-[#424754]/30" />

            {/* Metric 3 */}
            <div className="flex flex-col gap-1">
              <span className="text-[10px] font-bold uppercase text-[#8c909f] tracking-wider">
                EST. COST IMPACT
              </span>
              <div className="flex items-end justify-between">
                <span className="text-2xl font-bold font-mono text-[#ffb95f]">+$1.2k</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
