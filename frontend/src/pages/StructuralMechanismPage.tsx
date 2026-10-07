import React, { useEffect, useState } from 'react';
import { api } from '@/api/client';
import { StructureResponse } from '@/types/api';
import { Dna, ShieldCheck, Layers } from 'lucide-react';

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
        <h1 className="text-3xl font-extrabold text-[#121417] tracking-tight">
          IsPETase Structural & Catalytic Mechanism
        </h1>
        <p className="text-sm text-[#6C757D] mt-1">
          Crystallographic architecture and spatial active-site distance preservation based on IsPETase PDB 5XJH (1.58 Å resolution).
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column: Catalytic Machinery Groups */}
        <div className="space-y-6">
          <div className="qc-card p-6">
            <div className="text-xs font-cinzel font-bold text-[#C59A45] tracking-wider uppercase mb-2">
              Crystallographic Architecture
            </div>
            <h3 className="text-lg font-bold text-[#121417] mb-4">
              Catalytic Machinery of 5XJH
            </h3>
            <p className="text-sm text-[#343A40] leading-relaxed mb-6">
              IsPETase features a specialized α/β hydrolase fold adapted for crystalline PET polymer chain degradation.
            </p>

            <div className="space-y-4">
              {structure?.catalytic_groups.map((group, idx) => (
                <div
                  key={idx}
                  className="bg-[#FAF9F6] border border-[#E3E5E8] rounded-xl p-4 transition-all hover:border-[#C59A45]/40"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="w-5 h-5 rounded-full bg-[#121417] text-white text-[10px] font-bold flex items-center justify-center">
                      {idx + 1}
                    </span>
                    <h4 className="font-bold text-sm text-[#121417]">{group.group_name}</h4>
                  </div>
                  <p className="text-xs text-[#6C757D] mb-2">{group.description}</p>
                  <div className="flex flex-wrap gap-2">
                    {group.residues.map((res, rIdx) => (
                      <span
                        key={rIdx}
                        className="px-2 py-0.5 rounded bg-white border border-[#E3E5E8] text-[11px] font-medium text-[#343A40]"
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
            <div className="text-xs font-cinzel font-bold text-[#121417] tracking-wider uppercase mb-2">
              Active-Site Geometry
            </div>
            <h3 className="text-lg font-bold text-[#121417] mb-4">
              Spatial Proximity & Triad Distance Matrix
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[#E3E5E8] text-[#6C757D] font-semibold uppercase">
                    <th className="pb-3 pr-4">Residue Pair</th>
                    <th className="pb-3 pr-4">Distance</th>
                    <th className="pb-3 pr-4">Functional State</th>
                    <th className="pb-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F0F2F5]">
                  {structure?.distance_matrix.map((row, i) => (
                    <tr key={i} className="hover:bg-[#FAF9F6] transition-colors">
                      <td className="py-3 pr-4 font-semibold text-[#121417]">
                        {row.residue_pair}
                      </td>
                      <td className="py-3 pr-4 font-mono font-bold text-[#9E7A30]">
                        {row.distance_angstrom.toFixed(2)} Å
                      </td>
                      <td className="py-3 pr-4 text-[#6C757D]">{row.functional_state}</td>
                      <td className="py-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#EAF8EE] text-[#1E7E34]">
                          {row.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-6 bg-[#C59A45]/10 border border-[#C59A45]/30 rounded-xl p-4 text-xs text-[#7A5C1B] leading-relaxed">
              <div className="font-bold mb-1">Mechanism Acquisition Penalty Gate:</div>
              Mutations situated within the 6.0 Å active sphere that perturb catalytic triad hydrogen-bonding distances beyond 3.5 Å incur penalty dampening in multimodal fusion.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
