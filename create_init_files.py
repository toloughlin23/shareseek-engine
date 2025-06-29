
import os

folders_to_init = [
    ".",              # root folder (Share-Seek)
    "engine",
    "tests"
]

for folder in folders_to_init:
    init_path = os.path.join(folder, "__init__.py")
    if not os.path.exists(init_path):
        with open(init_path, "w") as f:
            f.write("# Automatically created __init__.py\n")
        print(f"Created: {init_path}")
    else:
        print(f"Already exists: {init_path}")
