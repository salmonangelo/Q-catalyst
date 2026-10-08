import React from 'react';
import { NavLink } from 'react-router-dom';
import { Atom, Sparkles } from 'lucide-react';

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
    <header className="sticky top-0 z-40 bg-[#070913]/85 backdrop-blur-lg border-b border-[#F59E0B]/20 shadow-qc-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <NavLink to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#141A2E] to-[#0A0D17] border border-[#F59E0B]/50 flex items-center justify-center text-[#FDE047] font-cinzel font-bold text-lg shadow-qc-gold group-hover:border-[#FDE047] transition-all group-hover:scale-105">
              Q
            </div>
            <div>
              <div className="font-cinzel font-bold text-lg tracking-wider text-[#F8FAFC] group-hover:text-[#FDE047] transition-colors flex items-center gap-1.5">
                Q-CATALYST
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#DC2626]" />
              </div>
              <div className="text-[10px] text-[#94A3B8] font-medium tracking-widest uppercase">
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
                      ? 'bg-gradient-to-r from-[#F59E0B]/20 to-[#DC2626]/10 text-[#FDE047] border border-[#F59E0B]/40 shadow-qc-sm'
                      : 'text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#141A2E]/60'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          {/* Status Badges */}
          <div className="hidden lg:flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#F59E0B]/10 text-[#FDE047] border border-[#F59E0B]/30 shadow-qc-gold">
              <Sparkles className="w-3.5 h-3.5 text-[#F59E0B]" />
              Hybrid Prototype
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#06B6D4]/10 text-[#38BDF8] border border-[#06B6D4]/30 shadow-qc-cyan">
              <Atom className="w-3.5 h-3.5 text-[#38BDF8]" />
              8-Qubit VQE
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
