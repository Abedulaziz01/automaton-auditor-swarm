from typing import List, Dict, Any, Optional
import re
from .synthesis_models import SecurityFinding, SecurityRiskLevel, RemediationAction

class SecurityOverride:
    """
    Applies security rules:
    - Shell injection detection
    - Caps scores at 3 if security issues found
    """
    
    def __init__(self):
        self.dangerous_patterns = [
            (r'os\.system\(.*\)', 'Direct system command execution', SecurityRiskLevel.CRITICAL),
            (r'subprocess\.call\(.*shell=True.*\)', 'Shell=True in subprocess', SecurityRiskLevel.HIGH),
            (r'eval\(.*\)', 'Eval execution', SecurityRiskLevel.CRITICAL),
            (r'exec\(.*\)', 'Exec execution', SecurityRiskLevel.CRITICAL),
            (r'__import__\(.*\)', 'Dynamic import', SecurityRiskLevel.MEDIUM),
            (r'pickle\.loads\(.*\)', 'Unsafe deserialization', SecurityRiskLevel.HIGH),
            (r'input\(.*\)', 'User input without validation', SecurityRiskLevel.MEDIUM),
            (r'%[^%]*\(.*\)', 'String formatting with % (SQL injection risk)', SecurityRiskLevel.MEDIUM),
            (r'\+\s*".*"\s*\+\s*".*"', 'String concatenation (SQL injection risk)', SecurityRiskLevel.LOW),
        ]
        
    def analyze_security(self, evidence: List[Any]) -> Dict[str, Any]:
        """
        Analyze all evidence for security issues
        Returns findings and whether to apply cap
        """
        print("\n🔒 SECURITY OVERRIDE ANALYSIS")
        print("="*60)
        
        findings = []
        highest_risk = SecurityRiskLevel.NONE
        shell_injection_detected = False
        
        # Look through all evidence
        for ev in evidence:
            if ev.source == "repo" and isinstance(ev.content, str):
                # Check for dangerous patterns
                for pattern, description, risk in self.dangerous_patterns:
                    if re.search(pattern, ev.content, re.IGNORECASE):
                        finding = SecurityFinding(
                            finding=f"{description} detected",
                            risk_level=risk,
                            evidence_id=ev.id,
                            file_path=self._extract_file_path(ev.content, pattern)
                        )
                        findings.append(finding)
                        
                        # Update highest risk
                        if self._risk_level_value(risk) > self._risk_level_value(highest_risk):
                            highest_risk = risk
                        
                        # Check specifically for shell injection
                        if "shell" in description.lower() or "system" in description.lower():
                            shell_injection_detected = True
        
        # Determine if we need to apply cap
        apply_cap = shell_injection_detected or highest_risk in [
            SecurityRiskLevel.HIGH, 
            SecurityRiskLevel.CRITICAL
        ]
        
        # Generate remediation actions
        remediations = self._generate_remediations(findings)
        
        result = {
            "findings": findings,
            "highest_risk": highest_risk.value,
            "shell_injection_detected": shell_injection_detected,
            "apply_cap": apply_cap,
            "cap_score": 3 if apply_cap else None,  # Cap at 3 if security issues
            "remediations": remediations
        }
        
        # Print summary
        print(f"\nFindings: {len(findings)} security issues")
        print(f"Highest Risk: {highest_risk.value}")
        print(f"Shell Injection: {'⚠️ YES' if shell_injection_detected else '✅ NO'}")
        print(f"Apply Score Cap: {'⚠️ YES (max score 3)' if apply_cap else '✅ NO'}")
        
        if findings:
            print("\nTop Security Findings:")
            for f in findings[:3]:
                print(f"  - {f.finding} ({f.risk_level.value})")
        
        return result
    
    def _risk_level_value(self, risk: SecurityRiskLevel) -> int:
        """Convert risk level to numeric for comparison"""
        values = {
            SecurityRiskLevel.NONE: 0,
            SecurityRiskLevel.LOW: 1,
            SecurityRiskLevel.MEDIUM: 2,
            SecurityRiskLevel.HIGH: 3,
            SecurityRiskLevel.CRITICAL: 4
        }
        return values.get(risk, 0)
    
    def _extract_file_path(self, content: str, pattern: str) -> Optional[str]:
        """Try to extract file path from context"""
        # Simple heuristic - look for file paths near the pattern
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if re.search(pattern, line, re.IGNORECASE):
                # Look for file path comments
                for j in range(max(0, i-3), min(len(lines), i+3)):
                    if '#' in lines[j] and ('.py' in lines[j] or '/' in lines[j]):
                        return lines[j].split('#')[-1].strip()
        return None
    
    def _generate_remediations(self, findings: List[SecurityFinding]) -> List[RemediationAction]:
        """Generate remediation actions for security findings"""
        remediations = []
        
        for finding in findings:
            if "system" in finding.finding.lower() or "shell" in finding.finding.lower():
                remediations.append(RemediationAction(
                    priority="HIGH",
                    action="Replace os.system() with subprocess.run() with shell=False",
                    file_path=finding.file_path,
                    code_example="subprocess.run(['command', 'arg1'], check=True)",
                    reasoning="Prevents shell injection attacks"
                ))
            elif "eval" in finding.finding.lower() or "exec" in finding.finding.lower():
                remediations.append(RemediationAction(
                    priority="HIGH",
                    action="Remove eval()/exec() - use safer alternatives like ast.literal_eval()",
                    file_path=finding.file_path,
                    code_example="import ast; ast.literal_eval(string)",
                    reasoning="Code execution from strings is extremely dangerous"
                ))
            elif "pickle" in finding.finding.lower():
                remediations.append(RemediationAction(
                    priority="MEDIUM",
                    action="Use JSON or safer serialization instead of pickle",
                    file_path=finding.file_path,
                    code_example="import json; json.dumps(data)",
                    reasoning="Pickle can execute arbitrary code during deserialization"
                ))
                
        return remediations
    
    def apply_override(self, scores: List[Dict], security_result: Dict) -> List[Dict]:
        """Apply security override to scores"""
        if not security_result['apply_cap']:
            return scores
        
        print("\n🔒 APPLYING SECURITY OVERRIDE - Capping scores at 3")
        
        capped_scores = []
        for score_dict in scores:
            original = score_dict['score']
            if original > 3:
                score_dict['score'] = 3
                score_dict['security_override_applied'] = True
                score_dict['reasoning'] += f" [SECURITY OVERRIDE: Score capped from {original} to 3 due to security findings]"
                print(f"   {score_dict['dimension']}: {original} → 3 (capped)")
            capped_scores.append(score_dict)
        
        return capped_scores