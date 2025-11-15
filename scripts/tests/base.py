"""
Base classes and utilities for all test scenarios.
"""

import json
import sys
import requests
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass


BASE_URL = "http://localhost:8443"
TIMEOUT = 10


@dataclass
class TestResult:
    """Test result structure."""
    success: bool
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    limitation: Optional[str] = None
    scenario: Optional[str] = None


def test_health() -> Tuple[bool, Optional[str]]:
    """Tests the health endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return True, None
        return False, f"Status code {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Could not connect to server"
    except Exception as e:
        return False, str(e)


def test_verification_request(
    request_file: Path, 
    expected_success: bool = True,
    policy_id: Optional[str] = None
) -> TestResult:
    """
    Tests a verification request.
    
    Args:
        request_file: Path to request JSON file
        expected_success: Whether success is expected (True) or failure (False)
        policy_id: Optional policy ID to override in request
        
    Returns:
        TestResult with test outcome
    """
    if not request_file.exists():
        return TestResult(
            success=False,
            error_code="FILE_NOT_FOUND",
            details={"file": str(request_file)}
        )
    
    try:
        with open(request_file, 'r', encoding='utf-8') as f:
            request_data = json.load(f)
        
        # Override policy_id if provided
        if policy_id:
            request_data["policy_id"] = policy_id
        
        response = requests.post(
            f"{BASE_URL}/verify",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        
        if expected_success:
            if response.status_code == 200:
                result = response.json()
                return TestResult(
                    success=True,
                    details={"vro_jwt": result.get("vro_jwt") is not None}
                )
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                return TestResult(
                    success=False,
                    error_code=error_data.get("detail", f"HTTP_{response.status_code}"),
                    details={"status_code": response.status_code}
                )
        else:
            # Negative test - expect failure
            if response.status_code != 200:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                error_detail = error_data.get("detail", "")
                return TestResult(
                    success=True,  # Failure is expected
                    error_code=error_detail,
                    details={"expected_failure": True}
                )
            else:
                return TestResult(
                    success=False,
                    error_code="UNEXPECTED_SUCCESS",
                    details={"message": "Expected failure but got success"}
                )
    
    except requests.exceptions.ConnectionError:
        return TestResult(
            success=False,
            error_code="CONNECTION_ERROR",
            details={"message": "Could not connect to server"}
        )
    except Exception as e:
        return TestResult(
            success=False,
            error_code="EXCEPTION",
            details={"error": str(e)}
        )


def get_base_dir() -> Path:
    """Get the project base directory."""
    return Path(__file__).parent.parent.parent


def print_test_header(scenario_name: str, description: str = ""):
    """Print formatted test header."""
    print("\n" + "=" * 70)
    print(f"{scenario_name}")
    if description:
        print(f"  {description}")
    print("=" * 70)


def print_test_result(result: TestResult, case_name: str = ""):
    """Print formatted test result."""
    if result.success:
        status = "[PASS]"
        print(f"{status} {case_name or 'Test'}: {'Success' if not result.details or not result.details.get('expected_failure') else 'Correctly rejected'}")
        if result.limitation:
            print(f"  [LIMITATION] {result.limitation}")
        if result.details:
            details_str = ", ".join([f"{k}: {v}" for k, v in result.details.items() if k != "expected_failure"])
            if details_str:
                print(f"  Details: {details_str}")
    else:
        status = "[FAIL]"
        print(f"{status} {case_name or 'Test'}: {result.error_code}")
        if result.details:
            print(f"  Details: {result.details}")


