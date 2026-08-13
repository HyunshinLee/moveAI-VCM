import React from 'react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-[#051424]/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="glass-panel w-full max-w-lg rounded-2xl p-6 shadow-2xl border border-[#424754]/40 flex flex-col gap-6">
        <div className="flex justify-between items-center border-b border-[#424754]/30 pb-4">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[#adc6ff]">settings</span>
            <h2 className="text-lg font-bold text-[#d4e4fa]">Control Tower 시스템 설정</h2>
          </div>
          <button onClick={onClose} className="text-[#8c909f] hover:text-white">
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        <div className="space-y-4 text-xs text-[#c2c6d6]">
          <div className="flex justify-between items-center p-3 bg-[#122131] rounded-lg border border-[#424754]/30">
            <div>
              <div className="font-bold text-[#d4e4fa]">자동 재경로 감지 주기</div>
              <div className="text-[11px] text-[#8c909f]">실시간 돌발상황 알림 수집 간격</div>
            </div>
            <select className="bg-[#1c2b3c] border border-[#424754] rounded px-2 py-1 text-xs text-[#d4e4fa]">
              <option>10초 (실시간)</option>
              <option>30초</option>
              <option>1분</option>
            </select>
          </div>

          <div className="flex justify-between items-center p-3 bg-[#122131] rounded-lg border border-[#424754]/30">
            <div>
              <div className="font-bold text-[#d4e4fa]">ALNS 최적화 엔진 모드</div>
              <div className="text-[11px] text-[#8c909f]">Adaptive Large Neighborhood Search</div>
            </div>
            <span className="text-[#4edea3] font-mono font-bold">Fast Heuristic (v2.4)</span>
          </div>

          <div className="flex justify-between items-center p-3 bg-[#122131] rounded-lg border border-[#424754]/30">
            <div>
              <div className="font-bold text-[#d4e4fa]">외부 교통 API 연동</div>
              <div className="text-[11px] text-[#8c909f]">서울 TOPIS / 경찰청 소통정보 / 고속도로 API</div>
            </div>
            <span className="bg-[#00a572]/20 text-[#4edea3] px-2 py-0.5 rounded text-[10px] font-bold border border-[#00a572]/40">
              CONNECTED
            </span>
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-[#4d8eff] text-[#00285d] font-bold rounded-lg text-xs hover:bg-[#d8e2ff]"
          >
            확인 및 닫기
          </button>
        </div>
      </div>
    </div>
  );
};
