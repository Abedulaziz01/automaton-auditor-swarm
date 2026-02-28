import os
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import base64
import json

# PDF to image conversion
from pdf2image import convert_from_path

# Image processing
import cv2
import numpy as np
from PIL import Image

# LangChain for vision analysis
from langchain_openai import ChatOpenAI
from langchain.schema.messages import HumanMessage

class VisionInspector:
    """
    Vision Inspector - Analyzes diagrams in PDF documents
    Verifies architectural patterns match implementation
    """
    
    def __init__(self, pdf_path: str, repo_evidence: Optional[Dict] = None):
        """
        Initialize with PDF path and optional repo evidence
        
        Args:
            pdf_path: Path to PDF file
            repo_evidence: Evidence from RepoInvestigator for cross-checking
        """
        self.pdf_path = pdf_path
        self.repo_evidence = repo_evidence
        self.temp_dir = None
        self.images_dir = None
        self.extracted_images = []
        
        # Initialize vision model
        self.llm = ChatOpenAI(model="gpt-4-vision-preview", max_tokens=1024)
        
        # Diagram types we're looking for
        self.diagram_types = {
            "state_machine": ["stategraph", "state diagram", "state machine", "nodes", "edges"],
            "sequence": ["sequence diagram", "interaction", "message flow", "lifeline"],
            "flowchart": ["flowchart", "flow chart", "process", "decision", "parallel"]
        }
        
        # Required architecture patterns
        self.required_patterns = [
            "parallel_detectives",
            "evidence_aggregation",
            "parallel_judges",
            "chief_justice"
        ]
        
    def setup(self):
        """Create temporary directory for images"""
        self.temp_dir = tempfile.mkdtemp()
        self.images_dir = os.path.join(self.temp_dir, "images")
        os.makedirs(self.images_dir, exist_ok=True)
        print(f"📁 Created temp directory: {self.temp_dir}")
        
    def cleanup(self):
        """Remove temporary directory"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"🧹 Cleaned up {self.temp_dir}")
    
    def extract_images_from_pdf(self, dpi: int = 200) -> List[str]:
        """
        Step 1: Extract all images/diagrams from PDF
        Success: Convert PDF pages to images, identify pages with diagrams
        """
        print("\n🖼️ Extracting images from PDF...")
        
        try:
            # Convert PDF to images
            images = convert_from_path(self.pdf_path, dpi=dpi)
            print(f"   Converted {len(images)} pages to images")
            
            image_paths = []
            for i, image in enumerate(images):
                # Save each page as image
                image_path = os.path.join(self.images_dir, f"page_{i+1:03d}.png")
                image.save(image_path, "PNG")
                image_paths.append(image_path)
                
                # Quick diagram detection (simple heuristic)
                if self._is_likely_diagram(image):
                    print(f"   📐 Page {i+1} appears to contain a diagram")
                    self.extracted_images.append({
                        "page": i+1,
                        "path": image_path,
                        "likely_diagram": True
                    })
                else:
                    self.extracted_images.append({
                        "page": i+1,
                        "path": image_path,
                        "likely_diagram": False
                    })
            
            # Filter to likely diagrams
            diagram_pages = [img for img in self.extracted_images if img["likely_diagram"]]
            print(f"\n✅ Found {len(diagram_pages)} pages that likely contain diagrams")
            
            return image_paths
            
        except Exception as e:
            print(f"❌ Error extracting images: {e}")
            return []
    
    def _is_likely_diagram(self, image) -> bool:
        """
        Simple heuristic to detect if a page contains a diagram
        Looks for:
        - Low text density
        - Presence of lines/shapes
        - White background with black lines (typical for diagrams)
        """
        # Convert to numpy array
        img_array = np.array(image)
        
        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Calculate text density (white pixels ratio)
        white_ratio = np.sum(gray > 240) / gray.size
        
        # Detect edges (lines)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Diagrams typically have:
        # - Lots of white space (low text density)
        # - Clear lines (medium edge density)
        # - Not too many dark pixels (not a photo)
        
        is_diagram = (
            white_ratio > 0.7 and  # Mostly white background
            edge_density > 0.05 and edge_density < 0.3 and  # Some lines but not too many
            np.sum(gray < 50) / gray.size < 0.1  # Not too many dark areas
        )
        
        return is_diagram
    
    def classify_diagram(self, image_path: str) -> Dict[str, Any]:
        """
        Step 2: Classify diagram type using vision model
        Success: Identify if diagram is state machine, sequence, or flowchart
        """
        print(f"\n🔍 Classifying diagram: {os.path.basename(image_path)}")
        
        try:
            # Load and encode image
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            # Create vision prompt
            prompt = """
            Analyze this diagram and classify it into one of these categories:
            1. STATE MACHINE DIAGRAM - Shows nodes/states and edges/transitions. May show state graph structure.
            2. SEQUENCE DIAGRAM - Shows interactions between components over time, with lifelines and messages.
            3. FLOWCHART - Shows process flow with decisions, parallel branches, and merging points.
            4. OTHER - Not a technical diagram or doesn't fit above categories.
            
            Look for these specific patterns in LangGraph architecture:
            - Parallel detectives (multiple agents working in parallel)
            - Evidence aggregation (fan-in node collecting results)
            - Parallel judges (multiple judges working in parallel)
            - Chief Justice (final node that synthesizes)
            
            Return JSON with:
            {
                "diagram_type": "state_machine|sequence|flowchart|other",
                "confidence": 0.0-1.0,
                "has_parallel_detectives": true/false,
                "has_aggregation": true/false,
                "has_parallel_judges": true/false,
                "has_chief_justice": true/false,
                "explanation": "Brief explanation of what you see",
                "elements_found": ["list", "of", "key", "elements"]
            }
            """
            
            # Get vision model analysis
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
                ]
            )
            
            response = self.llm.invoke([message])
            
            # Parse response (assuming it's JSON)
            try:
                result = json.loads(response.content)
            except:
                # Fallback if not JSON
                result = {
                    "diagram_type": "other",
                    "confidence": 0.5,
                    "has_parallel_detectives": False,
                    "has_aggregation": False,
                    "has_parallel_judges": False,
                    "has_chief_justice": False,
                    "explanation": response.content[:200],
                    "elements_found": []
                }
            
            # Display results
            print(f"   Type: {result.get('diagram_type')} ({result.get('confidence', 0):.2%})")
            print(f"   Parallel detectives: {result.get('has_parallel_detectives', False)}")
            print(f"   Evidence aggregation: {result.get('has_aggregation', False)}")
            print(f"   Parallel judges: {result.get('has_parallel_judges', False)}")
            print(f"   Chief justice: {result.get('has_chief_justice', False)}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error classifying diagram: {e}")
            return {
                "diagram_type": "error",
                "confidence": 0,
                "error": str(e)
            }
    
    def detect_architecture_patterns(self, image_path: str) -> Dict[str, Any]:
        """
        Step 3: Use OpenCV to detect architectural patterns
        Success: Identify parallel splits, merges, node structures
        """
        print(f"\n🔧 Detecting architectural patterns in {os.path.basename(image_path)}")
        
        try:
            # Load image
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detect shapes
            _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Analyze contours to find potential nodes
            nodes = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 100:  # Filter small noise
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # Detect node shapes (rectangles, circles)
                    if 0.5 < aspect_ratio < 2.0 and area < 5000:
                        nodes.append({
                            "x": x, "y": y, "w": w, "h": h,
                            "area": area,
                            "aspect_ratio": aspect_ratio
                        })
            
            # Detect lines (edges)
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, minLineLength=50, maxLineGap=10)
            
            connections = []
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    connections.append({
                        "from": (x1, y1),
                        "to": (x2, y2),
                        "length": np.sqrt((x2-x1)**2 + (y2-y1)**2)
                    })
            
            # Analyze layout for parallel structures
            result = {
                "nodes_detected": len(nodes),
                "connections_detected": len(connections) if connections else 0,
                "layout_analysis": self._analyze_layout(nodes),
                "has_parallel_structure": False,
                "has_fan_in": False,
                "has_fan_out": False
            }
            
            # Determine if diagram shows parallel structure
            if len(nodes) >= 4:
                # Look for multiple nodes at same vertical level (parallel)
                y_positions = [n["y"] for n in nodes]
                y_levels = {}
                for y in y_positions:
                    level = round(y / 50)  # Group by approximate vertical position
                    y_levels[level] = y_levels.get(level, 0) + 1
                
                # If any level has multiple nodes, could be parallel
                if max(y_levels.values()) >= 2:
                    result["has_parallel_structure"] = True
                
                # Look for nodes with multiple outgoing connections (fan-out)
                if connections and len(connections) > len(nodes):
                    result["has_fan_out"] = True
                
                # Look for nodes with multiple incoming connections (fan-in)
                # Simplified heuristic
                if connections and len(connections) > len(nodes) * 1.5:
                    result["has_fan_in"] = True
            
            print(f"   Nodes detected: {result['nodes_detected']}")
            print(f"   Connections: {result['connections_detected']}")
            print(f"   Parallel structure: {result['has_parallel_structure']}")
            print(f"   Fan-out detected: {result['has_fan_out']}")
            print(f"   Fan-in detected: {result['has_fan_in']}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error detecting patterns: {e}")
            return {"error": str(e)}
    
    def _analyze_layout(self, nodes: List[Dict]) -> Dict[str, Any]:
        """Analyze node layout for architectural patterns"""
        if len(nodes) < 2:
            return {"pattern": "too_few_nodes"}
        
        # Calculate centers
        centers = [(n["x"] + n["w"]/2, n["y"] + n["h"]/2) for n in nodes]
        
        # Check if nodes are arranged in layers (typical for architecture diagrams)
        y_coords = [c[1] for c in centers]
        y_mean = np.mean(y_coords)
        y_std = np.std(y_coords)
        
        # If nodes are in distinct layers
        if y_std > 50:
            # Group by vertical position
            layers = {}
            for i, y in enumerate(y_coords):
                layer = round((y - y_mean) / 100)
                if layer not in layers:
                    layers[layer] = []
                layers[layer].append(i)
            
            return {
                "pattern": "layered",
                "layers": len(layers),
                "nodes_per_layer": [len(v) for v in layers.values()]
            }
        else:
            return {
                "pattern": "flat",
                "nodes": len(nodes)
            }
    
    def verify_architecture(self, vision_results: List[Dict]) -> Dict[str, Any]:
        """
        Step 4: Verify if diagrams match required architecture
        Success: Confirm parallel detectives → aggregation → parallel judges → chief justice
        """
        print("\n🔍 VERIFYING ARCHITECTURE AGAINST REQUIREMENTS")
        print("="*60)
        
        # Initialize verification results
        verification = {
            "parallel_detectives_verified": False,
            "evidence_aggregation_verified": False,
            "parallel_judges_verified": False,
            "chief_justice_verified": False,
            "confidence": 0.0,
            "supporting_diagrams": [],
            "missing_patterns": []
        }
        
        # Analyze all diagram results
        for i, result in enumerate(vision_results):
            diagram_page = self.extracted_images[i]["page"] if i < len(self.extracted_images) else i+1
            
            # Check each required pattern
            if result.get("has_parallel_detectives", False):
                verification["parallel_detectives_verified"] = True
                verification["supporting_diagrams"].append({
                    "page": diagram_page,
                    "pattern": "parallel_detectives",
                    "confidence": result.get("confidence", 0.5)
                })
            
            if result.get("has_aggregation", False):
                verification["evidence_aggregation_verified"] = True
                verification["supporting_diagrams"].append({
                    "page": diagram_page,
                    "pattern": "evidence_aggregation",
                    "confidence": result.get("confidence", 0.5)
                })
            
            if result.get("has_parallel_judges", False):
                verification["parallel_judges_verified"] = True
                verification["supporting_diagrams"].append({
                    "page": diagram_page,
                    "pattern": "parallel_judges",
                    "confidence": result.get("confidence", 0.5)
                })
            
            if result.get("has_chief_justice", False):
                verification["chief_justice_verified"] = True
                verification["supporting_diagrams"].append({
                    "page": diagram_page,
                    "pattern": "chief_justice",
                    "confidence": result.get("confidence", 0.5)
                })
        
        # Identify missing patterns
        required_patterns = [
            ("parallel_detectives", "Parallel Detectives"),
            ("evidence_aggregation", "Evidence Aggregation"),
            ("parallel_judges", "Parallel Judges"),
            ("chief_justice", "Chief Justice")
        ]
        
        for pattern_key, pattern_name in required_patterns:
            if not verification[f"{pattern_key}_verified"]:
                verification["missing_patterns"].append(pattern_name)
        
        # Calculate overall confidence
        verified_count = sum([
            verification["parallel_detectives_verified"],
            verification["evidence_aggregation_verified"],
            verification["parallel_judges_verified"],
            verification["chief_justice_verified"]
        ])
        
        verification["confidence"] = verified_count / 4
        verification["architecture_score"] = verified_count * 25  # 25 points each
        
        # Display results
        print(f"\n📊 Architecture Verification Results:")
        print(f"   Parallel Detectives: {'✅' if verification['parallel_detectives_verified'] else '❌'}")
        print(f"   Evidence Aggregation: {'✅' if verification['evidence_aggregation_verified'] else '❌'}")
        print(f"   Parallel Judges: {'✅' if verification['parallel_judges_verified'] else '❌'}")
        print(f"   Chief Justice: {'✅' if verification['chief_justice_verified'] else '❌'}")
        print(f"\n   Architecture Score: {verification['architecture_score']}/100")
        print(f"   Confidence: {verification['confidence']:.2%}")
        
        if verification["missing_patterns"]:
            print(f"\n⚠️  Missing patterns:")
            for pattern in verification["missing_patterns"]:
                print(f"   - {pattern}")
        
        return verification
    
    def cross_reference_with_repo(self, vision_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 5: Cross-reference diagram findings with repo evidence
        Success: Verify diagrams match actual implementation
        """
        print("\n🔍 CROSS-REFERENCING WITH REPO IMPLEMENTATION")
        print("="*60)
        
        if not self.repo_evidence:
            print("⚠️  No repo evidence provided for cross-referencing")
            return vision_results
        
        # Extract graph structure from repo evidence
        graph_structure = self.repo_evidence.get("graph_structure", {})
        
        # Compare diagram findings with actual implementation
        comparison = {
            "diagram_vs_implementation": {},
            "consistency_score": 0,
            "discrepancies": []
        }
        
        # Check parallel detectives
        diagram_has = vision_results.get("parallel_detectives_verified", False)
        repo_has = graph_structure.get("has_fan_out", False)
        
        comparison["diagram_vs_implementation"]["parallel_detectives"] = {
            "diagram": diagram_has,
            "implementation": repo_has,
            "consistent": diagram_has == repo_has
        }
        if diagram_has != repo_has:
            comparison["discrepancies"].append({
                "pattern": "parallel_detectives",
                "diagram": diagram_has,
                "implementation": repo_has,
                "issue": "Diagram shows parallel detectives but implementation doesn't" if diagram_has and not repo_has else "Implementation has parallel detectives but diagram doesn't show it"
            })
        
        # Check aggregation/fan-in
        diagram_has = vision_results.get("evidence_aggregation_verified", False)
        repo_has = graph_structure.get("has_fan_in", False)
        
        comparison["diagram_vs_implementation"]["evidence_aggregation"] = {
            "diagram": diagram_has,
            "implementation": repo_has,
            "consistent": diagram_has == repo_has
        }
        if diagram_has != repo_has:
            comparison["discrepancies"].append({
                "pattern": "evidence_aggregation",
                "diagram": diagram_has,
                "implementation": repo_has,
                "issue": "Diagram shows aggregation but implementation doesn't" if diagram_has and not repo_has else "Implementation has fan-in but diagram doesn't show it"
            })
        
        # Calculate consistency score
        consistent_count = sum(1 for v in comparison["diagram_vs_implementation"].values() if v["consistent"])
        comparison["consistency_score"] = (consistent_count / len(comparison["diagram_vs_implementation"])) * 100
        
        # Display results
        print(f"\n📊 Diagram vs Implementation Consistency:")
        print(f"   Parallel Detectives: {'✅' if comparison['diagram_vs_implementation']['parallel_detectives']['consistent'] else '❌'}")
        print(f"   Evidence Aggregation: {'✅' if comparison['diagram_vs_implementation']['evidence_aggregation']['consistent'] else '❌'}")
        print(f"\n   Consistency Score: {comparison['consistency_score']:.1f}%")
        
        if comparison["discrepancies"]:
            print(f"\n⚠️  Discrepancies found:")
            for d in comparison["discrepancies"]:
                print(f"   - {d['issue']}")
        
        # Merge with vision results
        vision_results["cross_reference"] = comparison
        
        return vision_results
    
    def run_full_inspection(self) -> Dict[str, Any]:
        """
        Run complete vision inspection
        """
        print("\n" + "="*60)
        print("🖼️ STARTING VISION INSPECTION")
        print("="*60)
        
        try:
            self.setup()
            
            # Step 1: Extract images
            image_paths = self.extract_images_from_pdf()
            if not image_paths:
                return {"error": "No images extracted from PDF"}
            
            # Step 2: Analyze each diagram page
            vision_results = []
            diagram_count = 0
            
            for img_info in self.extracted_images:
                if img_info["likely_diagram"]:
                    diagram_count += 1
                    print(f"\n{'='*40}")
                    print(f"📐 Analyzing Diagram {diagram_count} (Page {img_info['page']})")
                    print(f"{'='*40}")
                    
                    # Classify diagram
                    classification = self.classify_diagram(img_info["path"])
                    
                    # Detect patterns
                    patterns = self.detect_architecture_patterns(img_info["path"])
                    
                    # Combine results
                    vision_results.append({
                        "page": img_info["page"],
                        "image_path": img_info["path"],
                        "classification": classification,
                        "patterns": patterns,
                        "has_parallel_detectives": classification.get("has_parallel_detectives", False) or patterns.get("has_parallel_structure", False),
                        "has_aggregation": classification.get("has_aggregation", False) or patterns.get("has_fan_in", False),
                        "has_parallel_judges": classification.get("has_parallel_judges", False),
                        "has_chief_justice": classification.get("has_chief_justice", False),
                        "confidence": classification.get("confidence", 0.5)
                    })
            
            # Step 3: Verify architecture
            architecture_verification = self.verify_architecture(vision_results)
            
            # Step 4: Cross-reference with repo
            final_results = self.cross_reference_with_repo(architecture_verification)
            
            # Add metadata
            final_results.update({
                "total_diagrams_analyzed": diagram_count,
                "diagram_details": vision_results,
                "pdf_analyzed": self.pdf_path
            })
            
            print("\n" + "="*60)
            print("✅ VISION INSPECTION COMPLETE")
            print("="*60)
            
            return final_results
            
        except Exception as e:
            print(f"❌ Error in vision inspection: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
            
        finally:
            self.cleanup()


# Standalone function for easy use
def inspect_diagrams(pdf_path: str, repo_evidence_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Main entry point for vision inspection
    
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
    
    inspector = VisionInspector(pdf_path, repo_evidence)
    return inspector.run_full_inspection()