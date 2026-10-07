import React, { useEffect, useState } from 'react';
import { api } from '@/api/client';
import { CandidatesListResponse, CandidateSummary } from '@/types/api';
import { CandidateCard } from '@/components/candidate/CandidateCard';
import { Filter, ArrowUpDown } from 'lucide-react';

export const CandidateTriagePage: React.FC = () => {
  const [candidates, setCandidates] = useState<CandidateSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [sortBy, setSortBy] = useState<'rank' | 'score'>('rank');

  useEffect(() => {
    api.getCandidates()
      .then((data) => setCandidates(data.candidates))
      .catch((err) => console.error('Failed to load candidates:', err))
      .finally(() => setLoading(false));
  }, []);

  const filtered = candidates
    .filter((c) => filterStatus === 'ALL' || c.decision_status === filterStatus)
    .sort((a, b) => (sortBy === 'rank' ? a.rank - b.rank : b.fusion_score - a.fusion_score));

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold text-[#121417] tracking-tight">
          Candidate Triage Matrix
        </h1>
        <p className="text-sm text-[#6C757D] mt-1">
          Multimodal candidate rankings integrating Protein AI, conformal uncertainty, active-site distance, and quantum simulation.
        </p>
      </div>

      {/* Filter and Sort Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-[#E3E5E8] shadow-qc-sm">
        <div className="flex items-center gap-3">
          <Filter className="w-4 h-4 text-[#6C757D]" />
          <span className="text-xs font-semibold text-[#121417]">Filter Status:</span>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="text-xs bg-[#FAF9F6] border border-[#E3E5E8] rounded-lg px-3 py-1.5 text-[#121417] font-medium focus:outline-none focus:ring-1 focus:ring-[#C59A45]"
          >
            <option value="ALL">All Statuses ({candidates.length})</option>
            <option value="PRIORITIZE">PRIORITIZE</option>
            <option value="PROMISING_BUT_UNCERTAIN">PROMISING BUT UNCERTAIN</option>
            <option value="INSUFFICIENT_EVIDENCE">INSUFFICIENT EVIDENCE</option>
            <option value="LOW_PRIORITY">LOW PRIORITY</option>
          </select>
        </div>

        <div className="flex items-center gap-3">
          <ArrowUpDown className="w-4 h-4 text-[#6C757D]" />
          <span className="text-xs font-semibold text-[#121417]">Sort By:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'rank' | 'score')}
            className="text-xs bg-[#FAF9F6] border border-[#E3E5E8] rounded-lg px-3 py-1.5 text-[#121417] font-medium focus:outline-none focus:ring-1 focus:ring-[#C59A45]"
          >
            <option value="rank">Rank (Ascending)</option>
            <option value="score">Composite Score (Descending)</option>
          </select>
        </div>
      </div>

      {/* Candidate Cards Grid */}
      <div className="space-y-4">
        {filtered.map((cand) => (
          <CandidateCard
            key={cand.candidate_id}
            candidate={cand}
            isTop={cand.rank === 1}
          />
        ))}
      </div>

      {/* Tabular Data Inspector */}
      <div className="qc-card p-6 overflow-x-auto">
        <div className="text-xs font-cinzel font-bold text-[#121417] tracking-wider uppercase mb-4">
          Tabular Data Inspector
        </div>
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-[#E3E5E8] text-[#6C757D] font-semibold uppercase">
              <th className="pb-3 pr-4">Rank</th>
              <th className="pb-3 pr-4">Candidate ID</th>
              <th className="pb-3 pr-4">Mature Mutation</th>
              <th className="pb-3 pr-4">5XJH Crystal</th>
              <th className="pb-3 pr-4">Score</th>
              <th className="pb-3 pr-4">Status</th>
              <th className="pb-3 pr-4">Confidence</th>
              <th className="pb-3 pr-4">Coverage</th>
              <th className="pb-3">VQE Error</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#F0F2F5]">
            {filtered.map((c) => (
              <tr key={c.candidate_id} className="hover:bg-[#FAF9F6] transition-colors">
                <td className="py-3 pr-4 font-cinzel font-bold text-[#C59A45]">#{c.rank}</td>
                <td className="py-3 pr-4 font-bold text-[#121417]">{c.candidate_id}</td>
                <td className="py-3 pr-4 font-mono">{c.mutations}</td>
                <td className="py-3 pr-4 font-mono text-[#343A40]">{c.crystal_mutation}</td>
                <td className="py-3 pr-4 font-bold">{c.fusion_score.toFixed(4)}</td>
                <td className="py-3 pr-4">{c.decision_status}</td>
                <td className="py-3 pr-4 text-[#6C757D]">{c.confidence_label}</td>
                <td className="py-3 pr-4">{c.evidence_coverage}</td>
                <td className="py-3 font-mono text-[#9E7A30]">
                  {c.vqe_casci_error !== null ? `${c.vqe_casci_error.toFixed(4)} Ha` : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
