# src/tools/repo_tools.py - COMPLETE UPDATED FILE

import git
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

class RepoInvestigator:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.temp_dir = None
        self.repo = None
        self.working_dir = None
        
    def setup(self):
        """Clone or open repository with improved error handling"""
        print("\n📦 Setting up repository...")
        
        try:
            if self.repo_path.startswith(('http://', 'https://', 'git@')):
                # GitHub URL
                self.temp_dir = tempfile.mkdtemp()
                print(f"   Cloning to temp directory: {self.temp_dir}")
                
                # Clone with progress and timeout
                self.repo = git.Repo.clone_from(
                    self.repo_path, 
                    self.temp_dir,
                    progress=None,  # Could add custom progress reporter
                    depth=50  # Limit clone depth for speed
                )
                self.working_dir = self.temp_dir
                print("   ✅ Clone complete")
            else:
                # Local path
                if not os.path.exists(self.repo_path):
                    raise FileNotFoundError(f"Local path not found: {self.repo_path}")
                    
                self.working_dir = self.repo_path
                self.repo = git.Repo(self.repo_path)
                print(f"   ✅ Using local repo: {self.repo_path}")
                
        except git.GitCommandError as e:
            print(f"   ❌ Git error: {e}")
            raise
        except Exception as e:
            print(f"   ❌ Setup error: {e}")
            raise
    
    def cleanup(self):
        """Clean up temp directory if used with better Windows handling"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            print(f"   🧹 Cleaning up temp directory: {self.temp_dir}")
            
            # Try multiple cleanup strategies
            strategies = [
                self._cleanup_normal,
                self._cleanup_force_windows,
                self._cleanup_ignore_errors
            ]
            
            for strategy in strategies:
                try:
                    if strategy():
                        break
                except Exception as e:
                    continue
            
            # Final check
            if os.path.exists(self.temp_dir):
                print(f"   ⚠️  Temp directory still exists: {self.temp_dir}")
                print(f"   📁 You may need to manually delete it")
    
    def _cleanup_normal(self) -> bool:
        """Normal cleanup attempt"""
        try:
            shutil.rmtree(self.temp_dir)
            print(f"   ✅ Cleaned up temp directory")
            return True
        except Exception:
            return False
    
    def _cleanup_force_windows(self) -> bool:
        """Force cleanup for Windows permission issues"""
        try:
            # First, try to release any git locks
            git_dir = os.path.join(self.temp_dir, '.git')
            if os.path.exists(git_dir):
                # Remove write protection from all files
                for root, dirs, files in os.walk(self.temp_dir):
                    for file in files:
                        try:
                            file_path = os.path.join(root, file)
                            os.chmod(file_path, 0o777)
                        except:
                            pass
                    
                    for dir in dirs:
                        try:
                            dir_path = os.path.join(root, dir)
                            os.chmod(dir_path, 0o777)
                        except:
                            pass
                
                # Small delay to allow OS to release file handles
                time.sleep(0.5)
            
            # Try removal again
            shutil.rmtree(self.temp_dir)
            print(f"   ✅ Force cleanup completed")
            return True
        except Exception:
            return False
    
    def _cleanup_ignore_errors(self) -> bool:
        """Last resort: ignore errors during cleanup"""
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            if not os.path.exists(self.temp_dir):
                print(f"   ✅ Cleanup completed (with ignored errors)")
                return True
        except Exception:
            pass
        return False
    
    def analyze_git_history(self) -> Dict[str, Any]:
        """
        Step 1.1: Git Forensics
        Success: Extract commit history, detect monolithic commits, check progression
        """
        print("\n" + "="*60)
        print("🔍 STEP 1.1: GIT FORENSICS")
        print("="*60)
        
        try:
            # Determine default branch (main/master)
            try:
                default_branch = self.repo.active_branch.name
            except:
                # Try common branch names
                for branch in ['main', 'master', 'develop']:
                    try:
                        default_branch = branch
                        list(self.repo.iter_commits(branch, max_count=1))
                        break
                    except:
                        continue
                else:
                    default_branch = 'HEAD'
            
            # Get commit history
            commits = []
            commit_count = 0
            max_commits = 50  # Limit to prevent overwhelming
            
            for commit in self.repo.iter_commits(default_branch, max_count=max_commits):
                try:
                    # Safely get commit stats
                    stats = {}
                    if hasattr(commit, 'stats') and commit.stats:
                        stats = {
                            'files_changed': len(commit.stats.files) if commit.stats.files else 0,
                            'insertions': commit.stats.total.get('insertions', 0) if commit.stats.total else 0,
                            'deletions': commit.stats.total.get('deletions', 0) if commit.stats.total else 0
                        }
                    
                    # Safely get commit info
                    commit_data = {
                        'hash': commit.hexsha[:8] if commit.hexsha else 'unknown',
                        'message': commit.message.strip() if commit.message else '',
                        'timestamp': datetime.fromtimestamp(commit.committed_date).isoformat() if hasattr(commit, 'committed_date') else '',
                        'author': str(commit.author) if commit.author else 'unknown',
                        'stats': stats
                    }
                    
                    commits.append(commit_data)
                    commit_count += 1
                    
                except Exception as e:
                    print(f"   ⚠️  Error processing commit {commit.hexsha[:8] if commit.hexsha else 'unknown'}: {e}")
                    continue
            
            # Reverse to get chronological order (oldest first)
            commits.reverse()
            
            # Analyze first commit for monolithic detection
            monolithic_detected = False
            total_changes_first = 0
            if commits and commits[0].get('stats'):
                first_commit = commits[0]
                total_changes_first = (first_commit['stats'].get('insertions', 0) + 
                                     first_commit['stats'].get('deletions', 0))
                monolithic_detected = total_changes_first > 500  # Arbitrary threshold
            
            # Check for 3+ commits progression
            has_progression = len(commits) >= 3
            
            # Format git log style output
            git_log = []
            for i, commit in enumerate(commits, 1):
                message_preview = commit['message'][:50] + ('...' if len(commit['message']) > 50 else '')
                timestamp_preview = commit['timestamp'][:10] if commit['timestamp'] else 'no-date'
                git_log.append(f"{i:2d}. {commit['hash']} - {message_preview} ({timestamp_preview})")
            
            result = {
                'total_commits_analyzed': len(commits),
                'has_three_commits_progression': has_progression,
                'monolithic_init_detected': monolithic_detected,
                'first_commit_changes': total_changes_first if monolithic_detected else None,
                'default_branch': default_branch,
                'commits': commits,
                'git_log': git_log
            }
            
            # Display results
            print("\n📊 GIT HISTORY RESULTS:")
            print(f"   Branch analyzed: {default_branch}")
            print(f"   Total commits: {len(commits)}")
            print(f"   Has 3+ commits progression: {has_progression}")
            print(f"   Monolithic init detected: {monolithic_detected}")
            
            if monolithic_detected:
                print(f"   ⚠️  First commit had {total_changes_first}+ line changes")
            
            print("\n📜 Git Log (chronological):")
            for line in git_log:
                print(f"   {line}")
            
            return result
            
        except git.GitCommandError as e:
            error_msg = f"Git command error: {e}"
            print(f"   ❌ {error_msg}")
            return {'error': error_msg, 'stage': 'git_forensics'}
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            print(f"   ❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return {'error': error_msg, 'stage': 'git_forensics'}
    
    def analyze_ast_structure(self) -> Dict[str, Any]:
        """
        Step 1.2: AST Parsing (Placeholder for now)
        Will parse Python files and analyze structure
        """
        print("\n" + "="*60)
        print("🔍 STEP 1.2: AST PARSING")
        print("="*60)
        
        # TODO: Implement AST parsing
        # This is a placeholder for the next step
        
        result = {
            'status': 'not_implemented',
            'message': 'AST parsing coming soon!',
            'files_found': [],
            'stats': {}
        }
        
        # Just count Python files for now
        if self.working_dir:
            python_files = list(Path(self.working_dir).rglob("*.py"))
            result['files_found'] = [str(f.relative_to(self.working_dir)) for f in python_files[:10]]
            result['stats']['total_python_files'] = len(python_files)
            
            print(f"\n📊 AST PARSING PREVIEW:")
            print(f"   Found {len(python_files)} Python files")
            if python_files:
                print("\n   Sample files:")
                for f in python_files[:5]:
                    print(f"   - {f.relative_to(self.working_dir)}")
        
        return result
    
    def analyze_dependencies(self) -> Dict[str, Any]:
        """
        Step 1.3: Dependency Analysis (Placeholder)
        Will analyze requirements, imports, etc.
        """
        print("\n" + "="*60)
        print("🔍 STEP 1.3: DEPENDENCY ANALYSIS")
        print("="*60)
        
        # TODO: Implement dependency analysis
        
        result = {
            'status': 'not_implemented',
            'message': 'Dependency analysis coming soon!',
            'dependencies': {}
        }
        
        # Look for requirement files
        if self.working_dir:
            req_files = list(Path(self.working_dir).glob("requirements*.txt")) + \
                       list(Path(self.working_dir).glob("pyproject.toml")) + \
                       list(Path(self.working_dir).glob("setup.py"))
            
            result['dependency_files'] = [str(f.relative_to(self.working_dir)) for f in req_files]
            
            print(f"\n📊 DEPENDENCY ANALYSIS PREVIEW:")
            print(f"   Found {len(req_files)} dependency files")
            for f in req_files:
                print(f"   - {f.relative_to(self.working_dir)}")
        
        return result
    
    def full_analysis(self) -> Dict[str, Any]:
        """
        Run all analysis steps
        """
        print("\n" + "🚀"*20)
        print("STARTING FULL REPOSITORY ANALYSIS")
        print("🚀"*20)
        
        results = {}
        
        try:
            self.setup()
            
            # Step 1.1: Git Forensics
            results['git_forensics'] = self.analyze_git_history()
            
            # Step 1.2: AST Parsing
            results['ast_analysis'] = self.analyze_ast_structure()
            
            # Step 1.3: Dependency Analysis
            results['dependency_analysis'] = self.analyze_dependencies()
            
            print("\n" + "✅"*20)
            print("FULL ANALYSIS COMPLETE")
            print("✅"*20)
            
        except Exception as e:
            print(f"\n❌ Analysis failed: {e}")
            results['error'] = str(e)
            
        finally:
            self.cleanup()
        
        return results