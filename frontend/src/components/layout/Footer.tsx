import React from 'react';
import { NavLink } from 'react-router-dom';

export const Footer: React.FC = () => {
  return (
    <footer className="mt-20 border-t border-[#E3E5E8] bg-white py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="font-cinzel font-bold text-xl tracking-wider text-[#121417] mb-2">
          Q-CATALYST
        </div>
        <p className="text-sm text-[#6C757D] max-w-2xl mx-auto mb-6">
          Mechanism-Aware Quantum–AI Triage for PETase Engineering • National Quantum Hackathon Prototype (2026)
        </p>

        <div className="flex flex-wrap items-center justify-center gap-6 text-xs font-semibold text-[#9E7A30] mb-8">
          <NavLink to="/mechanism" className="hover:underline">PDB 5XJH Structure</NavLink>
          <span>•</span>
          <NavLink to="/quantum" className="hover:underline">8-Qubit VQE Active Space</NavLink>
          <span>•</span>
          <NavLink to="/pipeline" className="hover:underline">7-Stage Hybrid Orchestrator</NavLink>
          <span>•</span>
          <NavLink to="/provenance" className="hover:underline">Scientific Provenance</NavLink>
        </div>

        <div className="text-xs text-[#6C757D]/80 border-t border-[#E3E5E8] pt-6 max-w-3xl mx-auto">
          All evaluations are in-silico computational screening. No physical quantum hardware execution or wet-lab kinetic validation is claimed.
        </div>
      </div>
    </footer>
  );
};
