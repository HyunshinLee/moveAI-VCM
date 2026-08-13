import React, { useState, useEffect } from 'react';
import {
  RouteNode,
  OptimizationObjective,
  OptimizationSettings,
  PlannedTruckRoute,
  FleetVehicle,
  IncidentAlert,
  ScenarioOptionId,
} from '../types';
import { RoutePlanningMap } from '../components/RoutePlanningMap';
import { generatePlannedRoutes } from '../data/routeData';

interface InitialRoutePageProps {
  nodes: RouteNode[];
  vehicles?: FleetVehicle[];
  activeIncident?: IncidentAlert | null;
  onOpenRerouteConsole?: () => void;
  onSelectVehicle?: (vehicleId: string | null) => void;
  selectedVehicleId?: string | null;
  onRunOptimization?: (settings: any) => void;
  optimizationResults?: any;
  activeScenarioId?: ScenarioOptionId | null;
}

export const InitialRoutePage: React.FC<InitialRoutePageProps> = ({
  nodes,
  vehicles = [],
  activeIncident,
  onOpenRerouteConsole,
  onSelectVehicle,
  selectedVehicleId: propSelectedVehicleId,
  activeScenarioId,
}) => {
  // Local selection state if not controlled externally
  const [internalSelectedVehicleId, setInternalSelectedVehicleId] = useState<string | null>('TRK-T02');

  const selectedVehicleId = propSelectedVehicleId !== undefined ? propSelectedVehicleId : internalSelectedVehicleId;

  const handleSelectVehicle = (id: string | null) => {
    setInternalSelectedVehicleId(id);
    if (onSelectVehicle) {
      onSelectVehicle(id);
    }
  };

  // Optimization Input Settings State
  const [objective, setObjective] = useState<OptimizationObjective>('balanced');
  const [truckCount, setTruckCount] = useState<number>(5);
  const [depotSelection, setDepotSelection] = useState<'both' | 'D01' | 'D12'>('both');
  const [timeWindowWeight, setTimeWindowWeight] = useState<'low' | 'medium' | 'high'>('medium');
  const [capacityLimit, setCapacityLimit] = useState<number>(85);
  const [realTimeTraffic, setRealTimeTraffic] = useState<boolean>(true);

  // Optimization Execution State
  const [isOptimizing, setIsOptimizing] = useState<boolean>(false);
  const [truckRoutes, setTruckRoutes] = useState<PlannedTruckRoute[]>(() =>
    generatePlannedRoutes({
      objective: 'balanced',
      truckCount: 5,
      depotSelection: 'both',
      timeWindowWeight: 'medium',
      capacityLimit: 85,
      realTimeTraffic: true,
    })
  );

  // Simulation State
  const [simulatedTimeProgress, setSimulatedTimeProgress] = useState<number>(0.15); // Start at ~10:12 AM
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [speedMultiplier, setSpeedMultiplier] = useState<1 | 2 | 5>(1);

  // Animation ticker for real-time truck movement simulation
  useEffect(() => {
    if (!isPlaying) return;

    const interval = setInterval(() => {
      setSimulatedTimeProgress((prev) => {
        const step = 0.0012 * speedMultiplier;
        if (prev + step >= 1.0) {
          setIsPlaying(false);
          return 1.0;
        }
        return prev + step;
      });
    }, 40);

    return () => clearInterval(interval);
  }, [isPlaying, speedMultiplier]);

  // Handle Run Optimization Button Click
  const handleRunOptimization = () => {
    setIsOptimizing(true);
    setIsPlaying(false);

    setTimeout(() => {
      const newSettings: OptimizationSettings = {
        objective,
        truckCount,
        depotSelection,
        timeWindowWeight,
        capacityLimit,
        realTimeTraffic,
      };

      const recalculatedRoutes = generatePlannedRoutes(newSettings);
      setTruckRoutes(recalculatedRoutes);
      handleSelectVehicle(null);
      setSimulatedTimeProgress(0.0);
      setIsOptimizing(false);
    }, 1000);
  };

  // Fleet Overall Aggregate Metrics
  const totalDistanceKm = Math.round(
    truckRoutes.reduce((acc, r) => acc + r.totalDistanceKm, 0) * 10
  ) / 10;
  const totalTravelTimeMin = truckRoutes.reduce((acc, r) => acc + r.travelTimeMin, 0);
  const totalTravelTimeHrs = Math.round((totalTravelTimeMin / 60) * 10) / 10;
  const vehiclesUsedCount = truckRoutes.length;
  const delayedDeliveriesCount = truckRoutes.filter((r) => r.tardinessRatePct > 0).length;

  // Selected Truck Object
  const selectedTruck = truckRoutes.find((r) => r.vehicleId === selectedVehicleId);

  return (
    <div className="flex-1 mt-16 p-6 flex gap-6 overflow-hidden relative z-10 h-[calc(100vh-64px)]">
      {/* 1. Left Control Panel (Optimization Preferences) */}
      <div className="w-[340px] flex-shrink-0 flex flex-col gap-4 overflow-hidden pointer-events-auto">
        <div className="glass-panel rounded-xl p-5 flex flex-col h-full shadow-2xl border border-[#424754]/40">
          <div className="flex items-center justify-between mb-5 border-b border-[#424754]/30 pb-3.5">
            <div>
              <h2 className="text-base font-bold text-[#d4e4fa]">최적화 환경 설정</h2>
              <span className="text-[10px] text-[#8c909f] font-mono">Optimization Preferences</span>
            </div>
            <span className="material-symbols-outlined text-[#8c909f]">tune</span>
          </div>

          <div className="flex-1 space-y-5 overflow-y-auto pr-1">
            {/* Optimization Objective Selector */}
            <div className="space-y-2.5">
              <label className="text-[11px] font-bold uppercase tracking-wider text-[#c2c6d6] block">
                최적화 목표 설정 (Optimization Objective)
              </label>

              <div className="grid grid-cols-1 gap-2">
                {[
                  {
                    id: 'balanced',
                    title: '균형 설정 (Balanced)',
                    desc: '시간 + 비용 + 지연 페널티 최적화',
                  },
                  {
                    id: 'fast',
                    title: '빠른 배송 (Fastest Delivery)',
                    desc: '총 이동 시간 최소화',
                  },
                  {
                    id: 'satisfaction',
                    title: '고객 만족도 (Customer Satisfaction)',
                    desc: '시간창 지연 준수 및 페널티 최소화',
                  },
                  {
                    id: 'cost',
                    title: '비용 절감 (Cost Saving)',
                    desc: '차량 수 및 총 운행 거리 최소화',
                  },
                ].map((opt) => {
                  const isChecked = objective === opt.id;
                  return (
                    <div
                      key={opt.id}
                      onClick={() => setObjective(opt.id as OptimizationObjective)}
                      className={`p-3 rounded-lg border cursor-pointer transition-all flex items-start gap-3 ${
                        isChecked
                          ? 'border-[#4d8eff] bg-[#4d8eff]/15 text-[#adc6ff] shadow-md shadow-[#4d8eff]/10'
                          : 'border-[#424754]/40 bg-[#122131]/40 hover:bg-white/5 text-[#c2c6d6]'
                      }`}
                    >
                      <input
                        type="radio"
                        name="objective"
                        checked={isChecked}
                        onChange={() => {}}
                        className="mt-0.5 form-radio h-4 w-4 text-[#4d8eff] bg-transparent border-[#8c909f] focus:ring-0"
                      />
                      <div>
                        <div className="text-xs font-bold">{opt.title}</div>
                        <div className="text-[10px] text-[#8c909f] mt-0.5">{opt.desc}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Input Parameter 1: Number of Trucks */}
            <div className="space-y-2 pt-2 border-t border-[#424754]/20">
              <div className="flex justify-between items-center">
                <label className="text-[11px] font-bold uppercase tracking-wider text-[#c2c6d6]">
                  배차 트럭 수 (Number of Trucks)
                </label>
                <span className="text-xs font-mono font-bold text-[#4d8eff] bg-[#4d8eff]/10 px-2 py-0.5 rounded border border-[#4d8eff]/30">
                  {truckCount} 대
                </span>
              </div>
              <div className="relative pt-1">
                <input
                  type="range"
                  min="1"
                  max="10"
                  step="1"
                  value={truckCount}
                  onChange={(e) => setTruckCount(Number(e.target.value))}
                  className="w-full cursor-pointer accent-[#4d8eff]"
                />
                <div className="flex justify-between text-[10px] text-[#8c909f] mt-1 font-mono">
                  <span>1대</span>
                  <span>5대</span>
                  <span>10대</span>
                </div>
              </div>
            </div>

            {/* Input Parameter 2: Depot Selection */}
            <div className="space-y-2 pt-2 border-t border-[#424754]/20">
              <label className="text-[11px] font-bold uppercase tracking-wider text-[#c2c6d6] block">
                출발 차고지 선택 (Depot Selection)
              </label>
              <select
                value={depotSelection}
                onChange={(e) => setDepotSelection(e.target.value as 'both' | 'D01' | 'D12')}
                className="w-full bg-[#122131] text-[#d4e4fa] border border-[#424754]/50 rounded-lg p-2.5 text-xs font-bold focus:outline-none focus:border-[#4d8eff]"
              >
                <option value="both">통합 운행 (마포 D01 + 강남 D12)</option>
                <option value="D01">마포 메인 센터 전용 (D01)</option>
                <option value="D12">강남 허브 센터 전용 (D12)</option>
              </select>
            </div>

            {/* Input Parameter 3: Time Window Weights */}
            <div className="space-y-2 pt-2 border-t border-[#424754]/20">
              <label className="text-[11px] font-bold uppercase tracking-wider text-[#c2c6d6] block">
                시간창 가중치 (Time Window Weight)
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: 'low', label: '낮음 (Low)' },
                  { id: 'medium', label: '보통 (Med)' },
                  { id: 'high', label: '높음 (High)' },
                ].map((w) => (
                  <button
                    key={w.id}
                    type="button"
                    onClick={() => setTimeWindowWeight(w.id as 'low' | 'medium' | 'high')}
                    className={`py-1.5 px-2 rounded-lg text-xs font-bold border transition-all ${
                      timeWindowWeight === w.id
                        ? 'bg-[#4d8eff] text-[#00285d] border-[#4d8eff]'
                        : 'bg-[#122131]/60 text-[#c2c6d6] border-[#424754]/40 hover:bg-white/5'
                    }`}
                  >
                    {w.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Input Parameter 4: Vehicle Capacity Limit */}
            <div className="space-y-2 pt-2 border-t border-[#424754]/20">
              <div className="flex justify-between items-center">
                <label className="text-[11px] font-bold uppercase tracking-wider text-[#c2c6d6]">
                  차량 적재 용량 제한 (Capacity Limit)
                </label>
                <span className="text-xs font-mono font-bold text-[#adc6ff] bg-[#4d8eff]/10 px-2 py-0.5 rounded">
                  {capacityLimit}%
                </span>
              </div>
              <div className="relative pt-1">
                <input
                  type="range"
                  min="50"
                  max="100"
                  value={capacityLimit}
                  onChange={(e) => setCapacityLimit(Number(e.target.value))}
                  className="w-full cursor-pointer accent-[#4d8eff]"
                />
              </div>
            </div>

            {/* Input Parameter 5: Real-time Traffic */}
            <div className="space-y-2 pt-2 border-t border-[#424754]/20">
              <div className="flex justify-between items-center">
                <label className="text-[11px] font-bold uppercase tracking-wider text-[#c2c6d6]">
                  실시간 교통 데이터 반영
                </label>
                <button
                  type="button"
                  onClick={() => setRealTimeTraffic(!realTimeTraffic)}
                  className={`w-10 h-5 rounded-full transition-colors relative flex items-center p-0.5 ${
                    realTimeTraffic ? 'bg-[#4edea3]' : 'bg-[#273647]'
                  }`}
                >
                  <div
                    className={`w-4 h-4 rounded-full bg-white transition-transform ${
                      realTimeTraffic ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          {/* Action Button: Run Route Optimization */}
          <div className="mt-4 pt-3 border-t border-[#424754]/30">
            <button
              type="button"
              onClick={handleRunOptimization}
              disabled={isOptimizing}
              className="w-full bg-[#adc6ff] hover:bg-[#d8e2ff] text-[#002e6a] py-3 px-4 rounded-xl text-sm font-bold transition-all flex items-center justify-center gap-2 shadow-lg shadow-[#adc6ff]/20 active:scale-95 disabled:opacity-50"
            >
              <span
                className={`material-symbols-outlined text-lg ${
                  isOptimizing ? 'animate-spin' : ''
                }`}
              >
                {isOptimizing ? 'sync' : 'play_arrow'}
              </span>
              {isOptimizing ? 'ALNS 엔진 경로 재계산 중...' : '최적화 실행 (Run Optimization)'}
            </button>
          </div>
        </div>
      </div>

      {/* 2. Interactive Route Map Component (Center Main Area) */}
      <div className="flex-1 rounded-xl overflow-hidden relative shadow-2xl border border-[#424754]/30 flex flex-col">
        <RoutePlanningMap
          nodes={nodes}
          truckRoutes={truckRoutes}
          vehicles={vehicles}
          activeIncident={activeIncident}
          selectedVehicleId={selectedVehicleId}
          onSelectVehicle={handleSelectVehicle}
          onOpenRerouteConsole={onOpenRerouteConsole}
          simulatedTimeProgress={simulatedTimeProgress}
          isPlaying={isPlaying}
          onTogglePlay={() => setIsPlaying(!isPlaying)}
          speedMultiplier={speedMultiplier}
          onChangeSpeed={setSpeedMultiplier}
          onTimeProgressChange={setSimulatedTimeProgress}
          activeScenarioId={activeScenarioId}
        />
      </div>

      {/* 3. Right Result Metrics Panel & Truck Selection Area */}
      <div className="w-[340px] flex-shrink-0 flex flex-col gap-4 pointer-events-auto h-full overflow-hidden">
        {/* Dynamic Result Metrics Panel */}
        <div className="glass-panel rounded-xl p-5 shadow-2xl flex flex-col gap-3.5 border border-[#424754]/40">
          <div className="flex items-center justify-between border-b border-[#424754]/30 pb-3">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[#4edea3]">analytics</span>
              <h2 className="text-sm font-bold text-[#d4e4fa]">
                {selectedTruck ? `${selectedTruck.vehicleName} 상세지표` : '전체 함대 최적화 결과'}
              </h2>
            </div>
            {selectedTruck && (
              <button
                type="button"
                onClick={() => handleSelectVehicle(null)}
                className="text-[10px] font-bold text-[#adc6ff] bg-[#4d8eff]/20 hover:bg-[#4d8eff]/40 px-2 py-0.5 rounded transition-colors"
              >
                전체 보기
              </button>
            )}
          </div>

          {/* Metrics Grid */}
          {selectedTruck ? (
            /* Selected Truck Specific Metrics */
            <div className="space-y-2.5">
              <div
                className="p-3 rounded-lg border flex items-center justify-between"
                style={{
                  backgroundColor: `${selectedTruck.routeColor}15`,
                  borderColor: `${selectedTruck.routeColor}55`,
                }}
              >
                <div>
                  <div className="text-[10px] font-bold uppercase text-[#c2c6d6]">
                    선택된 차량 (Focused Truck)
                  </div>
                  <div className="text-base font-bold" style={{ color: selectedTruck.routeColor }}>
                    {selectedTruck.vehicleName} ({selectedTruck.vehicleCode})
                  </div>
                  <div className="text-xs text-[#8c909f] mt-0.5">
                    담당 기사: {selectedTruck.driverName}
                  </div>
                </div>
                <div
                  className="w-4 h-4 rounded-full shadow-lg"
                  style={{ backgroundColor: selectedTruck.routeColor }}
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="bg-[#1c2b3c]/60 p-2.5 rounded-lg border border-white/5">
                  <div className="text-[10px] font-bold text-[#c2c6d6]">운행 거리</div>
                  <div className="text-lg font-bold text-[#d4e4fa] font-mono mt-0.5">
                    {selectedTruck.totalDistanceKm}{' '}
                    <span className="text-xs text-[#8c909f] font-normal">km</span>
                  </div>
                </div>

                <div className="bg-[#1c2b3c]/60 p-2.5 rounded-lg border border-white/5">
                  <div className="text-[10px] font-bold text-[#c2c6d6]">예상 소요 시간</div>
                  <div className="text-lg font-bold text-[#d4e4fa] font-mono mt-0.5">
                    {selectedTruck.travelTimeMin}{' '}
                    <span className="text-xs text-[#8c909f] font-normal">분</span>
                  </div>
                </div>

                <div className="bg-[#1c2b3c]/60 p-2.5 rounded-lg border border-white/5">
                  <div className="text-[10px] font-bold text-[#c2c6d6]">할당 고객사</div>
                  <div className="text-lg font-bold text-[#4edea3] font-mono mt-0.5">
                    {selectedTruck.assignedCustomersCount}{' '}
                    <span className="text-xs text-[#8c909f] font-normal">개소</span>
                  </div>
                </div>

                <div className="bg-[#1c2b3c]/60 p-2.5 rounded-lg border border-white/5">
                  <div className="text-[10px] font-bold text-[#c2c6d6]">적재율</div>
                  <div className="text-lg font-bold text-[#4d8eff] font-mono mt-0.5">
                    {selectedTruck.loadPercentage}%
                  </div>
                </div>
              </div>

              <div className="bg-[#122131]/60 p-2.5 rounded-lg border border-[#424754]/40 text-xs space-y-1">
                <div className="text-[#8c909f] font-bold">경로 노드 순서:</div>
                <div className="font-mono text-[#d4e4fa] text-[11px] truncate">
                  {selectedTruck.assignedNodes.join(' ➔ ')}
                </div>
              </div>
            </div>
          ) : (
            /* Fleet-wide Overall Summary Indicators */
            <div className="grid grid-cols-2 gap-2.5">
              {/* Total Distance */}
              <div className="bg-[#1c2b3c]/60 p-3 rounded-lg border border-white/5">
                <div className="text-[10px] font-bold text-[#c2c6d6]">총 운행 거리</div>
                <div className="text-xl font-bold text-[#d4e4fa] font-mono mt-1">
                  {totalDistanceKm.toLocaleString()}{' '}
                  <span className="text-xs text-[#8c909f] font-normal">km</span>
                </div>
              </div>

              {/* Total Travel Time */}
              <div className="bg-[#1c2b3c]/60 p-3 rounded-lg border border-white/5">
                <div className="text-[10px] font-bold text-[#c2c6d6]">총 소요 시간</div>
                <div className="text-xl font-bold text-[#d4e4fa] font-mono mt-1">
                  {totalTravelTimeHrs}{' '}
                  <span className="text-xs text-[#8c909f] font-normal">시간</span>
                </div>
              </div>

              {/* Vehicles Used */}
              <div className="bg-[#1c2b3c]/60 p-3 rounded-lg border border-white/5">
                <div className="text-[10px] font-bold text-[#c2c6d6]">투입 차량 수</div>
                <div className="text-xl font-bold text-[#adc6ff] font-mono mt-1">
                  {vehiclesUsedCount}{' '}
                  <span className="text-xs text-[#8c909f] font-normal">대</span>
                </div>
              </div>

              {/* Tardiness / Delay Rate */}
              <div className="bg-[#1c2b3c]/60 p-3 rounded-lg border border-white/5">
                <div className="text-[10px] font-bold text-[#c2c6d6]">지연율 (Tardiness)</div>
                <div className="text-xl font-bold text-[#4edea3] font-mono mt-1">
                  0.0 <span className="text-xs font-normal">%</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Truck Selection Area & Legend List */}
        <div className="glass-panel rounded-xl p-4 shadow-2xl flex-1 overflow-y-auto border border-[#424754]/40 flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#c2c6d6]">
              트럭 경로 카드 (Truck Selection)
            </h3>
            <span className="text-[10px] text-[#8c909f]">클릭하여 특정 경로 강조</span>
          </div>

          <div className="space-y-2 flex-1 overflow-y-auto pr-0.5">
            {truckRoutes.map((route) => {
              const isSelected = selectedVehicleId === route.vehicleId;
              const vehicleState = vehicles.find((v) => v.id === route.vehicleId);
              const isRisk =
                vehicleState?.status === 'risk' ||
                (route.vehicleId === 'TRK-T02' && activeIncident && !activeIncident.resolved);
              const isWarning = vehicleState?.status === 'warning';

              return (
                <div
                  key={route.vehicleId}
                  onClick={() => handleSelectVehicle(isSelected ? null : route.vehicleId)}
                  className={`p-2.5 rounded-lg cursor-pointer transition-all border flex items-center justify-between ${
                    isRisk
                      ? 'bg-[#93000a]/20 border-[#ffb4ab] shadow-md'
                      : isSelected
                      ? 'bg-[#1c2b3c] border-[#4d8eff] shadow-lg ring-1 ring-[#4d8eff]/50'
                      : 'bg-[#122131]/50 border-[#424754]/30 hover:bg-white/5 hover:border-white/20'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-3.5 h-3.5 rounded-full shadow-md flex-shrink-0 ${
                        isRisk ? 'bg-[#ffb4ab]' : isWarning ? 'bg-[#ffb95f]' : ''
                      }`}
                      style={{
                        backgroundColor: !isRisk && !isWarning ? route.routeColor : undefined,
                        boxShadow: `0 0 8px ${isRisk ? '#ffb4ab' : route.routeColor}aa`,
                      }}
                    />
                    <div>
                      <div className="text-xs font-bold text-[#d4e4fa] flex items-center gap-1.5">
                        <span>{route.vehicleName}</span>
                        <span className="text-[10px] font-mono text-[#8c909f]">
                          ({route.vehicleCode})
                        </span>
                        {isRisk && (
                          <span className="bg-[#93000a] text-[#ffdad6] text-[9px] font-bold px-1.5 py-0.5 rounded border border-[#ffb4ab]/40">
                            ⚠️ RISK
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-[#8c909f] mt-0.5">
                        {route.driverName} • {route.totalDistanceKm}km
                        {isRisk && <span className="text-[#ffb4ab] font-bold ml-1">+45분 지연</span>}
                      </div>
                    </div>
                  </div>

                  <div className="text-right">
                    <span
                      className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                        isRisk ? 'bg-[#93000a] text-[#ffdad6]' : ''
                      }`}
                      style={{
                        backgroundColor: !isRisk ? `${route.routeColor}22` : undefined,
                        color: !isRisk ? route.routeColor : undefined,
                      }}
                    >
                      {route.travelTimeMin}분
                    </span>
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
