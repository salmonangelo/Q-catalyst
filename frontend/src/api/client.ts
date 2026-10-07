/** API client for Q-Catalyst frontend */

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

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

async function fetchJson<T>(endpoint: string): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url);
    if (!res.ok) {
      throw new Error(`API Error ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (err) {
    console.warn(`Fetch to ${url} failed. Using built-in local fallback data.`, err);
    throw err;
  }
}

export const api = {
  getHealth: () => fetchJson<HealthResponse>('/api/health'),
  getOverview: () => fetchJson<OverviewResponse>('/api/overview'),
  getCandidates: () => fetchJson<CandidatesListResponse>('/api/candidates'),
  getCandidateDetail: (id: string) => fetchJson<CandidateDetailResponse>(`/api/candidates/${encodeURIComponent(id)}`),
  getQuantum: () => fetchJson<QuantumDetailsResponse>('/api/quantum'),
  getQuantumHistory: () => fetchJson<QuantumHistoryResponse>('/api/quantum/history'),
  getStructure: () => fetchJson<StructureResponse>('/api/structure'),
  getPipeline: () => fetchJson<PipelineResponse>('/api/pipeline'),
  getProvenance: () => fetchJson<ProvenanceResponse>('/api/provenance'),
};
