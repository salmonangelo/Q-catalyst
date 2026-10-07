import React from 'react';
import { NavLink } from 'react-router-dom';
import { Atom, Dna, Layers, ShieldCheck, Sparkles } from 'lucide-react';

export const Navbar: React.FC = () => {
  const navItems = [
    { to: '/', label: 'Overview' },
    { to: '/triage', label: 'Candidate Triage' },
    { to: '/deep-dive', label: 'Candidate Deep Dive' },
    { to: '/quantum', label: 'Quantum Lab' },
    { to: '/mechanism', label: 'Structural Mechanism' },
    { to: '/pipeline', label: 'Pipeline' },
    { to: '/provenance', label: 'Provenance' },
  ];

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-[#E3E5E8] shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <NavLink to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-[#121417] border border-[#C59A45] flex items-center justify-center text-[#DFBD74] font-cinzel font-bold text-lg shadow-qc-sm group-hover:border-[#DFBD74] transition-colors">
              Q
            </div>
            <div>
              <div className="font-cinzel font-bold text-lg tracking-wider text-[#121417]">
                Q-CATALYST
              </div>
              <div className="text-[10px] text-[#6C757D] font-medium tracking-widest uppercase">
                Quantum–AI PETase Triage
              </div>
            </div>
          </NavLink>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-[#121417] text-white shadow-sm'
                      : 'text-[#343A40] hover:text-[#121417] hover:bg-[#F5F4F0]'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          {/* Status Badges */}
          <div className="hidden lg:flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-[#C59A45]/10 text-[#9E7A30] border border-[#C59A45]/30">
              <Sparkles className="w-3.5 h-3.5" />
              Hybrid Prototype
            </span>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-[#5B4AE4]/10 text-[#5B4AE4] border border-[#5B4AE4]/30">
              <Atom className="w-3.5 h-3.5" />
              8-Qubit VQE
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
