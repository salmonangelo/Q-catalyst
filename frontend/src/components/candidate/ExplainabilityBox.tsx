import React from 'react';
import { CheckCircle2, AlertTriangle, Info, HelpCircle } from 'lucide-react';
import { CandidateExplanation } from '@/types/api';

interface ExplainabilityBoxProps {
  explanation: CandidateExplanation;
}

export const ExplainabilityBox: React.FC<ExplainabilityBoxProps> = ({ explanation }) => {
  return (
    <div className="bg-[#FDFBF7] border border-[#C59A45]/30 rounded-xl p-6 shadow-qc-sm">
      <div className="font-cinzel font-bold text-sm text-[#9E7A30] tracking-wider uppercase mb-3 flex items-center gap-2">
        <Info className="w-4 h-4 text-[#C59A45]" />
        Deterministic Multimodal Explainability
      </div>

      <p className="text-sm text-[#121417] leading-relaxed mb-6 font-medium">
        {explanation.summary}
      </p>

      <div className="space-y-4 text-xs">
        {/* Supporting Evidence */}
        {explanation.positive_factors.length > 0 && (
          <div>
            <div className="font-bold text-[#1E7E34] uppercase tracking-wide mb-2 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" /> Supporting Evidence
            </div>
            <ul className="space-y-1.5 pl-5 list-disc text-[#343A40]">
              {explanation.positive_factors.map((factor, i) => (
                <li key={i}>{factor}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Cautions */}
        {explanation.negative_factors.length > 0 && (
          <div>
            <div className="font-bold text-[#DC3545] uppercase tracking-wide mb-2 flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4" /> Cautionary Signals
            </div>
            <ul className="space-y-1.5 pl-5 list-disc text-[#343A40]">
              {explanation.negative_factors.map((factor, i) => (
                <li key={i}>{factor}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Missing / Uncomputed Channels */}
        {explanation.missing_evidence.length > 0 && (
          <div>
            <div className="font-bold text-[#6C757D] uppercase tracking-wide mb-2 flex items-center gap-1.5">
              <HelpCircle className="w-4 h-4" /> Uncomputed Channels (Dynamic Renormalization)
            </div>
            <ul className="space-y-1.5 pl-5 list-disc text-[#6C757D]">
              {explanation.missing_evidence.map((factor, i) => (
                <li key={i}>{factor}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Limitations */}
        {explanation.limitations.length > 0 && (
          <div>
            <div className="font-bold text-[#9E7A30] uppercase tracking-wide mb-2 flex items-center gap-1.5">
              <Info className="w-4 h-4" /> Scientific Limitations
            </div>
            <ul className="space-y-1.5 pl-5 list-disc text-[#7A5C1B]">
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
