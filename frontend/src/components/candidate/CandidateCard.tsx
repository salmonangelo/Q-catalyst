import React from 'react';
import { NavLink } from 'react-router-dom';
import { Atom, ArrowRight } from 'lucide-react';
import { CandidateSummary } from '@/types/api';
import { Badge } from '@/components/common/Badge';

interface CandidateCardProps {
  candidate: CandidateSummary;
  isTop?: boolean;
}

export const CandidateCard: React.FC<CandidateCardProps> = ({ candidate, isTop = false }) => {
  return (
    <div
      className={`qc-card p-6 ${
        isTop ? 'border-[#C59A45] shadow-qc-gold bg-gradient-to-b from-white to-[#FDFBF7]' : ''
      }`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center gap-3">
            <span className="font-cinzel font-bold text-lg text-[#C59A45]">
              #{candidate.rank.toString().padStart(2, '0')}
            </span>
            <span className="font-bold text-lg text-[#121417] tracking-tight">
              {candidate.candidate_id}
            </span>
            <Badge status={candidate.decision_status} />
          </div>
          <div className="text-xs text-[#6C757D] mt-1 flex items-center gap-2">
            <span>
              Mature: <b className="text-[#343A40]">{candidate.mutations}</b>
            </span>
            <span>•</span>
            <span>
              5XJH Crystal: <b className="text-[#343A40]">{candidate.crystal_mutation}</b>
            </span>
            <span>•</span>
            <span className="italic">{candidate.role}</span>
          </div>
        </div>

        <div className="text-right flex sm:flex-col items-center sm:items-end justify-between">
          <div className="text-[11px] text-[#6C757D] uppercase font-semibold">Composite Score</div>
          <div className="text-2xl font-bold text-[#121417] font-sans">
            {candidate.fusion_score.toFixed(4)}
          </div>
        </div>
      </div>

      {/* Grid of Scores */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-[#FAF9F6] border border-[#E3E5E8] rounded-lg p-3 mb-4">
        <div>
          <div className="text-[10px] text-[#6C757D] uppercase font-semibold">AI Fitness</div>
          <div className="text-sm font-bold text-[#343A40]">
            {(candidate.protein_ai_score * 100).toFixed(1)}%
          </div>
        </div>
        <div>
          <div className="text-[10px] text-[#6C757D] uppercase font-semibold">Uncertainty</div>
          <div className="text-sm font-bold text-[#343A40]">
            {(candidate.uncertainty_quality_score * 100).toFixed(1)}%
          </div>
        </div>
        <div>
          <div className="text-[10px] text-[#6C757D] uppercase font-semibold">Proximity</div>
          <div className="text-sm font-bold text-[#343A40]">
            {(candidate.mechanism_proximity_score * 100).toFixed(1)}%
          </div>
        </div>
        <div>
          <div className="text-[10px] text-[#6C757D] uppercase font-semibold">Coverage</div>
          <div className="text-sm font-bold text-[#343A40]">
            {candidate.evidence_coverage} Channels
          </div>
        </div>
      </div>

      {/* Bottom status & inspection link */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
        <div>
          {candidate.quantum_available && candidate.vqe_casci_error !== null ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#C59A45]/10 text-[#9E7A30] font-semibold border border-[#C59A45]/30">
              <Atom className="w-3.5 h-3.5" />
              VQE Error: {candidate.vqe_casci_error.toFixed(4)} Ha
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-gray-100 text-[#6C757D] font-medium border border-gray-200">
              Quantum: NOT SIMULATED (Renormalized)
            </span>
          )}
        </div>

        <NavLink
          to={`/deep-dive?candidate=${encodeURIComponent(candidate.candidate_id)}`}
          className="inline-flex items-center gap-1 font-semibold text-[#C59A45] hover:text-[#9E7A30] transition-colors"
        >
          Inspect Candidate Evidence <ArrowRight className="w-4 h-4" />
        </NavLink>
      </div>
    </div>
  );
};
