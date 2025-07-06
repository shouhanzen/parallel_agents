import json
import time
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from .config import VerifierConfig


class CodeReviewAgent:
    """Agent that reviews source code and suggests potential changes"""
    
    def __init__(self, config: VerifierConfig):
        self.config = config
        self.output_file = Path("potential_todo.jsonl")
        
    def review_codebase(self, src_dir: str = "src") -> List[Dict[str, Any]]:
        """Review the entire codebase and generate suggestions"""
        src_path = Path(src_dir)
        
        if not src_path.exists():
            print(f"❌ Source directory not found: {src_dir}")
            return []
            
        suggestions = []
        
        # Review all Python files
        for py_file in src_path.glob("**/*.py"):
            if py_file.name.startswith("__"):
                continue
                
            file_suggestions = self._review_file(py_file)
            suggestions.extend(file_suggestions)
            
        return suggestions
        
    def _review_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Review a single file and generate suggestions"""
        suggestions = []
        
        try:
            content = file_path.read_text()
            lines = content.split('\n')
            
            # Basic code review checks
            suggestions.extend(self._check_imports(file_path, lines))
            suggestions.extend(self._check_functions(file_path, lines))
            suggestions.extend(self._check_classes(file_path, lines))
            suggestions.extend(self._check_code_quality(file_path, lines))
            
        except Exception as e:
            suggestions.append({
                "file": str(file_path),
                "line": 1,
                "type": "error",
                "severity": "low",
                "title": "File Read Error",
                "description": f"Could not read file: {e}",
                "suggestion": "Check file permissions and encoding",
                "timestamp": datetime.now().isoformat()
            })
            
        return suggestions
        
    def _check_imports(self, file_path: Path, lines: List[str]) -> List[Dict[str, Any]]:
        """Check import statements"""
        suggestions = []
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Check for unused imports (basic heuristic)
            if line.startswith("import ") or line.startswith("from "):
                if "import" in line:
                    # Extract module name
                    if line.startswith("import "):
                        module = line.split("import ")[1].split(" as ")[0].split(".")[0]
                    elif line.startswith("from "):
                        parts = line.split("import ")[1].split(" as ")
                        module = parts[0].split(",")[0].strip()
                    else:
                        continue
                        
                    # Simple check if module is used in the file
                    if module not in " ".join(lines[i:]):
                        suggestions.append({
                            "file": str(file_path),
                            "line": i,
                            "type": "optimization",
                            "severity": "low",
                            "title": "Potential Unused Import",
                            "description": f"Import '{module}' may not be used",
                            "suggestion": f"Remove unused import: {line}",
                            "timestamp": datetime.now().isoformat()
                        })
                        
        return suggestions
        
    def _check_functions(self, file_path: Path, lines: List[str]) -> List[Dict[str, Any]]:
        """Check function definitions"""
        suggestions = []
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Check for functions without docstrings
            if line.startswith("def ") and not line.startswith("def _"):
                # Check if next non-empty line is a docstring
                has_docstring = False
                for j in range(i, min(i + 3, len(lines))):
                    next_line = lines[j].strip()
                    if next_line.startswith('"""') or next_line.startswith("'''"):
                        has_docstring = True
                        break
                        
                if not has_docstring:
                    func_name = line.split("def ")[1].split("(")[0]
                    suggestions.append({
                        "file": str(file_path),
                        "line": i,
                        "type": "documentation",
                        "severity": "medium",
                        "title": "Missing Docstring",
                        "description": f"Function '{func_name}' lacks documentation",
                        "suggestion": f"Add docstring to function {func_name}",
                        "timestamp": datetime.now().isoformat()
                    })
                    
            # Check for long functions (> 50 lines)
            if line.startswith("def "):
                func_start = i
                func_end = i
                indent_level = len(line) - len(line.lstrip())
                
                for j in range(i, len(lines)):
                    if j == i:
                        continue
                    current_line = lines[j]
                    if current_line.strip() and len(current_line) - len(current_line.lstrip()) <= indent_level:
                        func_end = j
                        break
                else:
                    func_end = len(lines)
                    
                if func_end - func_start > 50:
                    func_name = line.split("def ")[1].split("(")[0]
                    suggestions.append({
                        "file": str(file_path),
                        "line": i,
                        "type": "refactoring",
                        "severity": "medium",
                        "title": "Long Function",
                        "description": f"Function '{func_name}' is {func_end - func_start} lines long",
                        "suggestion": f"Consider breaking down function {func_name} into smaller functions",
                        "timestamp": datetime.now().isoformat()
                    })
                    
        return suggestions
        
    def _check_classes(self, file_path: Path, lines: List[str]) -> List[Dict[str, Any]]:
        """Check class definitions"""
        suggestions = []
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Check for classes without docstrings
            if line.startswith("class "):
                # Check if next non-empty line is a docstring
                has_docstring = False
                for j in range(i, min(i + 3, len(lines))):
                    next_line = lines[j].strip()
                    if next_line.startswith('"""') or next_line.startswith("'''"):
                        has_docstring = True
                        break
                        
                if not has_docstring:
                    class_name = line.split("class ")[1].split("(")[0].split(":")[0]
                    suggestions.append({
                        "file": str(file_path),
                        "line": i,
                        "type": "documentation",
                        "severity": "medium",
                        "title": "Missing Class Docstring",
                        "description": f"Class '{class_name}' lacks documentation",
                        "suggestion": f"Add docstring to class {class_name}",
                        "timestamp": datetime.now().isoformat()
                    })
                    
        return suggestions
        
    def _check_code_quality(self, file_path: Path, lines: List[str]) -> List[Dict[str, Any]]:
        """Check general code quality issues"""
        suggestions = []
        
        for i, line in enumerate(lines, 1):
            original_line = line
            line = line.strip()
            
            # Check for TODO comments
            if "TODO" in line.upper() or "FIXME" in line.upper():
                suggestions.append({
                    "file": str(file_path),
                    "line": i,
                    "type": "todo",
                    "severity": "low",
                    "title": "TODO Comment Found",
                    "description": f"TODO comment: {line}",
                    "suggestion": "Consider creating a proper task or issue for this TODO",
                    "timestamp": datetime.now().isoformat()
                })
                
            # Check for long lines (> 120 chars)
            if len(original_line) > 120:
                suggestions.append({
                    "file": str(file_path),
                    "line": i,
                    "type": "style",
                    "severity": "low",
                    "title": "Long Line",
                    "description": f"Line is {len(original_line)} characters long",
                    "suggestion": "Consider breaking long line into multiple lines",
                    "timestamp": datetime.now().isoformat()
                })
                
            # Check for hardcoded values
            if any(keyword in line for keyword in ["localhost", "127.0.0.1", "password", "secret"]):
                suggestions.append({
                    "file": str(file_path),
                    "line": i,
                    "type": "security",
                    "severity": "high",
                    "title": "Potential Hardcoded Value",
                    "description": f"Possible hardcoded value: {line[:50]}...",
                    "suggestion": "Consider using configuration or environment variables",
                    "timestamp": datetime.now().isoformat()
                })
                
        return suggestions
        
    def write_suggestions(self, suggestions: List[Dict[str, Any]]) -> None:
        """Write suggestions to the output file"""
        try:
            with open(self.output_file, 'w') as f:
                for suggestion in suggestions:
                    f.write(json.dumps(suggestion) + '\n')
                    
            print(f"✅ Wrote {len(suggestions)} suggestions to {self.output_file}")
        except Exception as e:
            print(f"❌ Error writing suggestions: {e}")
            
    def run_review(self) -> None:
        """Run the complete review process"""
        print("🔍 Starting code review...")
        
        # Review source code
        suggestions = self.review_codebase()
        
        if not suggestions:
            print("✅ No suggestions found - code looks good!")
            return
            
        # Sort suggestions by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda x: severity_order.get(x["severity"], 3))
        
        print(f"📋 Found {len(suggestions)} suggestions:")
        
        # Summary by type
        by_type = {}
        for suggestion in suggestions:
            stype = suggestion["type"]
            by_type[stype] = by_type.get(stype, 0) + 1
            
        for stype, count in sorted(by_type.items()):
            print(f"  {stype}: {count}")
            
        # Write to file
        self.write_suggestions(suggestions)
        
        print(f"🎯 Review complete! Check {self.output_file} for detailed suggestions")