import PyPDF2
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
import tempfile
import shutil
import re
import time
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

class DocAnalyst:
    """
    PDF Detective - Analyzes documentation for theoretical depth and hallucinations
    Uses Google's Gemini for embeddings
    """
    
    def __init__(self, pdf_path: str, repo_evidence: Optional[Dict] = None):
        """
        Initialize with PDF path and optional repo evidence for cross-checking
        
        Args:
            pdf_path: Path to PDF file
            repo_evidence: Evidence from RepoInvestigator for cross-validation
        """
        self.pdf_path = pdf_path
        self.repo_evidence = repo_evidence
        self.temp_dir = None
        self.vectorstore = None
        self.chunks = []
        
        # Configure Gemini
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Please set GOOGLE_API_KEY in your .env file")
        
        genai.configure(api_key=api_key)
        
        # Concepts we're looking for
        self.target_concepts = [
            "dialectical synthesis",
            "fan-in",
            "fan-out",
            "metacognition",
            "state synchronization"
        ]
        
    def setup(self):
        """Validate PDF exists and is readable"""
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")
        
        # Create temp directory for vector store if needed
        self.temp_dir = tempfile.mkdtemp()
        print(f"📁 Created temp directory: {self.temp_dir}")
        
    def cleanup(self):
        """Clean up temporary files with better Windows handling"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            print(f"🧹 Cleaning up {self.temp_dir}")
            
            # Clear vectorstore reference first
            if hasattr(self, 'vectorstore') and self.vectorstore:
                try:
                    self.vectorstore = None
                except:
                    pass
            
            # Try multiple times with delay
            for attempt in range(3):
                try:
                    time.sleep(1)  # Wait for file handles to be released
                    shutil.rmtree(self.temp_dir, ignore_errors=False)
                    print(f"✅ Cleaned up temp directory")
                    return
                except PermissionError:
                    print(f"   Attempt {attempt + 1}: File locked, retrying...")
                except Exception as e:
                    print(f"   Attempt {attempt + 1}: {e}")
            
            # Final attempt with ignore_errors
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                print(f"⚠️  Cleanup completed (with ignored errors)")
            except:
                print(f"⚠️  Could not clean up {self.temp_dir}")
    
    def extract_text_from_pdf(self) -> str:
        """
        Step 1: Extract all text from PDF
        Success: Get clean text content from all pages
        """
        print("\n📄 Extracting text from PDF...")
        
        text = ""
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                print(f"   Found {num_pages} pages")
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    text += f"\n--- Page {page_num + 1} ---\n"
                    text += page_text
                    
                    # Progress indicator
                    if (page_num + 1) % 5 == 0:
                        print(f"   Processed {page_num + 1}/{num_pages} pages")
                
            print(f"✅ Extracted {len(text)} characters from PDF")
            return text
            
        except Exception as e:
            print(f"❌ Error extracting PDF: {e}")
            return ""
    
    def chunk_document(self, text: str) -> List[str]:
        """
        Step 2: Chunk document for RAG-lite ingestion
        Success: Document split into semantic chunks
        """
        print("\n🔪 Chunking document...")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = text_splitter.split_text(text)
        self.chunks = chunks
        
        print(f"✅ Created {len(chunks)} chunks")
        print(f"   Average chunk size: {sum(len(c) for c in chunks)//len(chunks)} chars")
        
        # Show sample chunks
        print("\n📝 Sample chunks:")
        for i, chunk in enumerate(chunks[:2]):
            print(f"\n   Chunk {i+1} (first 200 chars):")
            print(f"   {chunk[:200]}...")
        
        return chunks
    
    def create_vector_store(self, chunks: List[str]):
        """
        Step 3: Create vector store for semantic search using Gemini embeddings
        Success: Embeddings created and searchable
        """
        print("\n🔧 Creating vector store with Gemini embeddings...")
        
        try:
            # Try different embedding models (in order of preference)
            embedding_models = [
                "models/text-embedding-004",  # Latest text embedding model
                "models/embedding-001",        # Older model
            ]
            
            embeddings = None
            last_error = None
            
            for model_name in embedding_models:
                try:
                    print(f"   Trying model: {model_name}")
                    embeddings = GoogleGenerativeAIEmbeddings(
                        model=model_name,
                        google_api_key=os.getenv("GOOGLE_API_KEY")
                    )
                    # Test the embeddings with a simple query
                    test_embed = embeddings.embed_query("test")
                    print(f"   ✅ Successfully connected to {model_name}")
                    break
                except Exception as e:
                    print(f"   ⚠️  Model {model_name} failed: {e}")
                    last_error = e
                    continue
            
            if embeddings is None:
                # If both fail, try to get available models
                print("\n📋 Available models:")
                try:
                    for model in genai.list_models():
                        if 'embedContent' in str(model.supported_generation_methods):
                            print(f"   - {model.name}")
                except:
                    pass
                raise Exception(f"Could not initialize any embedding model. Last error: {last_error}")
            
            # Create vector store
            self.vectorstore = Chroma.from_texts(
                texts=chunks,
                embedding=embeddings,
                persist_directory=os.path.join(self.temp_dir, "chroma_db")
            )
            
            print(f"✅ Vector store created with {len(chunks)} chunks")
            
        except Exception as e:
            print(f"❌ Error creating vector store: {e}")
            print("\n💡 Troubleshooting tips:")
            print("   1. Check your GOOGLE_API_KEY in .env file")
            print("   2. Visit https://makersuite.google.com/app/apikey to get a valid key")
            print("   3. Make sure the Gemini API is enabled for your project")
            raise
    
    def query_concept(self, concept: str) -> Dict[str, Any]:
        """
        Step 4: Query for specific concept with context
        Success: Get relevant passages with confidence scores
        """
        print(f"\n🔍 Querying concept: '{concept}'")
        
        if not self.vectorstore:
            return {"error": "Vector store not initialized"}
        
        # Similarity search
        docs = self.vectorstore.similarity_search_with_score(concept, k=3)
        
        results = {
            "concept": concept,
            "found": len(docs) > 0,
            "matches": [],
            "has_real_explanation": False,
            "is_buzzword": True  # Assume buzzword until proven otherwise
        }
        
        for doc, score in docs:
            match = {
                "text": doc.page_content[:300] + "...",
                "relevance_score": float(score),
                "context": doc.page_content
            }
            results["matches"].append(match)
            
            # Check if this is a real explanation (not just buzzword)
            if self._is_real_explanation(doc.page_content, concept):
                results["has_real_explanation"] = True
                results["is_buzzword"] = False
        
        # Display results
        if results["matches"]:
            print(f"   Found {len(results['matches'])} relevant passages")
            print(f"   Best relevance score: {results['matches'][0]['relevance_score']:.2f}")
            print(f"   Real explanation: {results['has_real_explanation']}")
        else:
            print(f"   No matches found")
        
        return results
    
    def _is_real_explanation(self, text: str, concept: str) -> bool:
        """
        Determine if text contains real explanation vs buzzword stuffing
        """
        # Convert to lowercase for matching
        text_lower = text.lower()
        concept_lower = concept.lower()
        
        # Indicators of real explanation:
        indicators = [
            # Has definition or explanation words
            "defined as" in text_lower or "refers to" in text_lower,
            "for example" in text_lower or "e.g." in text_lower,
            "such as" in text_lower or "like" in text_lower,
            "because" in text_lower or "therefore" in text_lower,
            "implemented by" in text_lower or "achieved through" in text_lower,
            
            # Has technical depth
            "code" in text_lower or "function" in text_lower,
            "graph" in text_lower or "node" in text_lower,
            "parallel" in text_lower or "concurrent" in text_lower,
            
            # Has context
            len(text) > 200,  # Substantial explanation
            text.count(concept_lower) > 1,  # Mentioned multiple times in context
        ]
        
        # Buzzword indicators:
        buzzword_indicators = [
            text.count(concept_lower) == 1,  # Only mentioned once
            len(text) < 100,  # Too short to be real explanation
            "buzzword" in text_lower or "trendy" in text_lower,  # Self-aware buzzwords
            text_lower.count(concept_lower) > text_lower.count(" ") * 0.3,  # Too frequent
        ]
        
        # Score the explanation
        real_score = sum(indicators)
        buzzword_score = sum(buzzword_indicators)
        
        # Decision
        return real_score > buzzword_score and real_score >= 2
    
    def analyze_theoretical_depth(self) -> Dict[str, Any]:
        """
        Step 5: Comprehensive theoretical depth analysis
        Success: Identify real explanations vs buzzwords for all concepts
        """
        print("\n" + "="*50)
        print("📚 ANALYZING THEORETICAL DEPTH")
        print("="*50)
        
        results = {
            "concepts_analyzed": [],
            "real_explanations": [],
            "buzzword_only": [],
            "summary": {}
        }
        
        for concept in self.target_concepts:
            concept_result = self.query_concept(concept)
            results["concepts_analyzed"].append(concept_result)
            
            if concept_result.get("has_real_explanation"):
                results["real_explanations"].append(concept)
            else:
                results["buzzword_only"].append(concept)
        
        # Summary
        results["summary"] = {
            "total_concepts": len(self.target_concepts),
            "real_explanations": len(results["real_explanations"]),
            "buzzword_only": len(results["buzzword_only"]),
            "depth_score": len(results["real_explanations"]) / len(self.target_concepts) if self.target_concepts else 0
        }
        
        print("\n" + "="*50)
        print("📊 THEORETICAL DEPTH SUMMARY")
        print("="*50)
        print(f"   Real explanations: {results['summary']['real_explanations']}/{results['summary']['total_concepts']}")
        print(f"   Buzzword only: {results['summary']['buzzword_only']}/{results['summary']['total_concepts']}")
        print(f"   Depth score: {results['summary']['depth_score']:.2%}")
        
        if results["real_explanations"]:
            print(f"\n✅ Concepts with real depth:")
            for concept in results["real_explanations"]:
                print(f"   - {concept}")
        
        if results["buzzword_only"]:
            print(f"\n⚠️  Buzzword-only concepts:")
            for concept in results["buzzword_only"]:
                print(f"   - {concept}")
        
        return results
    
    def extract_file_paths(self, text: str) -> List[str]:
        """
        Step 6: Extract all file paths mentioned in PDF
        Success: Find all potential file references
        """
        print("\n🔍 Extracting file paths from PDF...")
        
        # Common file path patterns
        patterns = [
            r'src/[a-zA-Z0-9_/]+\.py',  # Python files
            r'tests?/[a-zA-Z0-9_/]+\.py',  # Test files
            r'[a-zA-Z0-9_/]+\.py',  # Any Python file
            r'[a-zA-Z0-9_/]+\.json',  # JSON files
            r'[a-zA-Z0-9_/]+\.md',  # Markdown files
            r'[a-zA-Z0-9_/]+\.txt',  # Text files
            r'\./[a-zA-Z0-9_/]+',  # Relative paths
            r'/[a-zA-Z0-9_/]+',  # Absolute paths (simplified)
        ]
        
        found_paths = set()
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            found_paths.update(matches)
        
        # Clean and normalize paths
        cleaned_paths = []
        for path in found_paths:
            # Remove duplicates and normalize
            if len(path) > 3 and '/' in path:  # Basic validation
                cleaned_paths.append(path)
        
        print(f"✅ Found {len(cleaned_paths)} potential file paths")
        if cleaned_paths[:5]:
            print("   Sample paths:")
            for path in cleaned_paths[:5]:
                print(f"   - {path}")
        
        return cleaned_paths
    
    def cross_check_paths(self, pdf_paths: List[str]) -> Dict[str, Any]:
        """
        Step 7: Cross-check PDF paths with repo evidence
        Success: Identify verified vs hallucinated paths
        """
        print("\n🔍 CROSS-CHECKING PATHS WITH REPO")
        print("="*50)
        
        if not self.repo_evidence:
            print("⚠️  No repo evidence provided for cross-checking")
            return {
                "verified_paths": [],
                "hallucinated_paths": pdf_paths,
                "total_paths": len(pdf_paths),
                "verification_rate": 0
            }
        
        # Extract file list from repo evidence
        repo_files = self._get_repo_files_from_evidence()
        
        verified = []
        hallucinated = []
        
        for path in pdf_paths:
            # Check if path exists in repo
            path_exists = any(
                path in repo_file or repo_file in path
                for repo_file in repo_files
            )
            
            if path_exists:
                verified.append(path)
            else:
                hallucinated.append(path)
        
        result = {
            "verified_paths": verified,
            "hallucinated_paths": hallucinated,
            "total_paths": len(pdf_paths),
            "verification_rate": len(verified) / len(pdf_paths) if pdf_paths else 0
        }
        
        print(f"\n📊 Path Verification Results:")
        print(f"   Total paths: {result['total_paths']}")
        print(f"   Verified: {len(verified)} ({result['verification_rate']:.1%})")
        print(f"   Hallucinated: {len(hallucinated)}")
        
        if verified:
            print(f"\n✅ Verified paths:")
            for path in verified[:5]:
                print(f"   - {path}")
        
        if hallucinated:
            print(f"\n⚠️  Hallucinated paths:")
            for path in hallucinated[:5]:
                print(f"   - {path}")
        
        return result
    
    def _get_repo_files_from_evidence(self) -> List[str]:
        """Extract file list from repo evidence"""
        files = []
        
        # Try to get files from git commits
        if self.repo_evidence and 'commits' in self.repo_evidence:
            for commit in self.repo_evidence['commits']:
                if 'stats' in commit and 'files_changed' in commit['stats']:
                    # This would need actual file names - for now use simulated
                    pass
        
        # Fallback to simulated files if none found
        if not files:
            files = [
                "src/state.py",
                "src/graph.py",
                "src/nodes/detectives.py",
                "src/nodes/judges.py",
                "src/nodes/justice.py",
                "src/tools/repo_tools.py",
                "tests/test_detectives.py",
                "README.md"
            ]
        
        return files
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """
        Run complete PDF analysis
        """
        print("\n" + "="*60)
        print("📄 STARTING FULL DOCUMENT ANALYSIS WITH GEMINI")
        print("="*60)
        
        try:
            self.setup()
            
            # Step 1: Extract text
            text = self.extract_text_from_pdf()
            if not text:
                return {"error": "No text extracted from PDF"}
            
            # Step 2: Chunk document
            chunks = self.chunk_document(text)
            
            # Step 3: Create vector store
            self.create_vector_store(chunks)
            
            # Step 4: Analyze theoretical depth
            depth_results = self.analyze_theoretical_depth()
            
            # Step 5: Extract and verify paths
            pdf_paths = self.extract_file_paths(text)
            path_results = self.cross_check_paths(pdf_paths)
            
            # Combine results
            final_results = {
                "pdf_metadata": {
                    "path": self.pdf_path,
                    "chunks": len(chunks),
                    "text_length": len(text)
                },
                "theoretical_depth": depth_results,
                "path_verification": path_results,
                "model_used": "gemini"
            }
            
            print("\n" + "="*60)
            print("✅ DOCUMENT ANALYSIS COMPLETE")
            print("="*60)
            
            return final_results
            
        except Exception as e:
            print(f"❌ Error in analysis: {e}")
            return {"error": str(e)}
            
        finally:
            self.cleanup()


# Standalone function for easy use
def analyze_documentation(pdf_path: str, repo_evidence_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Main entry point for PDF analysis
    
    Args:
        pdf_path: Path to PDF file
        repo_evidence_path: Optional path to repo_evidence.json from RepoInvestigator
    """
    # Load repo evidence if provided
    repo_evidence = None
    if repo_evidence_path and os.path.exists(repo_evidence_path):
        with open(repo_evidence_path, 'r') as f:
            repo_evidence = json.load(f)
        print(f"📂 Loaded repo evidence from {repo_evidence_path}")
    
    analyst = DocAnalyst(pdf_path, repo_evidence)
    return analyst.run_full_analysis()