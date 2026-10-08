import React from 'react';
import { NavLink } from 'react-router-dom';

export const Footer: React.FC = () => {
  return (
    <footer className="mt-20 border-t border-[#F59E0B]/20 bg-[#070913]/90 backdrop-blur-md py-12 relative z-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="font-cinzel font-bold text-xl tracking-wider text-[#F8FAFC] mb-2 flex items-center justify-center gap-2">
          <span>Q-CATALYST</span>
          <span className="w-1.5 h-1.5 rounded-full bg-[#F59E0B]" />
        </div>
        <p className="text-sm text-[#94A3B8] max-w-2xl mx-auto mb-6">
          Mechanism-Aware Quantum–AI Triage for PETase Engineering • National Quantum Hackathon Prototype (2026)
        </p>

        <div className="flex flex-wrap items-center justify-center gap-6 text-xs font-semibold text-[#FDE047] mb-8">
          <NavLink to="/mechanism" className="hover:text-white transition-colors">PDB 5XJH Structure</NavLink>
          <span className="text-[#64748B]">•</span>
          <NavLink to="/quantum" className="hover:text-white transition-colors">8-Qubit VQE Active Space</NavLink>
          <span className="text-[#64748B]">•</span>
          <NavLink to="/pipeline" className="hover:text-white transition-colors">7-Stage Hybrid Orchestrator</NavLink>
          <span className="text-[#64748B]">•</span>
          <NavLink to="/provenance" className="hover:text-white transition-colors">Scientific Provenance</NavLink>
        </div>

        <div className="text-xs text-[#64748B] border-t border-[#1E293B] pt-6 max-w-3xl mx-auto leading-relaxed">
          All evaluations are in-silico computational screening. No physical quantum hardware execution or wet-lab kinetic validation is claimed.
        </div>
      </div>
    </footer>
  );
};
