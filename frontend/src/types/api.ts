/** TypeScript interfaces for Q-Catalyst backend API contracts */

export interface HealthResponse {
  status: string;
  version: string;
  app_name: string;
  timestamp: string;
}

export interface TopCandidateHighlight {
  candidate_id: string;
  mature_mutation: string;
  crystal_mutation: string;
  role: string;
  fusion_score: number;
  decision_status: string;
  confidence_label: string;
  evidence_coverage: string;
}

export interface QuantumHighlight {
  active_space: string;
  num_qubits: number;
  num_pauli_terms: number;
  casci_energy: number;
  vqe_energy: number;
  absolute_error: number;
  backend: string;
}

export interface OverviewResponse {
  target_enzyme: string;
  organism: string;
  active_run_id: string | null;
  total_candidates: number;
  stages_completed: number;
  total_stages: number;
  top_candidate: TopCandidateHighlight;
  quantum_highlight: QuantumHighlight;
  provenance_badge: string;
}

export interface CandidateSummary {
  rank: number;
  candidate_id: string;
  mutations: string;
  crystal_mutation: string;
  role: string;
  fusion_score: number;
  decision_status: string;
  confidence_label: string;
  evidence_coverage: string;
  protein_ai_score: number;
  uncertainty_quality_score: number;
  mechanism_proximity_score: number;
  chemistry_score: number;
  quantum_score: number | null;
  diversity_score: number;
  vqe_casci_error: number | null;
  quantum_available: boolean;
}

export interface CandidatesListResponse {
  count: number;
  candidates: CandidateSummary[];
}

export interface RadarScoreProfile {
  protein_ai: number;
  uncertainty_quality: number;
  mechanism_proximity: number;
  chemistry: number;
  quantum: number;
  diversity: number;
}

export interface CandidateExplanation {
  summary: string;
  positive_factors: string[];
  negative_factors: string[];
  missing_evidence: string[];
  limitations: string[];
}

export interface CandidateDetailResponse {
  candidate: CandidateSummary;
  radar_scores: RadarScoreProfile;
  explanation: CandidateExplanation;
  mature_numbering: string;
  crystal_numbering: string;
  functional_role: string;
  active_site_distance_angstrom: number | null;
  conformal_lower_bound: number | null;
  conformal_upper_bound: number | null;
}

export interface QuantumHistoryPoint {
  iteration: number;
  energy: number;
}

export interface QuantumDetailsResponse {
  active_space_electrons: number;
  active_space_orbitals: number;
  num_qubits: number;
  num_pauli_terms: number;
  mapping_method: string;
  ansatz_type: string;
  optimizer: string;
  iterations: number;
  casci_energy: number;
  vqe_energy: number;
  absolute_error: number;
  noise_enabled: boolean;
  noise_model: string;
  noisy_energy: number | null;
  noisy_error: number | null;
  backend: string;
  simulation_note: string;
}

export interface QuantumHistoryResponse {
  casci_reference_energy: number;
  final_vqe_energy: number;
  history: QuantumHistoryPoint[];
}

export interface StructuralDistancePair {
  residue_pair: string;
  distance_angstrom: number;
  functional_state: string;
  status: string;
}

export interface CatalyticResidueGroup {
  group_name: string;
  description: string;
  residues: string[];
}

export interface StructureResponse {
  pdb_id: string;
  resolution_angstrom: number;
  catalytic_groups: CatalyticResidueGroup[];
  distance_matrix: StructuralDistancePair[];
  mechanism_gate_cutoff_angstrom: number;
}

export interface PipelineStageDetail {
  stage_id: string;
  name: string;
  status: string;
  duration_seconds: number | null;
  artifact_path: string;
  description: string;
}

export interface PipelineResponse {
  run_id: string | null;
  timestamp: string | null;
  pipeline_version: string;
  all_stages_successful: boolean;
  stages: PipelineStageDetail[];
}

export interface ProvenanceDisclaimer {
  title: string;
  category: string;
  description: string;
}

export interface ProvenanceResponse {
  disclaimers: ProvenanceDisclaimer[];
  software_stack: Record<string, string>;
  quantum_backend: string;
  data_quality_tier: string;
}
