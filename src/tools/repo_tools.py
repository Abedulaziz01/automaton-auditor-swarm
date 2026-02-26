"""
Git repository analysis tools
Production-grade git forensics
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

class GitAnalyzer:
    """Production-grade git analysis tools"""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self._check_git_repo()
    
    def _check_git_repo(self) -> bool:
        """Check if path is a git repository"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def get_commit_history(self, max_count: Optional[int] = None) -> List[Dict]:
        """Get structured commit history with full details"""
        if not self._check_git_repo():
            return []
        
        # Format: hash|author_name|author_email|date|subject|body
        format_str = '%H|%an|%ae|%ad|%s|%b'
        cmd = ['git', 'log', f'--pretty=format:{format_str}', '--date=iso']
        
        if max_count:
            cmd.extend(['-n', str(max_count)])
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return []
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|', 5)
                    if len(parts) >= 5:
                        commits.append({
                            'hash': parts[0],
                            'author_name': parts[1],
                            'author_email': parts[2],
                            'date': parts[3],
                            'subject': parts[4],
                            'body': parts[5] if len(parts) > 5 else '',
                            'timestamp': datetime.fromisoformat(parts[3].replace(' ', 'T'))
                        })
            return commits
            
        except subprocess.TimeoutExpired:
            print("Git command timed out")
            return []
        except Exception as e:
            print(f"Git error: {e}")
            return []
    
    def get_commit_files(self, commit_hash: str) -> List[str]:
        """Get files changed in a commit"""
        try:
            result = subprocess.run(
                ['git', 'show', '--name-only', '--pretty=format:', commit_hash],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return []
            
            files = [f for f in result.stdout.strip().split('\n') if f]
            return files
            
        except Exception:
            return []
    
    def detect_monolithic_init(self) -> Dict:
        """Detect if initial commit was monolithic"""
        commits = self.get_commit_history(max_count=10)
        
        if not commits:
            return {'is_monolithic': False, 'reason': 'No commits found'}
        
        # Get first commit (last in reverse order)
        first_commit = commits[-1]
        files = self.get_commit_files(first_commit['hash'])
        
        # Analysis metrics
        file_count = len(files)
        
        # Heuristics for monolithic detection
        is_monolithic = False
        reasons = []
        
        if file_count > 20:
            is_monolithic = True
            reasons.append(f"Too many files ({file_count} > 20)")
        
        # Check commit message
        subject = first_commit['subject'].lower()
        monolithic_indicators = ['init', 'initial', 'first', 'setup', 'bootstrap']
        if any(ind in subject for ind in monolithic_indicators):
            if file_count > 10:
                is_monolithic = True
                reasons.append(f"Initial commit with {file_count} files")
        
        # Check for multiple core components
        core_dirs = set()
        for f in files:
            parts = f.split('/')
            if parts:
                core_dirs.add(parts[0])
        
        if len(core_dirs) > 3 and file_count > 15:
            is_monolithic = True
            reasons.append(f"Spans multiple directories: {', '.join(list(core_dirs)[:3])}")
        
        return {
            'is_monolithic': is_monolithic,
            'file_count': file_count,
            'commit_message': first_commit['subject'],
            'files_sample': files[:5],  # First 5 files as sample
            'reasons': reasons,
            'commit_hash': first_commit['hash'],
            'commit_date': first_commit['date']
        }
    
    def get_commit_progression(self) -> Dict:
        """Analyze commit progression over time"""
        commits = self.get_commit_history(max_count=100)
        
        if len(commits) < 3:
            return {'has_progression': False, 'reason': 'Insufficient commits'}
        
        # Calculate time between commits
        timestamps = [c['timestamp'] for c in commits]
        time_diffs = []
        for i in range(len(timestamps)-1):
            diff = (timestamps[i] - timestamps[i+1]).total_seconds() / 3600  # hours
            time_diffs.append(diff)
        
        avg_time_between = sum(time_diffs) / len(time_diffs) if time_diffs else 0
        
        # Check message quality
        messages = [c['subject'] for c in commits]
        avg_message_length = sum(len(m.split()) for m in messages) / len(messages)
        
        return {
            'has_progression': True,
            'total_commits': len(commits),
            'avg_time_between_commits_hours': round(avg_time_between, 2),
            'avg_message_length_words': round(avg_message_length, 1),
            'first_commit_date': commits[-1]['date'],
            'last_commit_date': commits[0]['date']
        }