import os
import sys

# Create directories
base = os.path.expanduser("~/.kimi_openclaw/workspace/seven_lamps")
dirs = ["core", "cards", "mechanics", "deck", "ui", "tests"]
for d in dirs:
    path = os.path.join(base, d)
    os.makedirs(path, exist_ok=True)
    # Create __init__.py
    open(os.path.join(path, "__init__.py"), "w", encoding="utf-8").close()

print("Directories created successfully!")
