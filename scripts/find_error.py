import os

def find_string(search_str, search_path="."):
    for root, dirs, files in os.walk(search_path):
        if ".venv" in dirs:
            dirs.remove(".venv")
        if ".git" in dirs:
            dirs.remove(".git")
        for file in files:
            if file.endswith((".py", ".sh", ".txt", ".md", ".json")):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        for i, line in enumerate(f, 1):
                            if search_str.lower() in line.lower():
                                print(f"{full_path}:{i}: {line.strip()}")
                except Exception:
                    pass

if __name__ == "__main__":
    print("Searching for 'Paper with id'...")
    find_string("Paper with id")
    print("Searching for 'Paper not found'...")
    find_string("Paper not found")
