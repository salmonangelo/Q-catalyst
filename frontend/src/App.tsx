import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Navbar } from '@/components/layout/Navbar';
import { HeaderBanner } from '@/components/layout/HeaderBanner';
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
      <div className="min-h-screen flex flex-col bg-[#FAF9F6]">
        <HeaderBanner />
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
    </BrowserRouter>
  );
}

export default App;
