import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '@/api/client';
import { CandidateDetailResponse, CandidatesListResponse } from '@/types/api';
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
        <h1 className="text-3xl font-extrabold text-[#121417] tracking-tight">
          Candidate Evidence Deep Dive
        </h1>
        <p className="text-sm text-[#6C757D] mt-1">
          Granular inspection of multimodal feature signals, radar profiles, residue coordinates, and deterministic explainability.
        </p>
      </div>

      {/* Candidate Selector */}
      <div className="bg-white p-4 rounded-xl border border-[#E3E5E8] shadow-qc-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-[#121417]">Select Variant:</span>
          <select
            value={currentCand}
            onChange={(e) => handleSelectCandidate(e.target.value)}
            className="text-xs bg-[#FAF9F6] border border-[#E3E5E8] rounded-lg px-3 py-1.5 text-[#121417] font-bold focus:outline-none focus:ring-1 focus:ring-[#C59A45]"
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
            <span className="text-xs text-[#6C757D]">
              Rank: <b className="text-[#121417]">#{detail.candidate.rank}</b>
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
              <div className="text-xs font-cinzel font-bold text-[#C59A45] tracking-wider uppercase mb-2">
                Multimodal Profile
              </div>
              <h3 className="text-lg font-bold text-[#121417] mb-4">6-Axis Evidence Radar</h3>
              <EvidenceRadar
                scores={detail.radar_scores}
                candidateId={detail.candidate.candidate_id}
                quantumAvailable={detail.candidate.quantum_available}
              />
              {!detail.candidate.quantum_available && (
                <div className="text-xs text-[#6C757D] bg-[#FAF9F6] p-3 rounded-lg border border-[#E3E5E8] mt-4">
                  ⚛️ <b>Quantum Channel:</b> Uncomputed under the representative simulation policy. Missing evidence was dynamically renormalized in the decision engine.
                </div>
              )}
            </div>

            {/* Residue Mapping & Structural Metrics */}
            <div className="qc-card p-6">
              <div className="text-xs font-cinzel font-bold text-[#121417] tracking-wider uppercase mb-3">
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
        <div className="py-20 text-center text-sm text-[#6C757D]">
          Loading candidate details...
        </div>
      )}
    </div>
  );
};
