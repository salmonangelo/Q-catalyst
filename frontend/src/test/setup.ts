import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Global mock for ResizeObserver (used by Recharts in jsdom)
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Global mock for fetch
global.fetch = vi.fn().mockImplementation((url: string) => {
  if (url.includes('/api/health')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ status: 'ok', version: '0.1.0', app_name: 'Q-Catalyst API', timestamp: new Date().toISOString() }),
    });
  }
  if (url.includes('/api/overview')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        target_enzyme: 'IsPETase (PDB 5XJH)',
        organism: 'Ideonella sakaiensis 201-F6',
        active_run_id: 'run_test',
        total_candidates: 6,
        stages_completed: 7,
        total_stages: 7,
        top_candidate: {
          candidate_id: 'VAR_W132H',
          mature_mutation: 'W132H',
          crystal_mutation: 'W159H',
          role: 'Substrate cleft',
          fusion_score: 0.7712,
          decision_status: 'PRIORITIZE',
          confidence_label: 'HIGH_CONFIDENCE',
          evidence_coverage: '5/6 Channels',
        },
        quantum_highlight: {
          active_space: '4e, 4o',
          num_qubits: 8,
          num_pauli_terms: 61,
          casci_energy: -18.215733,
          vqe_energy: -18.206475,
          absolute_error: 0.009258,
          backend: 'Qiskit_Statevector_VQE',
        },
        provenance_badge: 'DEMO EVALUATION FIXTURE',
      }),
    });
  }
  if (url.includes('/api/candidates')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        count: 1,
        candidates: [{
          rank: 1,
          candidate_id: 'VAR_W132H',
          mutations: 'W132H',
          crystal_mutation: 'W159H',
          role: 'Substrate cleft',
          fusion_score: 0.7712,
          decision_status: 'PRIORITIZE',
          confidence_label: 'HIGH_CONFIDENCE',
          evidence_coverage: '5/6 Channels',
          protein_ai_score: 0.85,
          uncertainty_quality_score: 0.72,
          mechanism_proximity_score: 0.90,
          chemistry_score: 0.65,
          quantum_score: 0.95,
          diversity_score: 0.50,
          vqe_casci_error: 0.009258,
          quantum_available: true,
        }],
      }),
    });
  }
  if (url.includes('/api/quantum')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        active_space_electrons: 4,
        active_space_orbitals: 4,
        num_qubits: 8,
        num_pauli_terms: 61,
        mapping_method: 'Jordan-Wigner',
        ansatz_type: 'TwoLocal',
        optimizer: 'COBYLA',
        iterations: 101,
        casci_energy: -18.215733,
        vqe_energy: -18.206475,
        absolute_error: 0.009258,
        noise_enabled: false,
        noise_model: 'none',
        noisy_energy: null,
        noisy_error: null,
        backend: 'Qiskit_Statevector_VQE',
        simulation_note: 'Simulator note',
      }),
    });
  }
  if (url.includes('/api/structure')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        pdb_id: '5XJH',
        resolution_angstrom: 1.58,
        catalytic_groups: [],
        distance_matrix: [],
        mechanism_gate_cutoff_angstrom: 6.0,
      }),
    });
  }
  if (url.includes('/api/pipeline')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        run_id: 'run_test',
        timestamp: '2026-10-07T16:05:33Z',
        pipeline_version: '0.1.0',
        all_stages_successful: true,
        stages: [],
      }),
    });
  }
  if (url.includes('/api/provenance')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        disclaimers: [],
        software_stack: {},
        quantum_backend: 'Qiskit',
        data_quality_tier: 'DEMO',
      }),
    });
  }
  return Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
  });
}) as any;
