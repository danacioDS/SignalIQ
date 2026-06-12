"""
Architecture Invariants Tests
These tests enforce structural rules that cannot be violated.
If they fail, the system architecture is compromised.
"""

import pytest
import os
import ast
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

@pytest.mark.smoke
def test_only_one_layer4_orchestrator():
    count = 0
    for root, dirs, files in os.walk('layers'):
        for file in files:
            if file.endswith('.py') and 'orchestrator' in file:
                with open(os.path.join(root, file)) as f:
                    content = f.read()
                    if 'class Layer4Orchestrator' in content:
                        count += 1
    assert count == 1, f"Found {count} Layer4Orchestrator classes. Expected 1."

@pytest.mark.smoke
def test_no_circular_imports():
    import layers
    import layers.llm_router
    import layers.system_config
    import backend.app

@pytest.mark.smoke
def test_ndi_formula_consistency():
    formula_pattern = "sentiment_zscore - momentum_zscore"
    matches = []
    for root, dirs, files in os.walk('layers'):
        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(root, file)) as f:
                    content = f.read()
                    if 'def calculate_ndi' in content:
                        if formula_pattern not in content and 'return sentiment_zscore - momentum_zscore' not in content:
                            matches.append(os.path.join(root, file))
    assert len(matches) == 0, f"Files defining calculate_ndi without standard formula: {matches}"

@pytest.mark.smoke
def test_no_sys_exit_in_libraries():
    violations = []
    for root, dirs, files in os.walk('ingestion'):
        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(root, file)) as f:
                    for i, line in enumerate(f):
                        if 'sys.exit' in line and '__main__' not in line:
                            violations.append(f"{file}:{i}")
    for root, dirs, files in os.walk('layers'):
        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(root, file)) as f:
                    for i, line in enumerate(f):
                        if 'sys.exit' in line and '__main__' not in line:
                            violations.append(f"{file}:{i}")
    assert len(violations) == 0, f"sys.exit() found in: {violations}"
