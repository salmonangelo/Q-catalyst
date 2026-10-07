"""Pydantic schema definitions for the Q-Catalyst FastAPI backend."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    app_name: str = "Q-Catalyst API"
    timestamp: str


class TopCandidateHighlight(BaseModel):
    candidate_id: str
    mature_mutation: str
    crystal_mutation: str
    role: str
    fusion_score: float
    decision_status: str
    confidence_label: str
    evidence_coverage: str


class QuantumHighlight(BaseModel):
    active_space: str = "4e, 4o"
    num_qubits: int = 8
    num_pauli_terms: int = 61
    casci_energy: float
    vqe_energy: float
    absolute_error: float
    backend: str = "Qiskit_Statevector_VQE"


class OverviewResponse(BaseModel):
    target_enzyme: str = "IsPETase (PDB 5XJH)"
    organism: str = "Ideonella sakaiensis 201-F6"
    active_run_id: Optional[str]
    total_candidates: int
    stages_completed: int
    total_stages: int = 7
    top_candidate: TopCandidateHighlight
    quantum_highlight: QuantumHighlight
    provenance_badge: str = "DEMO EVALUATION FIXTURE (SYNTHETIC BENCHMARK DATA)"


class CandidateSummary(BaseModel):
    rank: int
    candidate_id: str
    mutations: str
    crystal_mutation: str
    role: str
    fusion_score: float
    decision_status: str
    confidence_label: str
    evidence_coverage: str
    protein_ai_score: float
    uncertainty_quality_score: float
    mechanism_proximity_score: float
    chemistry_score: float
    quantum_score: Optional[float] = None
    diversity_score: float
    vqe_casci_error: Optional[float] = None
    quantum_available: bool


class CandidatesListResponse(BaseModel):
    count: int
    candidates: List[CandidateSummary]


class RadarScoreProfile(BaseModel):
    protein_ai: float
    uncertainty_quality: float
    mechanism_proximity: float
    chemistry: float
    quantum: float
    diversity: float


class CandidateExplanation(BaseModel):
    summary: str
    positive_factors: List[str]
    negative_factors: List[str]
    missing_evidence: List[str]
    limitations: List[str]


class CandidateDetailResponse(BaseModel):
    candidate: CandidateSummary
    radar_scores: RadarScoreProfile
    explanation: CandidateExplanation
    mature_numbering: str
    crystal_numbering: str
    functional_role: str
    active_site_distance_angstrom: Optional[float] = None
    conformal_lower_bound: Optional[float] = None
    conformal_upper_bound: Optional[float] = None


class QuantumHistoryPoint(BaseModel):
    iteration: int
    energy: float


class QuantumDetailsResponse(BaseModel):
    active_space_electrons: int = 4
    active_space_orbitals: int = 4
    num_qubits: int = 8
    num_pauli_terms: int = 61
    mapping_method: str = "Jordan-Wigner"
    ansatz_type: str = "TwoLocal"
    optimizer: str = "COBYLA"
    iterations: int = 101
    casci_energy: float
    vqe_energy: float
    absolute_error: float
    noise_enabled: bool = False
    noise_model: str = "none"
    noisy_energy: Optional[float] = None
    noisy_error: Optional[float] = None
    backend: str = "Qiskit_Statevector_VQE"
    simulation_note: str = "Classical simulation of 8-qubit active-space Hamiltonian"


class QuantumHistoryResponse(BaseModel):
    casci_reference_energy: float
    final_vqe_energy: float
    history: List[QuantumHistoryPoint]


class StructuralDistancePair(BaseModel):
    residue_pair: str
    distance_angstrom: float
    functional_state: str
    status: str


class CatalyticResidueGroup(BaseModel):
    group_name: str
    description: str
    residues: List[str]


class StructureResponse(BaseModel):
    pdb_id: str = "5XJH"
    resolution_angstrom: float = 1.58
    catalytic_groups: List[CatalyticResidueGroup]
    distance_matrix: List[StructuralDistancePair]
    mechanism_gate_cutoff_angstrom: float = 6.0


class PipelineStageDetail(BaseModel):
    stage_id: str
    name: str
    status: str
    duration_seconds: Optional[float] = None
    artifact_path: str
    description: str


class PipelineResponse(BaseModel):
    run_id: Optional[str]
    timestamp: Optional[str]
    pipeline_version: str = "0.1.0"
    all_stages_successful: bool
    stages: List[PipelineStageDetail]


class ProvenanceDisclaimer(BaseModel):
    title: str
    category: str
    description: str


class ProvenanceResponse(BaseModel):
    disclaimers: List[ProvenanceDisclaimer]
    software_stack: Dict[str, str]
    quantum_backend: str
    data_quality_tier: str
