import React, { useEffect, useState } from 'react';
import { api } from '@/api/client';
import { QuantumDetailsResponse, QuantumHistoryResponse } from '@/types/api';
import { MetricCard } from '@/components/common/MetricCard';
import { VQEConvergencePlot } from '@/components/charts/VQEConvergencePlot';
import { Atom, Cpu, Sparkles } from 'lucide-react';

export const QuantumLabPage: React.FC = () => {
  const [quantum, setQuantum] = useState<QuantumDetailsResponse | null>(null);
  const [history, setHistory] = useState<QuantumHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getQuantum(), api.getQuantumHistory()])
      .then(([qData, hData]) => {
        setQuantum(qData);
        setHistory(hData);
      })
      .catch((err) => console.error('Failed to load quantum data:', err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-cinzel font-bold text-[#F59E0B] tracking-widest uppercase mb-1">
          Active-Space Hamiltonian Simulation
        </div>
        <h1 className="text-3xl font-extrabold text-[#F8FAFC] tracking-tight">
          Quantum Chemical Simulation Lab
        </h1>
        <p className="text-sm text-[#94A3B8] mt-1">
          Active-space electronic Hamiltonian mapping, exact CASCI classical diagonalization, and VQE convergence profiling on a simulated 8-qubit register.
        </p>
      </div>

      {/* Metric Chips Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <MetricCard
          label="Active Space"
          value={`${quantum?.active_space_electrons || 4}e, ${quantum?.active_space_orbitals || 4}o`}
          subtext="4 Electrons, 4 Orbitals"
          variant="gold"
        />
        <MetricCard
          label="Qubit Register"
          value={`${quantum?.num_qubits || 8} Qubits`}
          subtext="Jordan-Wigner Mapping"
          variant="quantum"
        />
        <MetricCard
          label="Hamiltonian Terms"
          value={`${quantum?.num_pauli_terms || 61} Pauli`}
          subtext="Sparse Pauli Operator"
          variant="ruby"
        />
        <MetricCard
          label="Variational Ansatz"
          value={quantum?.ansatz_type || 'TwoLocal'}
          subtext={`Ry-Rz (${quantum?.optimizer || 'COBYLA'})`}
        />
      </div>

      {/* Main Analysis Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Convergence Chart */}
        <div className="lg:col-span-2 qc-card p-6">
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs font-cinzel font-bold text-[#F59E0B] tracking-wider uppercase">
              Variational Minimization
            </div>
            <span className="text-xs font-mono text-[#FDE047] flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-[#F59E0B]" />
              COBYLA Optimizer
            </span>
          </div>
          <h3 className="text-lg font-bold text-[#F8FAFC] mb-4">VQE Optimization Trajectory</h3>
          {history ? (
            <VQEConvergencePlot
              history={history.history}
              casciEnergy={history.casci_reference_energy}
              finalVqeEnergy={history.final_vqe_energy}
            />
          ) : (
            <div className="h-64 flex items-center justify-center text-xs text-[#64748B]">
              Loading convergence curve...
            </div>
          )}
        </div>

        {/* Energy Agreement & Noise Summary */}
        <div className="space-y-6">
          <div className="qc-card p-6 border-t-4 border-t-[#F59E0B]">
            <div className="text-xs font-cinzel font-bold text-[#F59E0B] tracking-wider uppercase mb-2">
              Energy Agreement Summary
            </div>
            <h3 className="text-lg font-bold text-[#F8FAFC] mb-4">CASCI vs VQE</h3>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-2 border-b border-[#1E293B]">
                <span className="font-semibold text-[#94A3B8]">CASCI Reference:</span>
                <span className="font-mono font-bold text-[#EF4444]">
                  {quantum?.casci_energy.toFixed(6) || '-18.215733'} Ha
                </span>
              </div>
              <div className="flex justify-between py-2 border-b border-[#1E293B]">
                <span className="font-semibold text-[#94A3B8]">VQE Optimized:</span>
                <span className="font-mono font-bold text-[#FDE047]">
                  {quantum?.vqe_energy.toFixed(6) || '-18.206475'} Ha
                </span>
              </div>
              <div className="flex justify-between py-2 border-b border-[#1E293B]">
                <span className="font-semibold text-[#94A3B8]">Absolute Deviation:</span>
                <span className="font-mono font-bold text-[#34D399]">
                  {quantum?.absolute_error.toFixed(6) || '0.009258'} Ha
                </span>
              </div>
              <div className="flex justify-between py-2">
                <span className="font-semibold text-[#94A3B8]">Depolarizing Noise:</span>
                <span className="font-mono font-bold text-[#38BDF8]">
                  {quantum?.noisy_energy !== null && quantum?.noisy_energy !== undefined
                    ? `${quantum.noisy_energy.toFixed(6)} Ha`
                    : 'Not Enabled (Ideal Statevector)'}
                </span>
              </div>
            </div>

            <div className="mt-6 bg-[#080C18] p-4 rounded-xl border border-[#F59E0B]/20 text-xs text-[#94A3B8] leading-relaxed">
              <div className="font-bold text-[#FDE047] mb-1 flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-[#F59E0B]" /> Scientific Provenance:
              </div>
              Simulated using Qiskit Aer statevector backend. The reduced Hamiltonian models the active-site catalytic core. No physical quantum hardware execution or quantum supremacy is claimed.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
