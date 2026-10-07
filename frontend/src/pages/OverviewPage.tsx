import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Atom, Dna, ArrowRight, Sparkles, Layers, ShieldCheck, Cpu } from 'lucide-react';
import { api } from '@/api/client';
import { OverviewResponse, CandidatesListResponse } from '@/types/api';
import { MetricCard } from '@/components/common/MetricCard';
import { RankingBarChart } from '@/components/charts/RankingBarChart';

export const OverviewPage: React.FC = () => {
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [candidates, setCandidates] = useState<CandidatesListResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getOverview(), api.getCandidates()])
      .then(([ovData, candsData]) => {
        setOverview(ovData);
        setCandidates(candsData);
      })
      .catch((err) => console.error('Failed to load overview data:', err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="hero-gradient border border-[#E3E5E8] rounded-2xl p-8 sm:p-12 shadow-qc-md relative overflow-hidden">
        <div className="max-w-3xl relative z-10">
          <div className="text-xs font-cinzel font-bold tracking-widest text-[#C59A45] uppercase mb-3">
            National Quantum Hackathon Prototype • 2026
          </div>
          <h1 className="text-3xl sm:text-5xl font-extrabold text-[#121417] tracking-tight leading-tight mb-4">
            Mechanism-Aware Quantum–AI Triage for PETase Engineering
          </h1>
          <p className="text-base sm:text-lg text-[#6C757D] leading-relaxed mb-8">
            Accelerating enzymatic plastic degradation by bridging sequence AI, structural catalytic reasoning, and active-space quantum simulation into a transparent candidate decision engine.
          </p>

          <div className="flex flex-wrap items-center gap-4">
            <NavLink
              to="/triage"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#121417] text-white text-sm font-semibold hover:bg-black shadow-qc-sm transition-all"
            >
              Explore Candidate Triage <ArrowRight className="w-4 h-4" />
            </NavLink>
            <NavLink
              to="/quantum"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-white border border-[#C59A45]/40 text-[#9E7A30] text-sm font-semibold hover:bg-[#FAF9F6] transition-all"
            >
              <Atom className="w-4 h-4" /> View Quantum Simulation
            </NavLink>
          </div>
        </div>

        {/* Subtle Decorative Molecular Linework */}
        <div className="absolute right-[-5%] top-[-20%] w-96 h-96 rounded-full bg-radial from-[#C59A45]/10 to-transparent pointer-events-none" />
      </section>

      {/* Narrative & Scientific Value */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="qc-card p-8">
            <div className="text-xs font-cinzel font-bold tracking-wider text-[#C59A45] uppercase mb-2">
              Problem & Solution
            </div>
            <h2 className="text-2xl font-bold text-[#121417] mb-4">Why Q-Catalyst?</h2>
            <p className="text-sm sm:text-base text-[#343A40] leading-relaxed mb-4">
              Rational engineering of <b>IsPETase</b> (from <i>Ideonella sakaiensis</i>) faces an immense mutational search space. Standard sequence-only AI models frequently select mutations that destabilize catalytic hydrogen-bonding networks.
            </p>
            <p className="text-sm sm:text-base text-[#343A40] leading-relaxed">
              <b>Q-Catalyst</b> implements a multimodal triage hierarchy: sequence models screen variants with conformal uncertainty bounds; structural proximity filters preserve the <b>Ser160-Asp206-His237</b> catalytic triad; and critical active-site transitions are simulated on a parameterized <b>(4e, 4o) 8-qubit Variational Quantum Eigensolver (VQE)</b>.
            </p>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-8 pt-6 border-t border-[#E3E5E8]">
              <MetricCard label="Target PDB" value="5XJH" subtext="1.58 Å resolution" />
              <MetricCard label="Active Space" value="4e, 4o" subtext="8 Qubits / JW" variant="gold" />
              <MetricCard label="Pauli Terms" value={overview?.quantum_highlight.num_pauli_terms || 61} subtext="Sparse operator" variant="quantum" />
              <MetricCard label="Pipeline Stages" value="7 / 7" subtext="100% Automated" />
            </div>
          </div>

          {/* Top Prioritized Candidate Highlight */}
          <div className="qc-card qc-card-gold p-8">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
              <div>
                <div className="text-xs font-cinzel font-bold text-[#C59A45] tracking-wider uppercase mb-1">
                  Top Priority Candidate
                </div>
                <h3 className="text-xl font-bold text-[#121417]">
                  {overview?.top_candidate.candidate_id || 'VAR_W132H'}
                  <span className="ml-2 text-sm font-normal text-[#6C757D]">
                    (5XJH Crystal: {overview?.top_candidate.crystal_mutation || 'W159H'})
                  </span>
                </h3>
              </div>
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[#EAF8EE] text-[#1E7E34]">
                RANK #01 • {overview?.top_candidate.decision_status || 'PRIORITIZE'}
              </span>
            </div>
            <p className="text-sm text-[#343A40] leading-relaxed mb-4">
              Located in the substrate-binding cleft, substitution with Histidine modulates electrostatic π-stacking interactions with PET aromatic rings while strictly preserving catalytic triad integrity.
            </p>
            <div className="flex items-center justify-between text-xs font-semibold text-[#6C757D] pt-4 border-t border-[#E3E5E8]">
              <span>Fusion Score: <b>{overview?.top_candidate.fusion_score.toFixed(4) || '0.7712'}</b></span>
              <span>Evidence Coverage: <b>{overview?.top_candidate.evidence_coverage || '5/6 Channels'}</b></span>
              <NavLink
                to="/deep-dive"
                className="text-[#C59A45] hover:underline inline-flex items-center gap-1"
              >
                Inspect Evidence <ArrowRight className="w-3.5 h-3.5" />
              </NavLink>
            </div>
          </div>
        </div>

        {/* Quantum Lab Highlight & Ranking Chart */}
        <div className="space-y-6">
          <div className="qc-card qc-card-quantum p-6">
            <div className="text-xs font-cinzel font-bold text-[#5B4AE4] tracking-wider uppercase mb-2">
              Quantum Simulation Layer
            </div>
            <h3 className="text-lg font-bold text-[#121417] mb-2">Ground-State VQE</h3>
            <p className="text-xs text-[#6C757D] leading-relaxed mb-4">
              Phase 5 evaluates the electronic Hamiltonian for the active site cluster.
            </p>

            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between py-1.5 border-b border-[#E3E5E8]">
                <span className="text-[#6C757D]">CASCI Reference:</span>
                <span className="font-mono font-bold text-[#121417]">
                  {overview?.quantum_highlight.casci_energy.toFixed(6) || '-18.215733'} Ha
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-[#E3E5E8]">
                <span className="text-[#6C757D]">VQE Optimized:</span>
                <span className="font-mono font-bold text-[#C59A45]">
                  {overview?.quantum_highlight.vqe_energy.toFixed(6) || '-18.206475'} Ha
                </span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-[#6C757D]">Absolute Deviation:</span>
                <span className="font-mono font-bold text-[#198754]">
                  {overview?.quantum_highlight.absolute_error.toFixed(6) || '0.009258'} Ha
                </span>
              </div>
            </div>
          </div>

          <div className="qc-card p-6">
            <div className="text-xs font-cinzel font-bold text-[#121417] tracking-wider uppercase mb-3">
              Composite Ranking Overview
            </div>
            {candidates ? (
              <RankingBarChart candidates={candidates.candidates} />
            ) : (
              <div className="h-64 flex items-center justify-center text-xs text-[#6C757D]">
                Loading ranking chart...
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
};
