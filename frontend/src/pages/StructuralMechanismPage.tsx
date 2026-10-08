import React, { useEffect, useState } from 'react';
import { api } from '@/api/client';
import { StructureResponse } from '@/types/api';

export const StructuralMechanismPage: React.FC = () => {
  const [structure, setStructure] = useState<StructureResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getStructure()
      .then((data) => setStructure(data))
      .catch((err) => console.error('Failed to load structural data:', err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-cinzel font-bold text-[#F59E0B] tracking-widest uppercase mb-1">
          Catalytic Geometry & Spatial Coordinates
        </div>
        <h1 className="text-3xl font-extrabold text-[#F8FAFC] tracking-tight">
          IsPETase Structural & Catalytic Mechanism
        </h1>
        <p className="text-sm text-[#94A3B8] mt-1">
          Crystallographic architecture and spatial active-site distance preservation based on IsPETase PDB 5XJH (1.58 Å resolution).
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column: Catalytic Machinery Groups */}
        <div className="space-y-6">
          <div className="qc-card p-6">
            <div className="text-xs font-cinzel font-bold text-[#F59E0B] tracking-wider uppercase mb-2">
              Crystallographic Architecture
            </div>
            <h3 className="text-lg font-bold text-[#F8FAFC] mb-4">
              Catalytic Machinery of 5XJH
            </h3>
            <p className="text-sm text-[#CBD5E1] leading-relaxed mb-6">
              IsPETase features a specialized α/β hydrolase fold adapted for crystalline PET polymer chain degradation.
            </p>

            <div className="space-y-4">
              {structure?.catalytic_groups.map((group, idx) => (
                <div
                  key={idx}
                  className="bg-[#080C18] border border-[#CBD5E1]/10 rounded-xl p-4 transition-all hover:border-[#F59E0B]/40"
                >
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="w-5 h-5 rounded-full bg-[#F59E0B]/20 text-[#FDE047] text-[10px] font-bold flex items-center justify-center border border-[#F59E0B]/40">
                      {idx + 1}
                    </span>
                    <h4 className="font-bold text-sm text-[#F8FAFC]">{group.group_name}</h4>
                  </div>
                  <p className="text-xs text-[#94A3B8] mb-2.5">{group.description}</p>
                  <div className="flex flex-wrap gap-2">
                    {group.residues.map((res, rIdx) => (
                      <span
                        key={rIdx}
                        className="px-2.5 py-1 rounded bg-[#0D1222] border border-[#CBD5E1]/15 text-[11px] font-mono font-medium text-[#CBD5E1]"
                      >
                        {res}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Distance Matrix & Gate Policy */}
        <div className="space-y-6">
          <div className="qc-card p-6">
            <div className="text-xs font-cinzel font-bold text-[#F59E0B] tracking-wider uppercase mb-2">
              Active-Site Geometry
            </div>
            <h3 className="text-lg font-bold text-[#F8FAFC] mb-4">
              Spatial Proximity & Triad Distance Matrix
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[#1E293B] text-[#94A3B8] font-semibold uppercase">
                    <th className="pb-3 pr-4">Residue Pair</th>
                    <th className="pb-3 pr-4">Distance</th>
                    <th className="pb-3 pr-4">Functional State</th>
                    <th className="pb-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#141A2E]">
                  {structure?.distance_matrix.map((row, i) => (
                    <tr key={i} className="hover:bg-[#141A2E]/50 transition-colors">
                      <td className="py-3 pr-4 font-semibold text-[#F8FAFC]">
                        {row.residue_pair}
                      </td>
                      <td className="py-3 pr-4 font-mono font-bold text-[#FDE047]">
                        {row.distance_angstrom.toFixed(2)} Å
                      </td>
                      <td className="py-3 pr-4 text-[#94A3B8]">{row.functional_state}</td>
                      <td className="py-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#10B981]/15 text-[#34D399] border border-[#10B981]/30">
                          {row.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-6 bg-[#080C18] border border-[#F59E0B]/30 rounded-xl p-4 text-xs text-[#FDE047] leading-relaxed">
              <div className="font-bold mb-1 text-[#F59E0B]">Mechanism Acquisition Penalty Gate:</div>
              Mutations situated within the 6.0 Å active sphere that perturb catalytic triad hydrogen-bonding distances beyond 3.5 Å incur penalty dampening in multimodal fusion.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
