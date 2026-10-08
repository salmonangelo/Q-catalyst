import React from 'react';
import { CheckCircle2, AlertTriangle, Info, HelpCircle } from 'lucide-react';
import { CandidateExplanation } from '@/types/api';

interface ExplainabilityBoxProps {
  explanation: CandidateExplanation;
}

export const ExplainabilityBox: React.FC<ExplainabilityBoxProps> = ({ explanation }) => {
  return (
    <div className="bg-[#0D1222]/90 border border-[#F59E0B]/30 rounded-2xl p-6 shadow-qc-md backdrop-blur-md">
      <div className="font-cinzel font-bold text-sm text-[#FDE047] tracking-wider uppercase mb-3 flex items-center gap-2">
        <Info className="w-4 h-4 text-[#F59E0B]" />
        Deterministic Multimodal Explainability
      </div>

      <p className="text-sm text-[#CBD5E1] leading-relaxed mb-6 font-medium">
        {explanation.summary}
      </p>

      <div className="space-y-4 text-xs">
        {/* Supporting Evidence */}
        {explanation.positive_factors.length > 0 && (
          <div className="bg-[#080C18]/60 p-3.5 rounded-xl border border-[#10B981]/25">
            <div className="font-bold text-[#34D399] uppercase tracking-wide mb-2 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-[#10B981]" /> Supporting Evidence
            </div>
            <ul className="space-y-1.5 pl-5 list-disc text-[#CBD5E1]">
              {explanation.positive_factors.map((factor, i) => (
                <li key={i}>{factor}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Cautions */}
        {explanation.negative_factors.length > 0 && (
          <div className="bg-[#080C18]/60 p-3.5 rounded-xl border border-[#DC2626]/25">
            <div className="font-bold text-[#EF4444] uppercase tracking-wide mb-2 flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-[#DC2626]" /> Cautionary Signals
            </div>
            <ul className="space-y-1.5 pl-5 list-disc text-[#CBD5E1]">
              {explanation.negative_factors.map((factor, i) => (
                <li key={i}>{factor}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Missing / Uncomputed Channels */}
        {explanation.missing_evidence.length > 0 && (
          <div className="bg-[#080C18]/60 p-3.5 rounded-xl border border-[#64748B]/25">
            <div className="font-bold text-[#94A3B8] uppercase tracking-wide mb-2 flex items-center gap-1.5">
              <HelpCircle className="w-4 h-4 text-[#64748B]" /> Uncomputed Channels (Dynamic Renormalization)
            </div>
            <ul className="space-y-1.5 pl-5 list-disc text-[#94A3B8]">
              {explanation.missing_evidence.map((factor, i) => (
                <li key={i}>{factor}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Limitations */}
        {explanation.limitations.length > 0 && (
          <div className="bg-[#080C18]/60 p-3.5 rounded-xl border border-[#F59E0B]/25">
            <div className="font-bold text-[#FDE047] uppercase tracking-wide mb-2 flex items-center gap-1.5">
              <Info className="w-4 h-4 text-[#F59E0B]" /> Scientific Limitations
            </div>
            <ul className="space-y-1.5 pl-5 list-disc text-[#FDE047]/90">
              {explanation.limitations.map((limit, i) => (
                <li key={i}>{limit}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};
