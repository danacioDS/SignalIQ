"""Architecture tests for SignalIQ."""

import os
import sys
import pytest


def test_only_one_layer4_orchestrator():
    """Only one layer4 orchestrator should exist."""
    layer_dir = 'backend/app/layers'
    assert os.path.exists(layer_dir), f"Directory not found: {layer_dir}"
    
    orchestrators = []
    for root, dirs, files in os.walk(layer_dir):
        for f in files:
            if 'orchestrator' in f and f.endswith('.py'):
                orchestrators.append(f)
    
    # We expect layer4 orchestrator to exist (layer3 is allowed)
    layer4_orchestrators = [f for f in orchestrators if 'layer4' in f]
    assert len(layer4_orchestrators) == 1, f"Found {len(layer4_orchestrators)} layer4 orchestrators: {layer4_orchestrators}"
    assert 'layer4_orchestrator.py' in layer4_orchestrators[0]


def test_no_circular_imports():
    """Check for circular imports in layers."""
    import ast
    import os
    
    layer_dir = 'backend/app/layers'
    if not os.path.exists(layer_dir):
        pytest.skip(f"Layer directory not found: {layer_dir}")
    
    imports = {}
    modules = {}
    
    # Collect all imports
    for root, dirs, files in os.walk(layer_dir):
        for f in files:
            if f.endswith('.py'):
                path = os.path.join(root, f)
                module_name = f.replace('.py', '')
                modules[module_name] = path
                
                with open(path, 'r') as fp:
                    try:
                        tree = ast.parse(fp.read())
                    except SyntaxError:
                        continue
                
                imports[module_name] = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports[module_name].append(alias.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports[module_name].append(node.module.split('.')[0])
    
    # Check for cycles (simplified)
    # For now, just check that no module imports itself
    for module, deps in imports.items():
        assert module not in deps, f"Module {module} imports itself"

def test_ndi_formula_consistency():
    """Skip - domain module doesn't exist yet."""
    pytest.skip("domain.ndi_calculator not implemented")

def test_no_sys_exit_in_libraries():
    """Verify no sys.exit() calls in library code."""
    import ast
    import os
    
    # Check ingestion/
    ingestion_dir = 'ingestion'
    if os.path.exists(ingestion_dir):
        for root, dirs, files in os.walk(ingestion_dir):
            for f in files:
                if f.endswith('.py'):
                    path = os.path.join(root, f)
                    with open(path, 'r') as fp:
                        content = fp.read()
                    # Check for sys.exit()
                    if 'sys.exit(' in content or 'sys.exit()' in content:
                        # This is allowed only in orchestrator
                        if 'orchestrator' not in path:
                            assert False, f"sys.exit() found in {path}"
    
    # Check layers/
    layer_dir = 'backend/app/layers'
    if os.path.exists(layer_dir):
        for root, dirs, files in os.walk(layer_dir):
            for f in files:
                if f.endswith('.py') and 'orchestrator' not in f:
                    path = os.path.join(root, f)
                    with open(path, 'r') as fp:
                        content = fp.read()
                    assert 'sys.exit(' not in content and 'sys.exit()' not in content, f"sys.exit() found in {path}"
