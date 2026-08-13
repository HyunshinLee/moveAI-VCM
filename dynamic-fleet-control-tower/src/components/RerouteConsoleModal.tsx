import React, { useState } from 'react';
import { RerouteScenario, ScenarioOptionId } from '../types';

interface RerouteConsoleModalProps {
  isOpen: boolean;
  onClose: () => void;
  scenarios: RerouteScenario[];
  onConfirmScenario: (selectedScenarioId: ScenarioOptionId) => void;
  affectedVehicleName?: string; // "Truck T02"
  affectedSegment?: string; // "C03 ➔ C07"
  incidentType?: string; // "사고"
  riskScore?: number; // 0.92
}

export const RerouteConsoleModal: React.FC<RerouteConsoleModalProps> = ({
  isOpen,
  onClose,
  scenarios,
  onConfirmScenario,
  affectedVehicleName = '트럭 T02',
  affectedSegment = 'C03 ➔ C07',
  incidentType = '사고',
  riskScore = 0.92,
}) => {
  const [selectedId, setSelectedId] = useState<ScenarioOptionId>('OPTION_A');

  if (!isOpen) return null;

  const selectedScenario = scenarios.find((s) => s.id === selectedId) || scenarios[0];

  const handleApply = () => {
    onConfirmScenario(selectedId);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-[#051424]/85 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto select-none animate-fadeIn">
      {/* Modal Container */}
      <div className="modal-glass w-full max-w-4xl rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-[#424754]/40 my-8">
        {/* Modal Header (Alert / Danger Banner Style) */}
        <div className="bg-[#93000a]/20 border-b border-[#93000a]/50 p-6 flex items-start gap-4 relative overflow-hidden">
          {/* Subtle pulsing background glow */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-[#ffb4ab]/10 rounded-full blur-3xl -mr-20 -mt-20 animate-pulse pointer-events-none" />

          <div className="w-12 h-12 rounded-full bg-[#93000a] flex items-center justify-center flex-shrink-0 z-10 border border-[#ffb4ab]/30 shadow-lg text-[#ffdad6]">
            <span
              className="material-symbols-outlined text-3xl"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              warning
            </span>
          </div>

          <div className="z-10 flex-1">
            <h2 className="text-2xl font-bold text-[#ffdad6] tracking-tight">
              🚨 교통 돌발 상황 감지 - 재경로 전략 선택
            </h2>
            <p className="text-sm text-[#ffdad6]/80 mt-0.5">
              (교통 돌발 상황 감지 - 실시간 대응 전략 선택)
            </p>

            <div className="mt-4 flex flex-wrap items-center gap-2.5 text-xs font-mono">
              <span className="bg-[#273647] text-[#d4e4fa] px-2.5 py-1 rounded border border-[#424754]/40 flex items-center gap-1.5 shadow-sm">
                <span className="material-symbols-outlined text-sm text-[#8c909f]">
                  local_shipping
                </span>
                {affectedVehicleName}
              </span>
              <span className="text-[#8c909f]">|</span>
              <span className="bg-[#273647] text-[#d4e4fa] px-2.5 py-1 rounded border border-[#424754]/40 flex items-center gap-1.5 shadow-sm">
                <span className="material-symbols-outlined text-sm text-[#8c909f]">
                  route
                </span>
                구간: {affectedSegment}
              </span>
              <span className="text-[#8c909f]">|</span>
              <span className="bg-[#93000a]/40 text-[#ffb4ab] px-2.5 py-1 rounded border border-[#ffb4ab]/30 flex items-center gap-1.5 font-bold shadow-sm">
                <span className="material-symbols-outlined text-sm">car_crash</span>
                돌발 상황: {incidentType}
              </span>
              <span className="text-[#8c909f]">|</span>
              <span className="bg-[#93000a] text-[#ffdad6] px-2.5 py-1 rounded flex items-center gap-1.5 font-bold shadow-sm">
                고위험 {riskScore}
              </span>
            </div>
          </div>
        </div>

        {/* Modal Body: 3 Scenario Cards */}
        <div className="p-6 bg-[#051424]/60 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <p className="text-xs font-bold uppercase tracking-wider text-[#c2c6d6]">
              AI 추천 대응 전략 (3가지 시나리오 비교)
            </p>
            <span className="text-xs text-[#8c909f]">
              클릭하여 최적화안 선택 후 확정하세요
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {scenarios.map((scenario) => {
              const isSelected = scenario.id === selectedId;

              return (
                <div
                  key={scenario.id}
                  onClick={() => setSelectedId(scenario.id)}
                  className={`relative rounded-xl p-5 cursor-pointer transition-all duration-200 flex flex-col h-full group ${
                    isSelected
                      ? 'bg-[#00a572]/10 border-2 border-[#4edea3] shadow-[0_0_20px_rgba(78,222,163,0.2)]'
                      : 'bg-[#122131] border border-[#424754]/40 hover:border-[#adc6ff]/50 hover:bg-[#1c2b3c]'
                  }`}
                >
                  {/* Selected Badge */}
                  <div className="absolute top-4 right-4">
                    {isSelected ? (
                      <span
                        className="material-symbols-outlined text-[#4edea3] text-2xl"
                        style={{ fontVariationSettings: "'FILL' 1" }}
                      >
                        check_circle
                      </span>
                    ) : (
                      <span className="material-symbols-outlined text-[#424754] text-2xl group-hover:text-[#adc6ff]">
                        radio_button_unchecked
                      </span>
                    )}
                  </div>

                  <h4
                    className={`text-lg font-bold mb-0.5 ${
                      isSelected ? 'text-[#4edea3]' : 'text-[#adc6ff]'
                    }`}
                  >
                    {scenario.optionTitle}
                  </h4>
                  <h5 className="text-base font-bold text-[#d4e4fa] mb-1">
                    {scenario.koreanName}{' '}
                    <span className="text-xs font-normal text-[#c2c6d6]">
                      {scenario.subtitle}
                    </span>
                  </h5>

                  <p className="text-xs text-[#c2c6d6] mb-4 mt-1 leading-relaxed flex-1">
                    {scenario.description}
                  </p>

                  <div className="mt-auto pt-4 border-t border-[#424754]/30 grid grid-cols-2 gap-2 text-xs">
                    <div className="bg-[#051424]/60 rounded p-2 border border-[#424754]/20">
                      <div className="text-[10px] text-[#8c909f] mb-0.5 flex items-center gap-1 font-mono">
                        <span className="material-symbols-outlined text-[13px]">
                          straighten
                        </span>
                        거리
                      </div>
                      <div className="font-mono font-bold text-[#ffb4ab]">
                        {scenario.distanceKmChange}
                      </div>
                    </div>

                    <div className="bg-[#051424]/60 rounded p-2 border border-[#424754]/20">
                      <div className="text-[10px] text-[#8c909f] mb-0.5 flex items-center gap-1 font-mono">
                        <span className="material-symbols-outlined text-[13px]">
                          schedule
                        </span>
                        시간
                      </div>
                      <div className="font-mono font-medium text-[#d4e4fa]">
                        {scenario.travelTimeMin} 분
                      </div>
                    </div>

                    <div
                      className={`rounded p-2 col-span-2 border ${
                        isSelected
                          ? 'bg-[#00a572]/15 border-[#4edea3]/30 text-[#4edea3]'
                          : 'bg-[#051424]/60 border-[#424754]/20 text-[#adc6ff]'
                      }`}
                    >
                      <div className="text-[10px] opacity-80 mb-0.5 flex items-center gap-1 font-mono">
                        <span className="material-symbols-outlined text-[13px]">
                          timer_off
                        </span>
                        지연 단축
                      </div>
                      <div className="font-mono font-bold">
                        {scenario.delayReductionMin} 분 단축
                      </div>
                    </div>

                    {scenario.tardinessDescription && (
                      <div className="bg-[#ca8100]/20 rounded p-2 col-span-2 border border-[#ca8100]/40 text-[#ffb95f]">
                        <div className="text-[10px] mb-0.5 flex items-center gap-1 font-mono">
                          <span className="material-symbols-outlined text-[13px]">
                            warning
                          </span>
                          SLA 영향
                        </div>
                        <div className="font-mono font-medium">
                          {scenario.tardinessDescription}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Modal Footer & Dynamic Summary Bar */}
        <div className="bg-[#1c2b3c] p-6 border-t border-[#424754]/30 flex flex-col gap-4">
          {/* Selected Summary Bar */}
          <div className="bg-[#010f1f] border border-[#424754]/40 rounded-xl p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-inner">
            <div className="flex items-center gap-2">
              <span
                className="material-symbols-outlined text-[#4edea3]"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                psychology
              </span>
              <span className="text-sm font-semibold text-[#d4e4fa]">
                선택됨: 시나리오 {selectedScenario.optionTitle.replace('Option ', '')} (
                {selectedScenario.koreanName})
              </span>
            </div>

            <div className="flex items-center gap-4 text-xs font-mono">
              <span className="text-[#4edea3] flex items-center gap-1 font-bold">
                <span className="material-symbols-outlined text-sm">
                  trending_down
                </span>
                예상 단축 시간: {Math.abs(selectedScenario.delayReductionMin)} 분
              </span>
              <span className="text-[#424754]">|</span>
              <span className="text-[#ffb4ab] flex items-center gap-1 font-bold">
                <span className="material-symbols-outlined text-sm">payments</span>
                추가 비용: +${selectedScenario.addedCostUsd.toFixed(2)}
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 mt-1">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 rounded-lg border border-[#424754] text-[#c2c6d6] font-medium hover:bg-[#122131] hover:text-[#d4e4fa] transition-colors text-sm"
            >
              취소 / 기존 경로 유지
            </button>
            <button
              type="button"
              onClick={handleApply}
              className="px-6 py-2.5 rounded-lg bg-[#4d8eff] text-[#00285d] font-bold hover:bg-[#d8e2ff] transition-all shadow-lg shadow-[#4d8eff]/20 flex items-center gap-2 text-sm"
            >
              <span className="material-symbols-outlined text-lg">send</span>
              전략 확정 및 적용
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
