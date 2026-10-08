/** API client for Q-Catalyst frontend with automatic fallback support for static hosting (e.g. Vercel) */

import {
  CandidateDetailResponse,
  CandidatesListResponse,
  HealthResponse,
  OverviewResponse,
  PipelineResponse,
  ProvenanceResponse,
  QuantumDetailsResponse,
  QuantumHistoryResponse,
  StructureResponse,
} from '@/types/api';

import {
  fallbackCandidates,
  fallbackCandidateDetails,
  fallbackHealth,
  fallbackOverview,
  fallbackPipeline,
  fallbackProvenance,
  fallbackQuantum,
  fallbackQuantumHistory,
  fallbackStructure,
} from './mockData';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

async function fetchWithFallback<T>(endpoint: string, fallbackValue: T): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url);
    if (!res.ok) {
      throw new Error(`API Error ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (err) {
    // Graceful fallback for static deployments (Vercel) without active backend instance
    return fallbackValue;
  }
}

export const api = {
  getHealth: () => fetchWithFallback<HealthResponse>('/api/health', fallbackHealth),
  getOverview: () => fetchWithFallback<OverviewResponse>('/api/overview', fallbackOverview),
  getCandidates: () => fetchWithFallback<CandidatesListResponse>('/api/candidates', fallbackCandidates),
  getCandidateDetail: (id: string) => {
    const fallback = fallbackCandidateDetails[id] || {
      ...fallbackCandidateDetails['VAR_W132H'],
      candidate: fallbackCandidates.candidates.find((c) => c.candidate_id === id) || fallbackCandidates.candidates[0],
    };
    return fetchWithFallback<CandidateDetailResponse>(`/api/candidates/${encodeURIComponent(id)}`, fallback);
  },
  getQuantum: () => fetchWithFallback<QuantumDetailsResponse>('/api/quantum', fallbackQuantum),
  getQuantumHistory: () => fetchWithFallback<QuantumHistoryResponse>('/api/quantum/history', fallbackQuantumHistory),
  getStructure: () => fetchWithFallback<StructureResponse>('/api/structure', fallbackStructure),
  getPipeline: () => fetchWithFallback<PipelineResponse>('/api/pipeline', fallbackPipeline),
  getProvenance: () => fetchWithFallback<ProvenanceResponse>('/api/provenance', fallbackProvenance),
};
