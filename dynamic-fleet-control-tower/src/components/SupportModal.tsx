import React from 'react';

interface SupportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SupportModal: React.FC<SupportModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-[#051424]/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="glass-panel w-full max-w-lg rounded-2xl p-6 shadow-2xl border border-[#424754]/40 flex flex-col gap-6">
        <div className="flex justify-between items-center border-b border-[#424754]/30 pb-4">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[#ffb95f]">help</span>
            <h2 className="text-lg font-bold text-[#d4e4fa]">운영 지원 및 시스템 가이드</h2>
          </div>
          <button onClick={onClose} className="text-[#8c909f] hover:text-white">
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        <div className="space-y-3 text-xs text-[#c2c6d6]">
          <div className="p-3 bg-[#122131] rounded-lg border border-[#424754]/30">
            <div className="font-bold text-[#adc6ff] mb-1">💡 3대 재경로 대응 시나리오 안내</div>
            <p className="leading-relaxed">
              사고 발생 시 <strong>Option A(경로 우회)</strong>, <strong>Option B(방문 순서 변경)</strong>, <strong>Option C(유휴 트럭 업무 승계)</strong>의 거리/시간/비용 지표를 비교하여 최적안을 클릭 한 번으로 확정할 수 있습니다.
            </p>
          </div>

          <div className="p-3 bg-[#122131] rounded-lg border border-[#424754]/30">
            <div className="font-bold text-[#4edea3] mb-1">🛠️ 시연 워크플로우 (Demo Guide)</div>
            <ol className="list-decimal list-inside space-y-1 text-[#c2c6d6]">
              <li>Initial Route 페이지에서 최적화 목표 설정 후 [최적화 실행] 클릭</li>
              <li>상단 [돌발상황 발생 시뮬레이션] 버튼을 눌러 C03-C07 사고 유발</li>
              <li>Risk Analysis 페이지에서 영향받는 차량(T02) 및 위험 점수(0.92) 확인</li>
              <li>Re-routing 콘솔에서 Option A, B, C 비교 후 [전략 확정 및 적용]</li>
            </ol>
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-[#4d8eff] text-[#00285d] font-bold rounded-lg text-xs hover:bg-[#d8e2ff]"
          >
            확인
          </button>
        </div>
      </div>
    </div>
  );
};
