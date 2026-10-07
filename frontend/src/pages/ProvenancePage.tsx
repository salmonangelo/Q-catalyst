import React, { useEffect, useState } from 'react';
import { api } from '@/api/client';
import { ProvenanceResponse } from '@/types/api';
import { ShieldCheck, Info, Cpu, CheckCircle2 } from 'lucide-react';

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
        <h1 className="text-3xl font-extrabold text-[#121417] tracking-tight">
          Scientific Provenance & Disclaimers
        </h1>
        <p className="text-sm text-[#6C757D] mt-1">
          Complete transparency on computational models, simulation limits, and methodological boundaries.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Disclaimers List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="text-xs font-cinzel font-bold text-[#C59A45] tracking-wider uppercase mb-2">
            Methodological Boundaries
          </div>

          {provenance?.disclaimers.map((disc, idx) => (
            <div key={idx} className="qc-card p-6 border-l-4 border-l-[#C59A45]">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-bold text-sm text-[#121417] flex items-center gap-2">
                  <Info className="w-4 h-4 text-[#C59A45]" />
                  {disc.title}
                </h3>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-[#FAF9F6] border border-[#E3E5E8] text-[#6C757D]">
                  {disc.category}
                </span>
              </div>
              <p className="text-xs text-[#343A40] leading-relaxed">{disc.description}</p>
            </div>
          ))}
        </div>

        {/* Software Stack & Environment Info */}
        <div className="space-y-6">
          <div className="qc-card p-6">
            <div className="text-xs font-cinzel font-bold text-[#121417] tracking-wider uppercase mb-3">
              Software Specifications
            </div>
            <div className="space-y-3 text-xs">
              {provenance &&
                Object.entries(provenance.software_stack).map(([k, v]) => (
                  <div key={k} className="flex justify-between py-1.5 border-b border-[#E3E5E8]">
                    <span className="text-[#6C757D] font-medium">{k}:</span>
                    <span className="font-mono text-[#121417] font-semibold text-[11px]">{v}</span>
                  </div>
                ))}
            </div>
          </div>

          <div className="qc-card p-6 bg-gradient-to-b from-white to-[#FAF9F6]">
            <div className="text-xs font-cinzel font-bold text-[#1E7E34] tracking-wider uppercase mb-2 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-[#1E7E34]" />
              Zero-Overclaim Pledge
            </div>
            <p className="text-xs text-[#343A40] leading-relaxed">
              Q-Catalyst is designed strictly as a scientific triage tool. Quantum circuits are simulated algorithmically to validate convergence rather than claiming premature quantum advantage.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
