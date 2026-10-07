"""API route handlers for Q-Catalyst FastAPI backend."""

from typing import Optional
from fastapi import APIRouter, HTTPException

from backend.schemas.models import (
    CandidateDetailResponse,
    CandidatesListResponse,
    HealthResponse,
    OverviewResponse,
    PipelineResponse,
    ProvenanceResponse,
    QuantumDetailsResponse,
    QuantumHistoryResponse,
    StructureResponse,
)
from backend.services.data_service import DataService

router = APIRouter(prefix="/api", tags=["Q-Catalyst"])
service = DataService()


@router.get("/health", response_model=HealthResponse)
def get_health():
    """Health check endpoint."""
    return service.get_health()


@router.get("/overview", response_model=OverviewResponse)
def get_overview():
    """System overview and high-level triage highlight."""
    return service.get_overview()


@router.get("/candidates", response_model=CandidatesListResponse)
def get_candidates():
    """Returns the full candidate ranking matrix with multimodal scores."""
    return service.get_candidates()


@router.get("/candidates/{candidate_id}", response_model=CandidateDetailResponse)
def get_candidate_detail(candidate_id: str):
    """Returns granular radar scores, structural metadata, and explainability for a candidate."""
    detail = service.get_candidate_detail(candidate_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Candidate '{candidate_id}' not found")
    return detail


@router.get("/quantum", response_model=QuantumDetailsResponse)
def get_quantum_details():
    """Returns quantum active space parameters, CASCI vs VQE energies, and noise status."""
    return service.get_quantum_details()


@router.get("/quantum/history", response_model=QuantumHistoryResponse)
def get_quantum_history():
    """Returns iteration-by-iteration VQE optimization trajectory points."""
    return service.get_quantum_history()


@router.get("/structure", response_model=StructureResponse)
def get_structure_info():
    """Returns 5XJH catalytic triad residues and active-site distance matrix."""
    return service.get_structure_info()


@router.get("/pipeline", response_model=PipelineResponse)
def get_pipeline_status():
    """Returns 7-stage execution status, stage runtimes, and artifact paths."""
    return service.get_pipeline_status()


@router.get("/provenance", response_model=ProvenanceResponse)
def get_provenance():
    """Returns scientific disclaimers and software stack specifications."""
    return service.get_provenance()
