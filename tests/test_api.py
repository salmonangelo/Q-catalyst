"""Automated test suite for FastAPI backend endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_api_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_api_overview_endpoint():
    resp = client.get("/api/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["target_enzyme"] == "IsPETase (PDB 5XJH)"
    assert data["total_stages"] == 7
    assert "top_candidate" in data
    assert data["top_candidate"]["candidate_id"] is not None
    assert "quantum_highlight" in data
    assert data["quantum_highlight"]["num_pauli_terms"] == 61
    assert data["quantum_highlight"]["num_qubits"] == 8


def test_api_candidates_list():
    resp = client.get("/api/candidates")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] > 0
    assert len(data["candidates"]) == data["count"]
    first = data["candidates"][0]
    assert "rank" in first
    assert "candidate_id" in first
    assert "fusion_score" in first
    assert "decision_status" in first


def test_api_candidate_detail_found():
    resp = client.get("/api/candidates")
    first_id = resp.json()["candidates"][0]["candidate_id"]
    
    det_resp = client.get(f"/api/candidates/{first_id}")
    assert det_resp.status_code == 200
    det = det_resp.json()
    assert det["candidate"]["candidate_id"] == first_id
    assert "radar_scores" in det
    assert "explanation" in det
    assert len(det["explanation"]["positive_factors"]) > 0


def test_api_candidate_detail_not_found():
    resp = client.get("/api/candidates/NON_EXISTENT_VAR")
    assert resp.status_code == 404


def test_api_quantum_endpoints():
    resp = client.get("/api/quantum")
    assert resp.status_code == 200
    q = resp.json()
    assert q["num_qubits"] == 8
    assert q["num_pauli_terms"] == 61
    assert q["casci_energy"] < 0
    assert q["vqe_energy"] < 0

    hist_resp = client.get("/api/quantum/history")
    assert hist_resp.status_code == 200
    h = hist_resp.json()
    assert len(h["history"]) > 0
    assert h["casci_reference_energy"] < 0


def test_api_structure_and_pipeline():
    resp = client.get("/api/structure")
    assert resp.status_code == 200
    s = resp.json()
    assert s["pdb_id"] == "5XJH"
    assert len(s["catalytic_groups"]) == 3
    assert len(s["distance_matrix"]) >= 5

    pipe_resp = client.get("/api/pipeline")
    assert pipe_resp.status_code == 200
    p = pipe_resp.json()
    assert len(p["stages"]) == 7
    assert p["all_stages_successful"] is True

    prov_resp = client.get("/api/provenance")
    assert prov_resp.status_code == 200
    prov = prov_resp.json()
    assert len(prov["disclaimers"]) >= 4
