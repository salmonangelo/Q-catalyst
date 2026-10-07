import React from 'react';
import { AlertCircle } from 'lucide-react';

export const HeaderBanner: React.FC = () => {
  return (
    <div className="bg-gradient-to-r from-[#C59A45]/15 via-[#FAF9F6] to-[#5B4AE4]/10 border-b border-[#C59A45]/25 py-2 px-4">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between text-xs gap-2">
        <div className="flex items-center gap-2 text-[#7A5C1B] font-semibold tracking-wide">
          <AlertCircle className="w-4 h-4 shrink-0 text-[#C59A45]" />
          <span>DEMO EVALUATION FIXTURE (SYNTHETIC DATA) • IN-SILICO COMPUTATIONAL SCREENING ONLY</span>
        </div>
        <div className="text-[#6C757D] font-medium">
          Simulator: Qiskit Aer Statevector • No Quantum Advantage Claimed
        </div>
      </div>
    </div>
  );
};
