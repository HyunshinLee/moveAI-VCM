import React, { useState } from 'react';
import {
  PageId,
  RouteNode,
  FleetVehicle,
  IncidentAlert,
  RerouteScenario,
  OptimizationResults,
  FleetEfficiencyStats,
  ScenarioOptionId,
  OptimizationObjective,
} from './types';
import {
  INITIAL_NODES,
  INITIAL_VEHICLES,
  INITIAL_INCIDENT,
  INITIAL_ALERTS,
  DEFAULT_SCENARIOS,
  DEFAULT_OPTIMIZATION_RESULTS,
  DEFAULT_EFFICIENCY_STATS,
} from './mockData';

import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { RerouteConsoleModal } from './components/RerouteConsoleModal';
import { SettingsModal } from './components/SettingsModal';
import { SupportModal } from './components/SupportModal';

import { DashboardPage } from './pages/DashboardPage';
import { InitialRoutePage } from './pages/InitialRoutePage';
import { ReroutePage } from './pages/ReroutePage';

export default function App() {
  const [currentPage, setCurrentPage] = useState<PageId>('dashboard');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Application Data States
  const [nodes] = useState<RouteNode[]>(INITIAL_NODES);
  const [vehicles, setVehicles] = useState<FleetVehicle[]>(INITIAL_VEHICLES);
  const [alerts, setAlerts] = useState<IncidentAlert[]>(INITIAL_ALERTS);
  const [activeIncident, setActiveIncident] = useState<IncidentAlert | null>(INITIAL_INCIDENT);
  const [scenarios] = useState<RerouteScenario[]>(DEFAULT_SCENARIOS);
  const [optimizationResults, setOptimizationResults] = useState<OptimizationResults>(
    DEFAULT_OPTIMIZATION_RESULTS
  );
  const [efficiencyStats, setEfficiencyStats] = useState<FleetEfficiencyStats>(
    DEFAULT_EFFICIENCY_STATS
  );

  // Selection & Modal States
  const [selectedVehicleId, setSelectedVehicleId] = useState<string | null>('TRK-T02');
  const [isRerouteConsoleOpen, setIsRerouteConsoleOpen] = useState<boolean>(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [isSupportOpen, setIsSupportOpen] = useState<boolean>(false);
  const [activeScenarioId, setActiveScenarioId] = useState<ScenarioOptionId | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 4000);
  };

  // 1. Simulate or Reset Disruption Trigger
  const handleSimulateDisruption = () => {
    if (activeIncident && !activeIncident.resolved) {
      // Reset disruption to clear state
      setActiveIncident(null);
      setActiveScenarioId(null);
      setVehicles((prev) =>
        prev.map((v) =>
          v.id === 'TRK-T02'
            ? { ...v, status: 'active', delayMinutes: 0, notes: '정상 운행 중' }
            : v
        )
      );
      showToast('✅ 돌발상황이 초기화되었습니다. 모든 차량이 정상 우회 경로로 복귀했습니다.');
    } else {
      // Trigger new disruption
      const newIncident: IncidentAlert = { ...INITIAL_INCIDENT, resolved: false };
      setActiveIncident(newIncident);
      setActiveScenarioId(null);
      setVehicles((prev) =>
        prev.map((v) =>
          v.id === 'TRK-T02'
            ? {
                ...v,
                status: 'risk',
                delayMinutes: 45,
                notes: '돌발 상황: C03-C07 전방 추돌 사고 발생로 인한 정체',
              }
            : v
        )
      );
      setAlerts((prev) => [newIncident, ...prev.filter((a) => a.id !== newIncident.id)]);
      showToast('🚨 [돌발 감지] C03-C07 구간 3중 추돌 사고 발생! T02 차량 영향 가중 (위험 점수 0.92)');
    }
  };

  // 2. Confirm & Apply Rerouting Scenario (Option A, B, or C)
  const handleConfirmScenario = (scenarioId: ScenarioOptionId) => {
    setActiveScenarioId(scenarioId);

    const selectedScenario = scenarios.find((s) => s.id === scenarioId);
    if (!selectedScenario) return;

    // Update Truck T02 state according to scenario choice
    setVehicles((prev) =>
      prev.map((v) => {
        if (v.id === 'TRK-T02') {
          return {
            ...v,
            status: 'active',
            delayMinutes: Math.max(0, 45 + selectedScenario.delayReductionMin),
            etaMinutes: selectedScenario.travelTimeMin,
            notes: `적용 전략: ${selectedScenario.optionTitle} (${selectedScenario.koreanName}) - 시간 절감 ${Math.abs(selectedScenario.delayReductionMin)}분`,
          };
        }
        return v;
      })
    );

    // Update Incident State
    if (activeIncident) {
      setActiveIncident({
        ...activeIncident,
        resolved: true,
        appliedScenario: scenarioId,
      });
    }

    // Update Efficiency Stats
    setEfficiencyStats((prev) => ({
      ...prev,
      routeRiskIndexLevel: 'Low',
    }));

    showToast(
      `🎉 [전략 확정] ${selectedScenario.optionTitle} (${selectedScenario.koreanName}) 적용 완료! 단축 시간: ${Math.abs(selectedScenario.delayReductionMin)}분 | 추가 비용: +$${selectedScenario.addedCostUsd.toFixed(2)}`
    );
  };

  // 3. Handle TDVRP Optimization Run
  const handleRunOptimization = (settings: {
    objective: OptimizationObjective;
    capacityLimit: number;
    realTimeTraffic: boolean;
  }) => {
    setOptimizationResults((prev) => ({
      ...prev,
      totalDistanceKm: settings.objective === 'cost' ? 1120 : 1245,
      totalTimeHours: settings.objective === 'fast' ? 42.0 : 48.5,
      vehiclesUsed: 5,
      delayedDeliveriesCount: 0,
    }));
    showToast(
      `⚙️ ALNS 최적화 완료: [목표: ${settings.objective.toUpperCase()}] 적재 제한 ${settings.capacityLimit}% 적용`
    );
  };

  // Filtered vehicles and alerts for search query
  const filteredVehicles = vehicles.filter(
    (v) =>
      v.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.driverName.includes(searchQuery) ||
      v.currentSegment.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="bg-[#051424] text-[#d4e4fa] font-['Inter',sans-serif] h-screen overflow-hidden flex relative selection:bg-[#4d8eff] selection:text-[#00285d]">
      {/* Toast Notification Banner */}
      {toastMessage && (
        <div className="fixed top-20 right-6 z-50 bg-[#122131] border border-[#4d8eff] text-[#d4e4fa] px-4 py-3 rounded-xl shadow-2xl flex items-center gap-3 animate-bounce">
          <span className="material-symbols-outlined text-[#4edea3]">check_circle</span>
          <span className="text-xs font-semibold">{toastMessage}</span>
          <button
            onClick={() => setToastMessage(null)}
            className="text-[#8c909f] hover:text-white ml-2"
          >
            ✕
          </button>
        </div>
      )}

      {/* Fixed Master Sidebar */}
      <Sidebar
        currentPage={currentPage}
        onSelectPage={setCurrentPage}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenSupport={() => setIsSupportOpen(true)}
      />

      {/* Main Workspace Frame */}
      <main className="flex-1 flex flex-col h-screen relative overflow-hidden">
        {/* Fixed Master Header */}
        <Header
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          unreadAlertsCount={alerts.filter((a) => !a.resolved).length}
          onToggleNotifications={() => setIsRerouteConsoleOpen(true)}
          onRefreshData={() => showToast('🔄 관제 데이터 텔레메트리가 실시간 동기화되었습니다.')}
          onSimulateDisruption={handleSimulateDisruption}
          isDisruptionActive={!!activeIncident && !activeIncident.resolved}
        />

        {/* Page Views Switcher */}
        {currentPage === 'dashboard' && (
          <DashboardPage
            nodes={nodes}
            vehicles={filteredVehicles}
            activeIncident={activeIncident}
            alerts={alerts}
            efficiencyStats={efficiencyStats}
            onOpenRerouteConsole={() => setIsRerouteConsoleOpen(true)}
            onSelectVehicle={setSelectedVehicleId}
            selectedVehicleId={selectedVehicleId}
            onNavigatePage={setCurrentPage}
            activeScenarioId={activeScenarioId}
          />
        )}

        {currentPage === 'initial-route' && (
          <InitialRoutePage
            nodes={nodes}
            vehicles={filteredVehicles}
            activeIncident={activeIncident}
            onOpenRerouteConsole={() => setIsRerouteConsoleOpen(true)}
            selectedVehicleId={selectedVehicleId}
            onSelectVehicle={setSelectedVehicleId}
            activeScenarioId={activeScenarioId}
          />
        )}

        {currentPage === 'rerouting' && (
          <ReroutePage
            nodes={nodes}
            vehicles={filteredVehicles}
            activeIncident={activeIncident}
            onOpenRerouteConsole={() => setIsRerouteConsoleOpen(true)}
            onSelectVehicle={setSelectedVehicleId}
            selectedVehicleId={selectedVehicleId}
            activeScenarioId={activeScenarioId}
          />
        )}

        {/* 3-Scenario Re-routing Decision Console Modal */}
        <RerouteConsoleModal
          isOpen={isRerouteConsoleOpen}
          onClose={() => setIsRerouteConsoleOpen(false)}
          scenarios={scenarios}
          onConfirmScenario={handleConfirmScenario}
          affectedVehicleName="트럭 T02"
          affectedSegment="C03 ➔ C07"
          incidentType="사고"
          riskScore={0.92}
        />

        {/* System Settings Modal */}
        <SettingsModal
          isOpen={isSettingsOpen}
          onClose={() => setIsSettingsOpen(false)}
        />

        {/* System Support & Demo Guide Modal */}
        <SupportModal
          isOpen={isSupportOpen}
          onClose={() => setIsSupportOpen(false)}
        />
      </main>
    </div>
  );
}
