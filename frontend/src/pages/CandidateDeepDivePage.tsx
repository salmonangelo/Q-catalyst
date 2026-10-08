import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '@/api/client';
import { CandidateDetailResponse } from '@/types/api';
import { EvidenceRadar } from '@/components/charts/EvidenceRadar';
import { ExplainabilityBox } from '@/components/candidate/ExplainabilityBox';
import { MetricCard } from '@/components/common/MetricCard';
import { Badge } from '@/components/common/Badge';

export const CandidateDeepDivePage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [candidatesList, setCandidatesList] = useState<string[]>([]);
  const [detail, setDetail] = useState<CandidateDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const currentCand = searchParams.get('candidate') || 'VAR_W132H';

  useEffect(() => {
    api.getCandidates()
      .then((res) => {
        const ids = res.candidates.map((c) => c.candidate_id);
        setCandidatesList(ids);
        const targetId = ids.includes(currentCand) ? currentCand : ids[0];
        return api.getCandidateDetail(targetId);
      })
      .then((det) => setDetail(det))
      .catch((err) => console.error('Failed to load deep-dive data:', err))
      .finally(() => setLoading(false));
  }, [currentCand]);

  const handleSelectCandidate = (id: string) => {
    setSearchParams({ candidate: id });
  };

  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-cinzel font-bold text-[#F59E0B] tracking-widest uppercase mb-1">
          Detailed Feature Analysis
        </div>
        <h1 className="text-3xl font-extrabold text-[#F8FAFC] tracking-tight">
          Candidate Evidence Deep Dive
        </h1>
        <p className="text-sm text-[#94A3B8] mt-1">
          Granular inspection of multimodal feature signals, radar profiles, residue coordinates, and deterministic explainability.
        </p>
      </div>

      {/* Candidate Selector */}
      <div className="bg-[#0D1222]/90 p-4 rounded-xl border border-[#F59E0B]/20 shadow-qc-md backdrop-blur-md flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-[#F8FAFC]">Select Variant:</span>
          <select
            value={currentCand}
            onChange={(e) => handleSelectCandidate(e.target.value)}
            className="text-xs bg-[#070913] border border-[#CBD5E1]/20 rounded-lg px-3 py-1.5 text-[#FDE047] font-bold focus:outline-none focus:ring-1 focus:ring-[#F59E0B]"
          >
            {candidatesList.map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
        </div>

        {detail && (
          <div className="flex items-center gap-3">
            <span className="text-xs text-[#94A3B8]">
              Rank: <b className="text-[#FDE047] font-cinzel text-sm">#{detail.candidate.rank}</b>
            </span>
            <Badge status={detail.candidate.decision_status} />
          </div>
        )}
      </div>

      {detail ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column: Radar Chart & Metrics */}
          <div className="space-y-6">
            <div className="qc-card p-6">
              <div className="text-xs font-cinzel font-bold text-[#F59E0B] tracking-wider uppercase mb-2">
                Multimodal Profile
              </div>
              <h3 className="text-lg font-bold text-[#F8FAFC] mb-4">6-Axis Evidence Radar</h3>
              <EvidenceRadar
                scores={detail.radar_scores}
                candidateId={detail.candidate.candidate_id}
                quantumAvailable={detail.candidate.quantum_available}
              />
              {!detail.candidate.quantum_available && (
                <div className="text-xs text-[#94A3B8] bg-[#080C18] p-3 rounded-lg border border-[#334155] mt-4 leading-relaxed">
                  ⚛️ <b className="text-[#FDE047]">Quantum Channel:</b> Uncomputed under the representative simulation policy. Missing evidence was dynamically renormalized in the decision engine without penalty.
                </div>
              )}
            </div>

            {/* Residue Mapping & Structural Metrics */}
            <div className="qc-card p-6">
              <div className="text-xs font-cinzel font-bold text-[#F59E0B] tracking-wider uppercase mb-3">
                Residue Numbering & Mechanism Resolution
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <MetricCard
                  label="Mature Sequence"
                  value={detail.mature_numbering}
                  subtext="IsPETase 1-263"
                />
                <MetricCard
                  label="5XJH Crystal Residue"
                  value={detail.crystal_numbering}
                  subtext="PDB coordinate"
                  variant="gold"
                />
                <MetricCard
                  label="Active-Site Distance"
                  value={`${detail.active_site_distance_angstrom?.toFixed(2) || '—'} Å`}
                  subtext="To catalytic triad"
                  variant="ruby"
                />
              </div>
            </div>
          </div>

          {/* Right Column: Explainability & Cautions */}
          <div className="space-y-6">
            <ExplainabilityBox explanation={detail.explanation} />
          </div>
        </div>
      ) : (
        <div className="py-20 text-center text-sm text-[#94A3B8]">
          Loading candidate details...
        </div>
      )}
    </div>
  );
};
