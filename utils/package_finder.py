"""
Features:
- Scans both `.py` and `.ipynb` files
- Handles both pip and conda install commands
- Recognizes various install command formats:
    o pip install package
    o pip3 install package
    o python -m pip install package
    o conda install package
- Handles options in install commands (e.g., --upgrade, --quiet)
- Creates sorted, deduplicated package list
- Writes clean package names to requirements.txt
- Error handling for file reading issues
- Progress feedback in console
"""

import os
import re
import json
from typing import Set, List
from pathlib import Path

def find_package_dependencies(directory: str = ".") -> Set[str]:
    """
    Scan all .py and .ipynb files in directory for pip/conda install commands.
    
    Args:
        directory (str): Directory to scan. Defaults to current directory.
        
    Returns:
        Set[str]: Unique package names found
    """
    packages = set()
    
    # Regular expressions for finding install commands
    pip_pattern = r"(?:pip install|pip3 install|python -m pip install)(?:\s+[--]\w+)*\s+([\w\-\[\]]+)"
    conda_pattern = r"conda install(?:\s+[--]\w+)*\s+([\w\-\[\]]+)"
    
    # Walk through directory
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.py', '.ipynb')):
                file_path = Path(root) / file
                
                try:
                    if file.endswith('.py'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                    else:  # .ipynb file
                        with open(file_path, 'r', encoding='utf-8') as f:
                            notebook = json.load(f)
                            content = ''
                            for cell in notebook.get('cells', []):
                                if cell['cell_type'] == 'code':
                                    content += ''.join(cell['source']) + '\n'
                    
                    # Find pip installations
                    pip_packages = re.findall(pip_pattern, content)
                    packages.update(pip_packages)
                    
                    # Find conda installations
                    conda_packages = re.findall(conda_pattern, content)
                    packages.update(conda_packages)
                    
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")
    
    return packages

def write_requirements(packages: Set[str], output_file: str = "requirements.txt"):
    """Write package list to requirements.txt file"""
    sorted_packages = sorted(list(packages))
    with open(output_file, 'w') as f:
        for package in sorted_packages:
            # Clean up package names (remove brackets, quotes, etc)
            clean_package = package.strip('[]"\'')
            f.write(f"{clean_package}\n")

if __name__ == "__main__":
    # Find all packages
    found_packages = find_package_dependencies()
    
    # Write to requirements.txt
    write_requirements(found_packages)
    
    # Print summary
    print(f"\nFound {len(found_packages)} unique packages:")
    for pkg in sorted(found_packages):
        print(f"  - {pkg}")