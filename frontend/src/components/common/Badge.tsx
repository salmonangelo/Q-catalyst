import React from 'react';

interface BadgeProps {
  status: string;
}

export const Badge: React.FC<BadgeProps> = ({ status }) => {
  switch (status) {
    case 'PRIORITIZE':
      return (
        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[#EAF8EE] text-[#1E7E34] border border-[#1E7E34]/20">
          PRIORITIZE
        </span>
      );
    case 'PROMISING_BUT_UNCERTAIN':
      return (
        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[#EEF2FF] text-[#4338CA] border border-[#4338CA]/20">
          PROMISING BUT UNCERTAIN
        </span>
      );
    case 'INSUFFICIENT_EVIDENCE':
      return (
        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[#FFFBEB] text-[#B45309] border border-[#B45309]/20">
          INSUFFICIENT EVIDENCE
        </span>
      );
    case 'LOW_PRIORITY':
      return (
        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[#F3F4F6] text-[#6B7280] border border-[#6B7280]/20">
          LOW PRIORITY
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-700">
          {status}
        </span>
      );
  }
};
