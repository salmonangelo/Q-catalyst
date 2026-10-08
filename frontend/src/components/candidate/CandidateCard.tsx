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
        isTop 
          ? 'border-[#F59E0B]/70 shadow-qc-gold bg-gradient-to-r from-[#F59E0B]/10 via-[#0D1222] to-[#0A0E1A]' 
          : 'hover:border-[#F59E0B]/40'
      }`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center gap-3">
            <span className="font-cinzel font-bold text-lg text-[#FDE047]">
              #{candidate.rank.toString().padStart(2, '0')}
            </span>
            <span className="font-bold text-lg text-[#F8FAFC] tracking-tight">
              {candidate.candidate_id}
            </span>
            <Badge status={candidate.decision_status} />
          </div>
          <div className="text-xs text-[#94A3B8] mt-1.5 flex flex-wrap items-center gap-2">
            <span>
              Mature: <b className="text-[#F8FAFC] font-mono">{candidate.mutations}</b>
            </span>
            <span className="text-[#64748B]">•</span>
            <span>
              5XJH Crystal: <b className="text-[#FDE047] font-mono">{candidate.crystal_mutation}</b>
            </span>
            <span className="text-[#64748B]">•</span>
            <span className="italic text-[#CBD5E1]">{candidate.role}</span>
          </div>
        </div>

        <div className="text-right flex sm:flex-col items-center sm:items-end justify-between">
          <div className="text-[11px] text-[#94A3B8] uppercase font-semibold tracking-wider">Composite Score</div>
          <div className="text-2xl font-bold text-[#FDE047] font-sans">
            {candidate.fusion_score.toFixed(4)}
          </div>
        </div>
      </div>

      {/* Grid of Scores */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-[#080C18]/80 border border-[#CBD5E1]/10 rounded-xl p-3 mb-4">
        <div>
          <div className="text-[10px] text-[#94A3B8] uppercase font-semibold">AI Fitness</div>
          <div className="text-sm font-bold text-[#F8FAFC]">
            {(candidate.protein_ai_score * 100).toFixed(1)}%
          </div>
        </div>
        <div>
          <div className="text-[10px] text-[#94A3B8] uppercase font-semibold">Uncertainty</div>
          <div className="text-sm font-bold text-[#38BDF8]">
            {(candidate.uncertainty_quality_score * 100).toFixed(1)}%
          </div>
        </div>
        <div>
          <div className="text-[10px] text-[#94A3B8] uppercase font-semibold">Proximity</div>
          <div className="text-sm font-bold text-[#EF4444]">
            {(candidate.mechanism_proximity_score * 100).toFixed(1)}%
          </div>
        </div>
        <div>
          <div className="text-[10px] text-[#94A3B8] uppercase font-semibold">Coverage</div>
          <div className="text-sm font-bold text-[#34D399]">
            {candidate.evidence_coverage} Channels
          </div>
        </div>
      </div>

      {/* Bottom status & inspection link */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
        <div>
          {candidate.quantum_available && candidate.vqe_casci_error !== null ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#F59E0B]/15 text-[#FDE047] font-semibold border border-[#F59E0B]/40 shadow-sm">
              <Atom className="w-3.5 h-3.5 text-[#F59E0B]" />
              VQE Error: {candidate.vqe_casci_error.toFixed(4)} Ha
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#1E293B]/60 text-[#94A3B8] font-medium border border-[#334155]">
              Quantum: NOT SIMULATED (Renormalized)
            </span>
          )}
        </div>

        <NavLink
          to={`/deep-dive?candidate=${encodeURIComponent(candidate.candidate_id)}`}
          className="inline-flex items-center gap-1 font-semibold text-[#F59E0B] hover:text-[#FDE047] transition-colors"
        >
          Inspect Candidate Evidence <ArrowRight className="w-4 h-4" />
        </NavLink>
      </div>
    </div>
  );
};
