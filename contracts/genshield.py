# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import typing

@allow_storage
@dataclass
class AuditCertificate:
    contract_name: str
    code_hash: str
    auditor: Address
    score: u32
    is_safe: bool
    timestamp: str

class GenShield(gl.Contract):
    certificates: TreeMap[str, AuditCertificate]
    min_fee: u256

    def __init__(self, min_fee: u256):
        self.min_fee = min_fee
        self.certificates = TreeMap()

    @gl.public.write.payable
    def submit_audit(self, contract_name: str, code: str) -> str:
        if gl.message.value < self.min_fee:
            raise gl.vm.UserError("Insufficient payment for audit fee")
        
        if len(code) > 20000:
            raise gl.vm.UserError("Contract code exceeds maximum length of 20000 characters")

        code_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()

        prompt = f"""
        You are a smart contract security auditor specializing in GenLayer Python Intelligent Contracts.
        Analyze the following Python contract code for security flaws, prompt injections, incorrect storage layouts, and non-deterministic violations.
        
        Follow these specific rules:
        1. Storage Layout:
           - Check that all persistent fields are declared inside the class body with type annotations.
           - Ensure persistent collections use 'TreeMap' instead of 'dict', and 'DynArray' instead of 'list'.
           - Ensure sized integer types (e.g. 'u256', 'i32', 'u8') are used instead of general 'int'.
        2. Non-Deterministic Violations:
           - All 'gl.nondet.*' calls (like web requests, LLM prompts) MUST be inside a non-deterministic block.
           - NO storage writes (like 'self.x = ...'), contract calls, or message emissions are allowed inside non-deterministic blocks.
        3. Forbidden Imports:
           - Check for imports like 'os', 'sys', 'subprocess', or 'socket' which are forbidden in GenVM.
        4. Prompt Injection:
           - Check if user inputs are concatenated directly into prompt strings without sanitization or structural wrapping.

        Respond ONLY in the following JSON format:
        {{
            "is_safe": true/false,
            "vulnerabilities": [
                {{"type": "category", "description": "detail", "severity": "high/medium/low", "line": 12}}
            ],
            "score": 0 to 100
        }}
        
        Contract Code:
        {code}
        """

        def leader_fn():
            res = gl.nondet.exec_prompt(prompt, response_format="json")
            return res

        def validator_fn(leaders_res) -> bool:
            if not isinstance(leaders_res, gl.vm.Return):
                return False
            
            data = leaders_res.calldata
            
            if not isinstance(data, dict):
                return False
            if "is_safe" not in data or "score" not in data:
                return False
            
            my_res = leader_fn()
            
            # Check safety consensus
            if my_res.get("is_safe") != data.get("is_safe"):
                return False
                
            # Allow minor differences in score up to 15 points
            try:
                score_diff = abs(int(my_res.get("score", 0)) - int(data.get("score", 0)))
                if score_diff > 15:
                    return False
            except Exception:
                return False
                
            return True

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        
        now = datetime.now(timezone.utc).isoformat()
        
        if result.get("is_safe", False):
            cert = AuditCertificate(
                contract_name=contract_name,
                code_hash=code_hash,
                auditor=gl.message.sender_address,
                score=u32(int(result.get("score", 0))),
                is_safe=True,
                timestamp=now
            )
            self.certificates[code_hash] = cert
            
        return code_hash

    @gl.public.view
    def get_certificate(self, code_hash: str) -> dict:
        cert = self.certificates.get(code_hash, None)
        if cert is None:
            return {}
        return {
            "contract_name": cert.contract_name,
            "code_hash": cert.code_hash,
            "auditor": str(cert.auditor),
            "score": int(cert.score),
            "is_safe": cert.is_safe,
            "timestamp": cert.timestamp
        }

    @gl.public.view
    def get_min_fee(self) -> u256:
        return self.min_fee
