#!/usr/bin/env python
"""
Quick Test Setup & Verification Script

This script:
1. Checks if pytest-asyncio is installed
2. Verifies test file syntax
3. Checks environment variables
4. Provides one-command test execution

Usage:
    python verify_websocket_tests.py
"""

import sys
import os
import subprocess
from pathlib import Path


def check_imports():
    """Check if required packages are installed"""
    print("Checking required packages...")
    
    missing = []
    
    try:
        import pytest
        print("  ✅ pytest")
    except ImportError:
        missing.append("pytest")
        print("  ❌ pytest")
    
    try:
        import pytest_asyncio
        print("  ✅ pytest-asyncio")
    except ImportError:
        missing.append("pytest-asyncio")
        print("  ❌ pytest-asyncio")
    
    try:
        import websockets
        print("  ✅ websockets")
    except ImportError:
        missing.append("websockets")
        print("  ❌ websockets")
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    
    return True


def check_test_file():
    """Check if test file exists and is valid"""
    print("\nChecking test file...")
    
    test_file = Path("tests/integration/test_websocket_events.py")
    
    if not test_file.exists():
        print(f"  ❌ Test file not found: {test_file}")
        return False
    
    print(f"  ✅ Test file found: {test_file}")
    
    # Check syntax
    try:
        with open(test_file) as f:
            compile(f.read(), str(test_file), 'exec')
        print(f"  ✅ Syntax valid")
        return True
    except SyntaxError as e:
        print(f"  ❌ Syntax error: {e}")
        return False


def check_env_vars():
    """Check environment variables"""
    print("\nChecking environment variables...")
    
    required_vars = {
        "LIVE_INTERVIEW_BASE_URL": "http://localhost:8000",
        "LIVE_INTERVIEW_ADMIN_EMAIL": "admin@example.com",
        "LIVE_INTERVIEW_ADMIN_PASSWORD": "password",
        "LIVE_INTERVIEW_CANDIDATE_EMAIL": "candidate@example.com",
        "LIVE_INTERVIEW_CANDIDATE_PASSWORD": "password",
    }
    
    missing = {}
    for var, example in required_vars.items():
        if os.getenv(var):
            print(f"  ✅ {var}")
        else:
            print(f"  ❌ {var} (example: {example})")
            missing[var] = example
    
    if missing:
        print("\n⚠️  Missing environment variables!")
        print("\nSet them using one of these methods:\n")
        
        print("Python:")
        for var, example in missing.items():
            print(f'  os.environ["{var}"] = "{example}"')
        
        print("\nBash/Linux/Mac:")
        for var, example in missing.items():
            print(f'  export {var}="{example}"')
        
        print("\nPowerShell:")
        for var, example in missing.items():
            print(f'  $env:{var} = "{example}"')
        
        print("\nWindows CMD:")
        for var, example in missing.items():
            print(f'  set {var}={example}')
        
        return False
    
    return True


def show_test_options():
    """Show available test options"""
    print("\n" + "="*70)
    print("Available Test Commands")
    print("="*70)
    
    commands = [
        ("All tests", "pytest tests/integration/test_websocket_events.py -v -s"),
        ("Connection tests", "pytest tests/integration/test_websocket_events.py::test_candidate_websocket_connect -v -s"),
        ("Event tests", "pytest tests/integration/test_websocket_events.py::test_interview_started_event -v -s"),
        ("With coverage", "pytest tests/integration/test_websocket_events.py --cov=app -v -s"),
        ("Quiet mode", "pytest tests/integration/test_websocket_events.py -q"),
    ]
    
    for i, (desc, cmd) in enumerate(commands, 1):
        print(f"\n{i}. {desc}:")
        print(f"   {cmd}")
    
    print("\n" + "="*70)


def run_verification():
    """Run verification and show results"""
    print("\n" + "="*70)
    print("WebSocket Test Setup Verification")
    print("="*70)
    
    all_ok = True
    
    # Check imports
    if not check_imports():
        all_ok = False
    
    # Check test file
    if not check_test_file():
        all_ok = False
    
    # Check env vars
    if not check_env_vars():
        all_ok = False
    
    print("\n" + "="*70)
    
    if all_ok:
        print("✅ All checks passed! Ready to run tests.\n")
        show_test_options()
        
        # Suggest running tests
        print("\nQuick start (set env vars first):")
        print("  pytest tests/integration/test_websocket_events.py -v -s\n")
        
        return 0
    else:
        print("❌ Some checks failed. See above for details.\n")
        return 1


if __name__ == "__main__":
    sys.exit(run_verification())
