# list_files.py
import os

def list_tree(dir_path):
    for root, dirs, files in os.walk(dir_path):
        level = root.replace(dir_path, "").count(os.sep)
        indent = " " * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        for f in files:
            print(f"{indent}    {f}")

if __name__ == "__main__":
    here = os.path.abspath(os.path.dirname(__file__))
    print(f"Contents of {here}:\n")
    list_tree(here)
