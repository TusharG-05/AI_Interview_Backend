#!/usr/bin/env python
"""
WebSocket Test Runner - Comprehensive Test Suite Executor

Runs all WebSocket tests with detailed reporting and summary statistics.

Usage:
    python run_websocket_tests.py [--verbose] [--pattern TEST_PATTERN]
    
Environment Variables Required:
    LIVE_INTERVIEW_BASE_URL
    LIVE_INTERVIEW_ADMIN_EMAIL
    LIVE_INTERVIEW_ADMIN_PASSWORD
    LIVE_INTERVIEW_CANDIDATE_EMAIL
    LIVE_INTERVIEW_CANDIDATE_PASSWORD
"""

import sys
import os
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


def check_env_vars() -> bool:
    """Check if required environment variables are set"""
    required_vars = [
        "LIVE_INTERVIEW_BASE_URL",
        "LIVE_INTERVIEW_ADMIN_EMAIL",
        "LIVE_INTERVIEW_ADMIN_PASSWORD",
        "LIVE_INTERVIEW_CANDIDATE_EMAIL",
        "LIVE_INTERVIEW_CANDIDATE_PASSWORD",
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print("❌ Missing Environment Variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nSet these before running tests:")
        print("  export LIVE_INTERVIEW_BASE_URL=http://localhost:8000")
        print("  export LIVE_INTERVIEW_ADMIN_EMAIL=admin@example.com")
        print("  export LIVE_INTERVIEW_ADMIN_PASSWORD=password")
        print("  export LIVE_INTERVIEW_CANDIDATE_EMAIL=candidate@example.com")
        print("  export LIVE_INTERVIEW_CANDIDATE_PASSWORD=password")
        return False
    
    return True


def print_header():
    """Print test run header"""
    print("\n" + "="*70)
    print("  WebSocket Integration Tests - Live Backend")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Backend URL: {os.getenv('LIVE_INTERVIEW_BASE_URL')}")
    print("="*70 + "\n")


def print_footer(passed: int, failed: int, skipped: int, total: int, duration: float):
    """Print test run footer with summary"""
    print("\n" + "="*70)
    print("  Test Run Summary")
    print("="*70)
    
    status = "✅ PASSED" if failed == 0 else "❌ FAILED"
    
    print(f"\nStatus: {status}")
    print(f"Total:   {total} tests")
    print(f"Passed:  {passed} ✅")
    print(f"Failed:  {failed} ❌")
    print(f"Skipped: {skipped} ⏭️")
    print(f"Duration: {duration:.2f}s")
    
    if failed == 0 and passed > 0:
        print(f"\n🎉 All {passed} tests passed!")
    elif failed > 0:
        print(f"\n⚠️  {failed} test(s) failed. Check logs above for details.")
    
    print("="*70 + "\n")
    
    return 0 if failed == 0 else 1


def run_tests(verbose: bool = True, pattern: str = None) -> int:
    """Run WebSocket tests and return exit code"""
    
    # Build pytest command
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/integration/test_websocket_events.py",
        "-v",
        "-s",
        "--tb=short",
        "--log-cli-level=INFO",
    ]
    
    if verbose:
        cmd.append("--verbose")
    
    if pattern:
        cmd.append(f"-k {pattern}")
    
    # Run tests
    result = subprocess.run(
        cmd,
        cwd=Path(__file__).parent,
        capture_output=False,
        text=True
    )
    
    return result.returncode


def run_specific_test_groups() -> int:
    """Run tests grouped by category with summaries"""
    
    test_groups = {
        "Connection Tests": [
            "test_candidate_websocket_connect",
            "test_admin_websocket_connect",
            "test_websocket_invalid_interview_id",
            "test_websocket_disconnection_handling",
        ],
        "Multi-Client Tests": [
            "test_multiple_admin_connections",
            "test_multiple_clients_same_interview",
        ],
        "Violation Broadcast Tests": [
            "test_violation_event_broadcast_to_candidate",
            "test_violation_event_broadcast_to_admin",
        ],
        "Status Change Tests": [
            "test_interview_started_event",
            "test_interview_completed_event",
        ],
        "Error Handling Tests": [
            "test_websocket_reconnection_after_disconnect",
            "test_websocket_missing_token_param",
        ],
    }
    
    total_passed = 0
    total_failed = 0
    total_skipped = 0
    
    for group_name, tests in test_groups.items():
        print(f"\n{'─'*70}")
        print(f"  {group_name}")
        print(f"{'─'*70}\n")
        
        for test_name in tests:
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                f"tests/integration/test_websocket_events.py::{test_name}",
                "-v",
                "-s",
                "--tb=line",
            ]
            
            result = subprocess.run(
                cmd,
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True
            )
            
            # Parse result
            if "PASSED" in result.stdout:
                status = "✅ PASSED"
                total_passed += 1
            elif "FAILED" in result.stdout:
                status = "❌ FAILED"
                total_failed += 1
            elif "SKIPPED" in result.stdout:
                status = "⏭️ SKIPPED"
                total_skipped += 1
            else:
                status = "⚠️  UNKNOWN"
            
            print(f"  {test_name}: {status}")
    
    print(f"\n{'─'*70}")
    print(f"  Total: {total_passed} passed, {total_failed} failed, {total_skipped} skipped")
    print(f"{'─'*70}\n")
    
    return 0 if total_failed == 0 else 1


def main():
    """Main entry point"""
    
    # Check environment
    if not check_env_vars():
        return 1
    
    print_header()
    
    # Run tests
    exit_code = run_tests(verbose=True)
    
    if exit_code != 0:
        print("\n⚠️  Some tests failed. Running grouped test summary...\n")
        # Optionally run grouped tests for more detail
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
