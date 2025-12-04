import os
import re
import shutil

CATEGORIES = [
    "Practical",
    "Algorithmic",
    "EmulationModeling",
    "ArtificialIntelligence",
    "GameDevelopment",
]

ROOT_DIR = os.getcwd()

README_TEMPLATE = """# {title}

## Overview
{description}

## Requirements
- Python 3.10+
- Dependencies: `requirements.txt` (if applicable)

## How to Run
```bash
# Navigate to the directory
cd "{category}/{folder_name}"

# Run the main script (example)
python main.py
```

## Implementation Details
- **Difficulty**: {difficulty}
- **Status**: {status}

## Notes
(Add any algorithmic notes or design decisions here)
"""


def normalize_name(name):
    return name.replace(" ", "").lower()


def get_readme_info_from_root(challenge_name):
    # This is a heuristic. We'll try to find the line in root README
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    # Regex to find the table row
    # | # | Challenge | Difficulty | Status | Notes |
    pattern = re.escape(challenge_name)
    match = re.search(
        r"\|\s*\d+\s*\|\s*" + pattern + r"\s*\|\s*(\(.\))\s*\|\s*([^|]+)\s*\|", content
    )
    if match:
        return match.group(1), match.group(2).strip()
    return "(Unknown)", "Unknown"


def merge_directories(src, dst):
    print(f"Merging {src} into {dst}...")
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            if not os.path.exists(d):
                shutil.move(s, d)
            else:
                merge_directories(s, d)
                os.rmdir(s)
        else:
            if not os.path.exists(d):
                shutil.move(s, d)
            else:
                print(f"Conflict: {d} already exists. Skipping {s}.")
    try:
        os.rmdir(src)
    except OSError:
        print(f"Could not remove {src}, it might not be empty.")


def fix_duplicates(category_path):
    items = os.listdir(category_path)
    dirs = [
        d
        for d in items
        if os.path.isdir(os.path.join(category_path, d)) and d != "__pycache__"
    ]

    # Map normalized name to list of actual names
    norm_map = {}
    for d in dirs:
        norm = normalize_name(d)
        if norm not in norm_map:
            norm_map[norm] = []
        norm_map[norm].append(d)

    for norm, names in norm_map.items():
        if len(names) > 1:
            # Prefer the one with spaces if it exists, else the first one
            # Actually, check which one has code.
            # Heuristic: Prefer "Spaced Name" over "SpacedName"
            # But if "SpacedName" has code and "Spaced Name" is empty, keep "SpacedName".

            # Simple strategy: Pick the longest name (usually has spaces) as target
            target = max(names, key=len)
            others = [n for n in names if n != target]

            for other in others:
                src = os.path.join(category_path, other)
                dst = os.path.join(category_path, target)
                merge_directories(src, dst)


def generate_readmes(category):
    category_path = os.path.join(ROOT_DIR, category)
    if not os.path.exists(category_path):
        return

    dirs = [
        d
        for d in os.listdir(category_path)
        if os.path.isdir(os.path.join(category_path, d)) and d != "__pycache__"
    ]

    for d in dirs:
        readme_path = os.path.join(category_path, d, "README.md")
        if not os.path.exists(readme_path):
            print(f"Generating README for {category}/{d}")
            difficulty, status = get_readme_info_from_root(d)
            content = README_TEMPLATE.format(
                title=d,
                description=f"Implementation of the {d} challenge.",
                category=category,
                folder_name=d,
                difficulty=difficulty,
                status=status,
            )
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(content)


def update_root_readme():
    print("Updating root README links...")
    with open("README.md", "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        # Check if line is a table row
        if (
            line.strip().startswith("|")
            and not line.strip().startswith("| :")
            and not line.strip().startswith("| #")
        ):
            # Extract challenge name
            parts = [p.strip() for p in line.split("|")]
            if len(parts) > 3:
                challenge_name = parts[2]
                # Check if it's already a link
                if "[" not in challenge_name:
                    # Find which category it belongs to
                    found = False
                    for cat in CATEGORIES:
                        if os.path.exists(os.path.join(ROOT_DIR, cat, challenge_name)):
                            link = f"[{challenge_name}]({cat}/{challenge_name.replace(' ', '%20')})"
                            line = line.replace(challenge_name, link, 1)
                            found = True
                            break
                    if not found:
                        # Try to find it with normalized name
                        for cat in CATEGORIES:
                            cat_path = os.path.join(ROOT_DIR, cat)
                            if os.path.exists(cat_path):
                                for d in os.listdir(cat_path):
                                    if normalize_name(d) == normalize_name(
                                        challenge_name
                                    ):
                                        link = f"[{challenge_name}]({cat}/{d.replace(' ', '%20')})"
                                        line = line.replace(challenge_name, link, 1)
                                        found = True
                                        break
                                if found:
                                    break
        new_lines.append(line)

    with open("README.md", "w", encoding="utf-8") as f:
        f.writelines(new_lines)


def main():
    for cat in CATEGORIES:
        print(f"Processing {cat}...")
        cat_path = os.path.join(ROOT_DIR, cat)
        if os.path.exists(cat_path):
            fix_duplicates(cat_path)
            generate_readmes(cat)

    update_root_readme()
    print("Done!")


if __name__ == "__main__":
    main()
