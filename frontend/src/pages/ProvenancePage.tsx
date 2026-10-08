import React, { useEffect, useState } from 'react';
import { api } from '@/api/client';
import { ProvenanceResponse } from '@/types/api';
import { ShieldCheck, Info } from 'lucide-react';

export const ProvenancePage: React.FC = () => {
  const [provenance, setProvenance] = useState<ProvenanceResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getProvenance()
      .then((data) => setProvenance(data))
      .catch((err) => console.error('Failed to load provenance:', err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-cinzel font-bold text-[#F59E0B] tracking-widest uppercase mb-1">
          Scientific Transparency
        </div>
        <h1 className="text-3xl font-extrabold text-[#F8FAFC] tracking-tight">
          Scientific Provenance & Disclaimers
        </h1>
        <p className="text-sm text-[#94A3B8] mt-1">
          Complete transparency on computational models, simulation limits, and methodological boundaries.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Disclaimers List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="text-xs font-cinzel font-bold text-[#F59E0B] tracking-wider uppercase mb-2">
            Methodological Boundaries
          </div>

          {provenance?.disclaimers.map((disc, idx) => (
            <div key={idx} className="qc-card p-6 border-l-4 border-l-[#F59E0B]">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-bold text-sm text-[#F8FAFC] flex items-center gap-2">
                  <Info className="w-4 h-4 text-[#F59E0B]" />
                  {disc.title}
                </h3>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#080C18] border border-[#F59E0B]/30 text-[#FDE047]">
                  {disc.category}
                </span>
              </div>
              <p className="text-xs text-[#CBD5E1] leading-relaxed">{disc.description}</p>
            </div>
          ))}
        </div>

        {/* Software Stack & Environment Info */}
        <div className="space-y-6">
          <div className="qc-card p-6">
            <div className="text-xs font-cinzel font-bold text-[#F59E0B] tracking-wider uppercase mb-3">
              Software Specifications
            </div>
            <div className="space-y-3 text-xs">
              {provenance &&
                Object.entries(provenance.software_stack).map(([k, v]) => (
                  <div key={k} className="flex justify-between py-1.5 border-b border-[#1E293B]">
                    <span className="text-[#94A3B8] font-medium">{k}:</span>
                    <span className="font-mono text-[#FDE047] font-semibold text-[11px]">{v}</span>
                  </div>
                ))}
            </div>
          </div>

          <div className="qc-card p-6 border-l-4 border-l-[#10B981] bg-gradient-to-br from-[#10B981]/10 via-[#0D1222] to-[#0A0E1A]">
            <div className="text-xs font-cinzel font-bold text-[#34D399] tracking-wider uppercase mb-2 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-[#10B981]" />
              Zero-Overclaim Pledge
            </div>
            <p className="text-xs text-[#CBD5E1] leading-relaxed">
              Q-Catalyst is designed strictly as a scientific triage tool. Quantum circuits are simulated algorithmically to validate convergence rather than claiming premature quantum advantage.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
