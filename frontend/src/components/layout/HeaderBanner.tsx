import React from 'react';
import { AlertCircle, Cpu } from 'lucide-react';

export const HeaderBanner: React.FC = () => {
  return (
    <div className="bg-gradient-to-r from-[#DC2626]/20 via-[#0A0E1A] to-[#F59E0B]/20 border-b border-[#F59E0B]/30 py-2 px-4 backdrop-blur-md">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between text-xs gap-2">
        <div className="flex items-center gap-2 text-[#FDE047] font-semibold tracking-wide">
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#F59E0B] opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-[#F59E0B]"></span>
          </span>
          <AlertCircle className="w-4 h-4 shrink-0 text-[#F59E0B]" />
          <span>DEMO EVALUATION FIXTURE (SYNTHETIC DATA) • IN-SILICO COMPUTATIONAL SCREENING ONLY</span>
        </div>
        <div className="flex items-center gap-2 text-[#94A3B8] font-medium">
          <Cpu className="w-3.5 h-3.5 text-[#38BDF8]" />
          <span>Simulator: Qiskit Aer Statevector • No Quantum Advantage Claimed</span>
        </div>
      </div>
    </div>
  );
};
