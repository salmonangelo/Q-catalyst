import React from 'react';

interface BadgeProps {
  status: string;
}

export const Badge: React.FC<BadgeProps> = ({ status }) => {
  switch (status) {
    case 'PRIORITIZE':
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#10B981]/15 text-[#34D399] border border-[#10B981]/40 shadow-sm">
          <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-pulse" />
          PRIORITIZE
        </span>
      );
    case 'PROMISING_BUT_UNCERTAIN':
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#06B6D4]/15 text-[#38BDF8] border border-[#06B6D4]/40">
          <span className="w-1.5 h-1.5 rounded-full bg-[#06B6D4]" />
          PROMISING BUT UNCERTAIN
        </span>
      );
    case 'INSUFFICIENT_EVIDENCE':
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#F59E0B]/15 text-[#FBBF24] border border-[#F59E0B]/40">
          <span className="w-1.5 h-1.5 rounded-full bg-[#F59E0B]" />
          INSUFFICIENT EVIDENCE
        </span>
      );
    case 'LOW_PRIORITY':
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#334155]/40 text-[#94A3B8] border border-[#475569]/40">
          <span className="w-1.5 h-1.5 rounded-full bg-[#64748B]" />
          LOW PRIORITY
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-[#1E293B] text-[#CBD5E1] border border-[#334155]">
          {status}
        </span>
      );
  }
};
