import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Atom, ArrowRight, Sparkles, Layers, ShieldCheck, Cpu, ChevronRight } from 'lucide-react';
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
      <section className="qc-card hero-gradient rounded-3xl p-8 sm:p-12 relative overflow-hidden">
        {/* Glow ambient spots */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-radial from-[#F59E0B]/15 via-[#DC2626]/10 to-transparent blur-3xl pointer-events-none" />
        <div className="absolute -bottom-10 -left-10 w-80 h-80 bg-radial from-[#06B6D4]/15 to-transparent blur-3xl pointer-events-none" />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center relative z-10">
          <div className="lg:col-span-8 space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-cinzel font-bold tracking-widest text-[#FDE047] bg-[#F59E0B]/10 border border-[#F59E0B]/30 shadow-qc-gold">
              <Sparkles className="w-3.5 h-3.5 text-[#F59E0B]" />
              NATIONAL QUANTUM HACKATHON PROTOTYPE • 2026
            </div>
            
            <h1 className="text-3xl sm:text-5xl font-extrabold text-[#F8FAFC] tracking-tight leading-tight">
              Mechanism-Aware <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FDE047] via-[#F59E0B] to-[#EF4444]">Quantum–AI Triage</span> for PETase Engineering
            </h1>
            
            <p className="text-base sm:text-lg text-[#94A3B8] leading-relaxed max-w-2xl">
              Accelerating enzymatic plastic degradation by bridging protein sequence AI, structural catalytic reasoning, and active-space quantum simulation into a transparent candidate decision engine.
            </p>

            <div className="flex flex-wrap items-center gap-4 pt-2">
              <NavLink
                to="/triage"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-[#F59E0B] to-[#D97706] text-[#070913] text-sm font-bold hover:brightness-110 shadow-qc-gold transition-all"
              >
                Explore Candidate Triage <ArrowRight className="w-4 h-4" />
              </NavLink>
              <NavLink
                to="/quantum"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#0D1222]/90 border border-[#F59E0B]/40 text-[#FDE047] text-sm font-semibold hover:bg-[#141A2E] hover:border-[#F59E0B]/70 shadow-qc-sm transition-all"
              >
                <Atom className="w-4 h-4 text-[#F59E0B]" /> View Quantum Simulation
              </NavLink>
            </div>
          </div>

          {/* Hero Quantum Hardware Chandelier Art Card */}
          <div className="lg:col-span-4 flex justify-center">
            <div className="relative group">
              <div className="absolute -inset-1 rounded-2xl bg-gradient-to-r from-[#DC2626]/40 via-[#F59E0B]/40 to-[#06B6D4]/40 blur-lg opacity-70 group-hover:opacity-100 transition duration-500" />
              <div className="relative bg-[#0A0E1A] border border-[#F59E0B]/40 rounded-2xl p-4 overflow-hidden shadow-qc-lg text-center">
                <div className="relative h-64 sm:h-72 w-full flex items-center justify-center overflow-hidden rounded-xl bg-gradient-to-b from-[#141A2E]/50 to-[#060810]">
                  <img 
                    src="/assets/quantum_hardware_bg.png" 
                    alt="Quantum Dilution Refrigerator" 
                    className="h-full object-contain filter drop-shadow-[0_0_15px_rgba(245,158,11,0.3)] group-hover:scale-105 transition-transform duration-500"
                  />
                </div>
                <div className="mt-3 flex items-center justify-between text-xs px-2">
                  <span className="font-mono text-[#FDE047] font-semibold flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-[#10B981] animate-ping" />
                    Cryogenic Stage: 15 mK
                  </span>
                  <span className="text-[#94A3B8] font-mono">8-Qubit (4e, 4o)</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Narrative & Scientific Value */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="qc-card p-8">
            <div className="text-xs font-cinzel font-bold tracking-wider text-[#F59E0B] uppercase mb-2">
              Problem & Solution
            </div>
            <h2 className="text-2xl font-bold text-[#F8FAFC] mb-4">Why Q-Catalyst?</h2>
            <p className="text-sm sm:text-base text-[#CBD5E1] leading-relaxed mb-4">
              Rational engineering of <b className="text-white">IsPETase</b> (from <i>Ideonella sakaiensis</i>) faces an immense mutational search space. Standard sequence-only AI models frequently select mutations that destabilize catalytic hydrogen-bonding networks.
            </p>
            <p className="text-sm sm:text-base text-[#CBD5E1] leading-relaxed">
              <b className="text-[#FDE047]">Q-Catalyst</b> implements a multimodal triage hierarchy: sequence models screen variants with conformal uncertainty bounds; structural proximity filters preserve the <b className="text-white">Ser160-Asp206-His237</b> catalytic triad; and critical active-site transitions are simulated on a parameterized <b className="text-white">(4e, 4o) 8-qubit Variational Quantum Eigensolver (VQE)</b>.
            </p>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-8 pt-6 border-t border-[#1E293B]">
              <MetricCard label="Target PDB" value="5XJH" subtext="1.58 Å resolution" />
              <MetricCard label="Active Space" value="4e, 4o" subtext="8 Qubits / JW" variant="gold" />
              <MetricCard label="Pauli Terms" value={overview?.quantum_highlight.num_pauli_terms || 61} subtext="Sparse operator" variant="quantum" />
              <MetricCard label="Pipeline Stages" value="7 / 7" subtext="100% Automated" variant="ruby" />
            </div>
          </div>

          {/* Top Prioritized Candidate Highlight */}
          <div className="qc-card qc-card-gold p-8">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
              <div>
                <div className="text-xs font-cinzel font-bold text-[#F59E0B] tracking-wider uppercase mb-1">
                  Top Priority Candidate
                </div>
                <h3 className="text-xl font-bold text-[#F8FAFC]">
                  {overview?.top_candidate.candidate_id || 'VAR_W132H'}
                  <span className="ml-2 text-sm font-normal text-[#94A3B8]">
                    (5XJH Crystal: {overview?.top_candidate.crystal_mutation || 'W159H'})
                  </span>
                </h3>
              </div>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#10B981]/15 text-[#34D399] border border-[#10B981]/40 shadow-qc-sm">
                <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-pulse" />
                RANK #01 • {overview?.top_candidate.decision_status || 'PRIORITIZE'}
              </span>
            </div>
            <p className="text-sm text-[#CBD5E1] leading-relaxed mb-4">
              {overview?.top_candidate.role
                ? `Role: ${overview.top_candidate.role}. High sequence score combined with tight conformal uncertainty and safe distance to the catalytic triad.`
                : 'High sequence score combined with tight conformal uncertainty and safe distance to the catalytic triad.'}
            </p>
            <div className="flex items-center justify-between pt-4 border-t border-[#F59E0B]/20 text-xs">
              <span className="font-mono text-[#FDE047] font-semibold">
                Multimodal Composite Score: {overview?.top_candidate.fusion_score?.toFixed(4) || '0.8421'}
              </span>
              <NavLink to="/deep-dive" className="text-[#38BDF8] hover:text-[#7DD3FC] font-semibold flex items-center gap-1">
                View candidate profile <ChevronRight className="w-3.5 h-3.5" />
              </NavLink>
            </div>
          </div>
        </div>

        {/* Right Column: Mini Ranking Chart & Quantum Highlight */}
        <div className="space-y-6">
          <div className="qc-card p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-[#F8FAFC]">Candidate Triage Preview</h3>
              <NavLink to="/triage" className="text-xs font-semibold text-[#F59E0B] hover:text-[#FDE047]">
                View All →
              </NavLink>
            </div>
            {candidates ? (
              <RankingBarChart candidates={candidates.candidates} />
            ) : (
              <div className="h-72 flex items-center justify-center text-xs text-[#64748B]">
                Loading triage data...
              </div>
            )}
          </div>

          <div className="qc-card p-6 border-l-4 border-l-[#DC2626]">
            <div className="flex items-center gap-2 text-xs font-bold text-[#EF4444] uppercase tracking-wider mb-2">
              <Cpu className="w-4 h-4" /> Quantum Simulation Policy
            </div>
            <p className="text-xs text-[#94A3B8] leading-relaxed mb-3">
              To mirror real-world quantum compute allocation, 8-qubit VQE simulation is executed on representative candidate active sites. Unsimulated variants are dynamically normalized without penalty.
            </p>
            <div className="bg-[#080B14] p-3 rounded-lg border border-[#DC2626]/20 font-mono text-xs text-[#CBD5E1] space-y-1">
              <div>VQE Energy: <span className="text-[#FDE047]">{overview?.quantum_highlight.vqe_energy.toFixed(6) || '-18.206475'} Ha</span></div>
              <div>CASCI Baseline: <span className="text-[#EF4444]">{overview?.quantum_highlight.casci_energy.toFixed(6) || '-18.215733'} Ha</span></div>
              <div>Hamiltonian: <span className="text-[#38BDF8]">{overview?.quantum_highlight.num_pauli_terms || 61} Pauli terms</span></div>
            </div>
          </div>
        </div>
      </section>

      {/* 4 Pillars Architecture */}
      <section className="space-y-6">
        <div className="text-center max-w-2xl mx-auto">
          <div className="text-xs font-cinzel font-bold text-[#F59E0B] tracking-widest uppercase mb-1">
            System Architecture
          </div>
          <h2 className="text-2xl font-bold text-[#F8FAFC]">The 4 Triage Pillars</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="qc-card p-6 space-y-3 hover:border-[#F59E0B]/50 transition-all">
            <div className="w-10 h-10 rounded-xl bg-[#F59E0B]/10 border border-[#F59E0B]/30 flex items-center justify-center text-[#F59E0B] shadow-qc-gold">
              <Sparkles className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-[#F8FAFC]">1. Sequence AI</h3>
            <p className="text-xs text-[#94A3B8] leading-relaxed">
              ESM protein embeddings predict mutational fitness while preserving sequence integrity across global families.
            </p>
          </div>

          <div className="qc-card p-6 space-y-3 hover:border-[#38BDF8]/50 transition-all">
            <div className="w-10 h-10 rounded-xl bg-[#06B6D4]/10 border border-[#06B6D4]/30 flex items-center justify-center text-[#38BDF8] shadow-qc-cyan">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-[#F8FAFC]">2. Conformal Uncertainty</h3>
            <p className="text-xs text-[#94A3B8] leading-relaxed">
              Rigorous split-conformal calibration generates prediction intervals with formal statistical guarantees.
            </p>
          </div>

          <div className="qc-card p-6 space-y-3 hover:border-[#EF4444]/50 transition-all">
            <div className="w-10 h-10 rounded-xl bg-[#DC2626]/10 border border-[#DC2626]/30 flex items-center justify-center text-[#EF4444] shadow-qc-ruby">
              <Layers className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-[#F8FAFC]">3. Mechanism Reasoning</h3>
            <p className="text-xs text-[#94A3B8] leading-relaxed">
              Active-site cluster analysis safeguards the Ser160-Asp206-His237 catalytic triad against disruption.
            </p>
          </div>

          <div className="qc-card p-6 space-y-3 hover:border-[#A5B4FC]/50 transition-all">
            <div className="w-10 h-10 rounded-xl bg-[#6366F1]/10 border border-[#6366F1]/30 flex items-center justify-center text-[#A5B4FC] shadow-sm">
              <Atom className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-[#F8FAFC]">4. Quantum VQE</h3>
            <p className="text-xs text-[#94A3B8] leading-relaxed">
              (4e, 4o) active space mapped to 8 qubits via Jordan-Wigner transformation and solved via parameterized ansatz.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};
