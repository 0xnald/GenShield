import pytest
import json

def test_genshield_audit_safe(direct_vm, direct_deploy, direct_alice):
    # Deploy GenShield with min_fee = 1000
    genshield = direct_deploy("contracts/genshield.py", 1000)
    from genlayer import Address
    
    # Check min fee view
    assert genshield.get_min_fee() == 1000

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
    cert = genshield.get_certificate(code_hash)
    assert cert["is_safe"] is True
    assert cert["contract_name"] == "DummyContract"
    assert cert["score"] == 95
    assert cert["auditor"] == Address(direct_alice).as_hex
    assert len(cert["timestamp"]) > 0

    # Reset mocks
    direct_vm.clear_mocks()

def test_genshield_audit_unsafe(direct_vm, direct_deploy, direct_alice):
    genshield = direct_deploy("contracts/genshield.py", 1000)
    
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
    
    # Verify certificate is registered but is_safe is False
    cert = genshield.get_certificate(code_hash)
    assert cert != {}
    assert cert["is_safe"] is False
    assert cert["score"] == 20
    assert cert["contract_name"] == "UnsafeContract"
    vulnerabilities = json.loads(cert["vulnerabilities_json"])
    assert len(vulnerabilities) == 1
    assert vulnerabilities[0]["type"] == "forbidden_import"
    assert vulnerabilities[0]["severity"] == "high"

    direct_vm.clear_mocks()

def test_genshield_insufficient_payment(direct_vm, direct_deploy, direct_alice):
    genshield = direct_deploy("contracts/genshield.py", 1000)
    
    direct_vm.sender = direct_alice
    direct_vm.value = 500  # Less than min_fee of 1000

    with direct_vm.expect_revert("Insufficient payment for audit fee"):
        genshield.submit_audit("DummyContract", "code")

def test_genshield_owner_and_fee_update(direct_vm, direct_deploy, direct_alice):
    # Deploy contract
    direct_vm.sender = direct_alice
    genshield = direct_deploy("contracts/genshield.py", 1000)
    from genlayer import Address

    # Verify owner view returns alice's address hex
    assert genshield.get_owner() == Address(direct_alice).as_hex

    # Bob (non-owner) tries to update the fee, which should revert
    bob = b"\x02" * 20
    direct_vm.sender = bob
    with direct_vm.expect_revert("Only the owner can update the minimum fee"):
        genshield.update_min_fee(2000)

    # Alice (owner) updates the fee to 2000
    direct_vm.sender = direct_alice
    genshield.update_min_fee(2000)
    assert genshield.get_min_fee() == 2000
