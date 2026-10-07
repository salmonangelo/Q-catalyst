"""Automated headless UI testing for Q-Catalyst Streamlit application using Streamlit AppTest framework."""

import io
import sys
from pathlib import Path
from streamlit.testing.v1 import AppTest

# Reconfigure stdout for utf-8 on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

def test_app_overview_and_navigation():
    print("Testing Q-Catalyst Streamlit Application via Streamlit AppTest...")
    app_path = Path("app/app.py").resolve()
    
    # Initialize and run app
    at = AppTest.from_file(str(app_path), default_timeout=30)
    at.run()
    
    # 1. Verify Overview page
    assert not at.exception, f"App encountered an exception on initial load: {at.exception}"
    print("[PASS] Initial load (Overview & Vision) rendered without errors.")
    
    # 2. Test Navigation to Candidate Triage
    print("Testing navigation to '🎯 Candidate Triage'...")
    radio = at.sidebar.radio[0]
    radio.set_value("🎯 Candidate Triage")
    at.run()
    assert not at.exception, f"Candidate Triage encountered an exception: {at.exception}"
    print("[PASS] Candidate Triage rendered without errors.")
    
    # 3. Test Navigation to Candidate Deep-Dive
    print("Testing navigation to '🔬 Candidate Deep-Dive'...")
    radio.set_value("🔬 Candidate Deep-Dive")
    at.run()
    assert not at.exception, f"Candidate Deep-Dive encountered an exception: {at.exception}"
    print("[PASS] Candidate Deep-Dive rendered without errors.")
    
    # 4. Test Navigation to Quantum Lab
    print("Testing navigation to '⚛️ Quantum Lab'...")
    radio.set_value("⚛️ Quantum Lab")
    at.run()
    assert not at.exception, f"Quantum Lab encountered an exception: {at.exception}"
    print("[PASS] Quantum Lab rendered without errors.")
    
    # 5. Test Navigation to Structural Mechanism
    print("Testing navigation to '🧬 Structural Mechanism'...")
    radio.set_value("🧬 Structural Mechanism")
    at.run()
    assert not at.exception, f"Structural Mechanism encountered an exception: {at.exception}"
    print("[PASS] Structural Mechanism rendered without errors.")
    
    # 6. Test Navigation to Pipeline & Provenance
    print("Testing navigation to '⚡ Pipeline & Provenance'...")
    radio.set_value("⚡ Pipeline & Provenance")
    at.run()
    assert not at.exception, f"Pipeline & Provenance encountered an exception: {at.exception}"
    print("[PASS] Pipeline & Provenance rendered without errors.")
    
    print("\n[ALL 6 VIEWS VERIFIED SUCCESSFULLY VIA STREAMLIT HEADLESS APPTEST]")

if __name__ == "__main__":
    test_app_overview_and_navigation()
