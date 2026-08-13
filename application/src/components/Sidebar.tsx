import React from 'react';
import { PageId } from '../types';

interface SidebarProps {
  currentPage: PageId;
  onSelectPage: (page: PageId) => void;
  onOpenSettings: () => void;
  onOpenSupport: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onSelectPage,
  onOpenSettings,
  onOpenSupport,
}) => {
  const navItems: { id: PageId; label: string; icon: string }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: 'dashboard' },
    { id: 'initial-route', label: 'Initial Route', icon: 'route' },
    { id: 'rerouting', label: 'Re-routing', icon: 'rebase_edit' },
  ];

  return (
    <nav className="w-[260px] h-screen sticky left-0 top-0 bg-[#122131] shadow-md flex flex-col py-6 z-50 flex-shrink-0 border-r border-[#424754]/30 select-none">
      {/* Brand / Header */}
      <div className="px-4 mb-8 flex flex-col gap-1">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-[#1c2b3c] border border-[#424754]/30 text-[#adc6ff] font-bold text-xl shadow-inner">
            CT
          </div>
          <div className="flex flex-col">
            <span className="text-xl font-bold text-[#adc6ff] tracking-tight">
              Control Tower
            </span>
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#c2c6d6]">
              AI Fleet Manager
            </span>
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 flex flex-col gap-2 px-3">
        {navItems.map((item) => {
          const isActive = currentPage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectPage(item.id)}
              className={`flex items-center gap-3 px-4 py-3 rounded-r-full text-left transition-all duration-200 ${
                isActive
                  ? 'text-[#4edea3] border-l-2 border-[#4edea3] font-semibold bg-[#00a572]/15 shadow-sm'
                  : 'text-[#c2c6d6] border-l-2 border-transparent font-medium hover:bg-[#2c3a4c]/30 hover:text-[#d4e4fa]'
              }`}
            >
              <span
                className="material-symbols-outlined text-[20px]"
                style={{ fontVariationSettings: isActive ? "'FILL' 1" : "'FILL' 0" }}
              >
                {item.icon}
              </span>
              <span className="text-sm">{item.label}</span>
            </button>
          );
        })}
      </div>

      {/* Footer Navigation & Profile */}
      <div className="mt-auto flex flex-col gap-2 px-3 border-t border-[#424754]/30 pt-4">
        <button
          onClick={onOpenSettings}
          className="flex items-center gap-3 px-4 py-2.5 border-l-2 border-transparent text-[#c2c6d6] font-medium hover:bg-[#2c3a4c]/20 hover:text-[#d4e4fa] transition-colors rounded-r-full text-left"
        >
          <span className="material-symbols-outlined text-[20px]">settings</span>
          <span className="text-sm">Settings</span>
        </button>
        <button
          onClick={onOpenSupport}
          className="flex items-center gap-3 px-4 py-2.5 border-l-2 border-transparent text-[#c2c6d6] font-medium hover:bg-[#2c3a4c]/20 hover:text-[#d4e4fa] transition-colors rounded-r-full text-left"
        >
          <span className="material-symbols-outlined text-[20px]">help</span>
          <span className="text-sm">Support</span>
        </button>

        <div className="mt-3 px-4 pt-2 flex items-center gap-3 border-t border-[#424754]/20">
          <div className="w-8 h-8 rounded-full border border-[#424754] overflow-hidden bg-[#273647] flex items-center justify-center shrink-0">
            <span className="material-symbols-outlined text-[#adc6ff] text-lg">person</span>
          </div>
          <div className="text-xs font-medium text-[#c2c6d6] truncate">
            Opr: J. Doe
          </div>
        </div>
      </div>
    </nav>
  );
};
