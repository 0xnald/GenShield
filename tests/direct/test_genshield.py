import pytest
import json

def test_genshield_audit_safe(direct_vm, direct_deploy, direct_alice):
    # Deploy GenShield with min_fee = 1000
    genshield = direct_deploy("contracts/genshield.py", args=[1000])
    
    # Check min fee view
    assert genshield.get_min_fee().call() == 1000

    # Mock the LLM response to return a safe audit result
    mock_response = {
        "is_safe": True,
        "vulnerabilities": [],
        "score": 95
    }
    direct_vm.mock_llm(r".*specializing in GenLayer Python.*", json.dumps(mock_response))

    # Configure transaction details
    direct_vm.sender = direct_alice
    direct_vm.value = 1500  # higher than min_fee

    # Target contract code to audit
    target_code = """
    # { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
    from genlayer import *
    class Dummy(gl.Contract):
        x: u256
        def __init__(self):
            self.x = 0
    """

    # Call submit_audit
    code_hash = genshield.submit_audit("DummyContract", target_code)
    
    # Verify certificate is saved
    cert = genshield.get_certificate(code_hash).call()
    assert cert["is_safe"] is True
    assert cert["contract_name"] == "DummyContract"
    assert cert["score"] == 95
    assert cert["auditor"] == str(direct_alice)
    assert len(cert["timestamp"]) > 0

    # Reset mocks
    direct_vm.clear_mocks()

def test_genshield_audit_unsafe(direct_vm, direct_deploy, direct_alice):
    genshield = direct_deploy("contracts/genshield.py", args=[1000])
    
    # Mock the LLM response to return an unsafe audit result
    mock_response = {
        "is_safe": False,
        "vulnerabilities": [
            {"type": "forbidden_import", "description": "Import of 'os' is forbidden", "severity": "high", "line": 3}
        ],
        "score": 20
    }
    direct_vm.mock_llm(r".*specializing in GenLayer Python.*", json.dumps(mock_response))

    direct_vm.sender = direct_alice
    direct_vm.value = 1000

    unsafe_code = """
    import os
    class Dummy:
        pass
    """

    code_hash = genshield.submit_audit("UnsafeContract", unsafe_code)
    
    # Verify no certificate is registered because is_safe is False
    cert = genshield.get_certificate(code_hash).call()
    assert cert == {}

    direct_vm.clear_mocks()

def test_genshield_insufficient_payment(direct_vm, direct_deploy, direct_alice):
    genshield = direct_deploy("contracts/genshield.py", args=[1000])
    
    direct_vm.sender = direct_alice
    direct_vm.value = 500  # Less than min_fee of 1000

    with direct_vm.expect_revert("Insufficient payment for audit fee"):
        genshield.submit_audit("DummyContract", "code")
