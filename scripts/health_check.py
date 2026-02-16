import os
import ast
import sys

def check_file(filepath):
    """
    Parses a python file to check for syntax errors.
    Returns: (is_valid, message)
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        ast.parse(source)
        return True, "OK"
    except SyntaxError as e:
        return False, f"SyntaxError: {e.msg} at line {e.lineno}"
    except Exception as e:
        return False, f"Error: {e}"

def scan_project(root_dir):
    print(f"Scanning project: {root_dir}")
    print("="*60)
    
    error_count = 0
    file_count = 0
    
    for root, dirs, files in os.walk(root_dir):
        # Skip venv and git
        if ".venv" in dirs: dirs.remove(".venv")
        if ".git" in dirs: dirs.remove(".git")
        if "__pycache__" in dirs: dirs.remove("__pycache__")
        
        for file in files:
            if file.endswith(".py"):
                file_count += 1
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, root_dir)
                
                is_valid, msg = check_file(full_path)
                
                if not is_valid:
                    print(f"❌ {rel_path}: {msg}")
                    error_count += 1
                else:
                    # Optional: Print verbose success? No, keep it clean.
                    pass

    print("="*60)
    print(f"Scan Complete.")
    print(f"Files Scanned: {file_count}")
    print(f"Errors Found: {error_count}")
    
    if error_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    scan_project(os.getcwd())
