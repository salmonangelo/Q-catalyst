import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Navbar } from '@/components/layout/Navbar';
import { Footer } from '@/components/layout/Footer';

import { OverviewPage } from '@/pages/OverviewPage';
import { CandidateTriagePage } from '@/pages/CandidateTriagePage';
import { CandidateDeepDivePage } from '@/pages/CandidateDeepDivePage';
import { QuantumLabPage } from '@/pages/QuantumLabPage';
import { StructuralMechanismPage } from '@/pages/StructuralMechanismPage';
import { PipelinePage } from '@/pages/PipelinePage';
import { ProvenancePage } from '@/pages/ProvenancePage';

export function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col bg-[#060810] text-[#CBD5E1] relative selection:bg-[#F59E0B]/30 selection:text-white">
        {/* Fixed Ambient Background Artwork & Cryogenic Glows */}
        <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
          {/* Top Ruby / Crimson Light Orb */}
          <div className="absolute top-[-10%] left-1/2 -translate-x-1/2 w-[900px] h-[450px] bg-radial from-[#DC2626]/12 via-[#F59E0B]/8 to-transparent blur-3xl opacity-70" />
          
          {/* Central Quantum Chandelier Graphic (Translucent Cryogenic Watermark) */}
          <div 
            className="absolute top-0 left-1/2 -translate-x-1/2 w-[1100px] h-[1500px] bg-no-repeat bg-top opacity-[0.14] mix-blend-screen"
            style={{ 
              backgroundImage: `url('/assets/quantum_hardware_bg.png')`,
              backgroundSize: 'contain',
              maskImage: 'radial-gradient(ellipse 70% 60% at 50% 30%, black 20%, transparent 85%)',
              WebkitMaskImage: 'radial-gradient(ellipse 70% 60% at 50% 30%, black 20%, transparent 85%)'
            }}
          />

          {/* Deep Amber & Gold Lower Atmospheric Glows */}
          <div className="absolute top-[35%] -left-[10%] w-[600px] h-[600px] bg-radial from-[#F59E0B]/10 to-transparent blur-3xl" />
          <div className="absolute top-[55%] -right-[10%] w-[650px] h-[650px] bg-radial from-[#DC2626]/8 via-[#F59E0B]/6 to-transparent blur-3xl" />
          
          {/* Subtle Cybernetic Grid Pattern */}
          <div 
            className="absolute inset-0 opacity-[0.03]"
            style={{
              backgroundImage: `linear-gradient(to right, #CBD5E1 1px, transparent 1px), linear-gradient(to bottom, #CBD5E1 1px, transparent 1px)`,
              backgroundSize: '60px 60px'
            }}
          />
        </div>

        {/* Foreground Content */}
        <div className="relative z-10 flex flex-col min-h-screen">
          <Navbar />
          <main className="grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <Routes>
              <Route path="/" element={<OverviewPage />} />
              <Route path="/triage" element={<CandidateTriagePage />} />
              <Route path="/deep-dive" element={<CandidateDeepDivePage />} />
              <Route path="/quantum" element={<QuantumLabPage />} />
              <Route path="/mechanism" element={<StructuralMechanismPage />} />
              <Route path="/pipeline" element={<PipelinePage />} />
              <Route path="/provenance" element={<ProvenancePage />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
