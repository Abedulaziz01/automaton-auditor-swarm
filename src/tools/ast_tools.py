"""
AST parsing tools for code analysis
Production-grade AST analysis for detective work
"""

import ast
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import subprocess

class ASTAnalyzer:
    """Production-grade AST analysis tools"""
    
    @staticmethod
    def parse_python_file(file_path: Union[str, Path]) -> Optional[ast.AST]:
        """Safely parse a Python file with error handling"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                print(f"File not found: {file_path}")
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return ast.parse(content)
            
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}")
            return None
        except UnicodeDecodeError as e:
            print(f"Encoding error in {file_path}: {e}")
            return None
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None
    
    @staticmethod
    def find_class_definitions(tree: ast.AST, base_class: str) -> List[Dict]:
        """Find all classes inheriting from a specific base class"""
        findings = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    # Handle different base class representations
                    if isinstance(base, ast.Name) and base.id == base_class:
                        findings.append({
                            'class_name': node.name,
                            'line': node.lineno,
                            'base_class': base_class,
                            'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                            'decorators': [ast.unparse(d) for d in node.decorator_list] if hasattr(ast, 'unparse') else []
                        })
                    elif isinstance(base, ast.Attribute) and base.attr == base_class:
                        findings.append({
                            'class_name': node.name,
                            'line': node.lineno,
                            'base_class': f"{base.value.id}.{base.attr}" if hasattr(base.value, 'id') else base_class,
                            'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                        })
        
        return findings
    
    @staticmethod
    def find_function_calls(tree: ast.AST, function_name: str) -> List[Dict]:
        """Find all calls to a specific function"""
        findings = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Method call like obj.method()
                if isinstance(node.func, ast.Attribute) and node.func.attr == function_name:
                    findings.append({
                        'type': 'method_call',
                        'object': ast.unparse(node.func.value) if hasattr(ast, 'unparse') else 'unknown',
                        'method': function_name,
                        'line': node.lineno,
                        'args': [ast.unparse(arg) for arg in node.args] if hasattr(ast, 'unparse') else [],
                        'keywords': {kw.arg: ast.unparse(kw.value) for kw in node.keywords if kw.arg} if hasattr(ast, 'unparse') else {}
                    })
                
                # Function call like function()
                elif isinstance(node.func, ast.Name) and node.func.id == function_name:
                    findings.append({
                        'type': 'function_call',
                        'function': function_name,
                        'line': node.lineno,
                        'args': [ast.unparse(arg) for arg in node.args] if hasattr(ast, 'unparse') else [],
                        'keywords': {kw.arg: ast.unparse(kw.value) for kw in node.keywords if kw.arg} if hasattr(ast, 'unparse') else {}
                    })
        
        return findings
    
    @staticmethod
    def detect_graph_structure(tree: ast.AST) -> Dict:
        """Detect StateGraph structure in AST"""
        result = {
            'has_stategraph': False,
            'add_edge_calls': [],
            'add_node_calls': [],
            'fan_out_detected': False,
            'fan_in_detected': False,
            'parallel_branches': []
        }
        
        # Track node connections for fan-out detection
        node_connections = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Detect StateGraph instantiation
                if isinstance(node.func, ast.Attribute) and node.func.attr == 'StateGraph':
                    result['has_stategraph'] = True
                
                # Detect add_node calls
                if isinstance(node.func, ast.Attribute) and node.func.attr == 'add_node':
                    node_info = {
                        'line': node.lineno,
                        'args': [ast.unparse(arg) for arg in node.args] if hasattr(ast, 'unparse') else []
                    }
                    result['add_node_calls'].append(node_info)
                    
                    # Track node name if available
                    if node.args and hasattr(ast, 'unparse'):
                        node_name = ast.unparse(node.args[0])
                        node_connections[node_name] = []
                
                # Detect add_edge calls
                if isinstance(node.func, ast.Attribute) and node.func.attr == 'add_edge':
                    edge_info = {
                        'line': node.lineno,
                        'args': [ast.unparse(arg) for arg in node.args] if hasattr(ast, 'unparse') else []
                    }
                    result['add_edge_calls'].append(edge_info)
                    
                    # Track connections for fan-out detection
                    if len(node.args) >= 2 and hasattr(ast, 'unparse'):
                        source = ast.unparse(node.args[0])
                        target = ast.unparse(node.args[1])
                        if source in node_connections:
                            node_connections[source].append(target)
                        else:
                            node_connections[source] = [target]
        
        # Detect fan-out (nodes with multiple outgoing edges)
        for source, targets in node_connections.items():
            if len(targets) > 1:
                result['fan_out_detected'] = True
                result['parallel_branches'].append({
                    'source': source,
                    'targets': targets,
                    'branch_count': len(targets)
                })
        
        return result
    
    @staticmethod
    def check_tool_safety(tree: ast.AST) -> List[Dict]:
        """Check for unsafe tool usage patterns"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for os.system
                if isinstance(node.func, ast.Attribute) and node.func.attr == 'system':
                    if isinstance(node.func.value, ast.Name) and node.func.value.id == 'os':
                        issues.append({
                            'type': 'unsafe_system_call',
                            'severity': 'HIGH',
                            'line': node.lineno,
                            'message': 'os.system() detected - security risk',
                            'remediation': 'Use subprocess.run() instead'
                        })
                
                # Check for subprocess with shell=True
                if isinstance(node.func, ast.Attribute) and node.func.attr == 'run':
                    for keyword in node.keywords:
                        if keyword.arg == 'shell' and isinstance(keyword.value, ast.Constant) and keyword.value.value == True:
                            issues.append({
                                'type': 'shell_injection_risk',
                                'severity': 'HIGH',
                                'line': node.lineno,
                                'message': 'subprocess.run with shell=True - shell injection risk',
                                'remediation': 'Avoid shell=True, use argument lists'
                            })
                
                # Check for eval/exec
                if isinstance(node.func, ast.Name) and node.func.id in ['eval', 'exec']:
                    issues.append({
                        'type': 'code_injection_risk',
                        'severity': 'HIGH',
                        'line': node.lineno,
                        'message': f'{node.func.id}() detected - code injection risk',
                        'remediation': 'Avoid dynamic code execution'
                    })
        
        # Check for tempfile.TemporaryDirectory usage (good practice)
        has_tempdir = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == 'TemporaryDirectory':
                has_tempdir = True
        
        if not has_tempdir:
            # This is just informational, not an issue
            issues.append({
                'type': 'tempfile_usage',
                'severity': 'INFO',
                'message': 'Consider using tempfile.TemporaryDirectory for safe temp file handling',
                'remediation': 'Use with tempfile.TemporaryDirectory() as temp_dir:'
            })
        
        return issues
    
    @staticmethod
    def verify_structured_output(tree: ast.AST) -> Dict:
        """Verify .with_structured_output() or .bind_tools() usage"""
        result = {
            'has_structured_output': False,
            'has_bind_tools': False,
            'locations': [],
            'pydantic_models': []
        }
        
        # First find Pydantic models
        pydantic_models = ASTAnalyzer.find_class_definitions(tree, 'BaseModel')
        result['pydantic_models'] = [m['class_name'] for m in pydantic_models]
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == 'with_structured_output':
                        result['has_structured_output'] = True
                        result['locations'].append({
                            'type': 'structured_output',
                            'line': node.lineno,
                            'schema': ast.unparse(node.args[0]) if node.args and hasattr(ast, 'unparse') else 'unknown'
                        })
                    elif node.func.attr == 'bind_tools':
                        result['has_bind_tools'] = True
                        result['locations'].append({
                            'type': 'bind_tools',
                            'line': node.lineno,
                            'tools': [ast.unparse(arg) for arg in node.args] if hasattr(ast, 'unparse') else []
                        })
        
        return result