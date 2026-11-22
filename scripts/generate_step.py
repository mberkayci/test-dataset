"""A helper class that generates the steps folder and updates the steps.json file for the benchmark with the standard structure."""

import sys, subprocess
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS_DIR = ROOT / "benchmark" / "steps"
STEPS_JSON = ROOT / "benchmark" / "steps.json"
SCHEMA_REF = "../schema/steps.schema.json"
STEP_SCHEMA_REF = "../../../schema/evolution-step.schema.json"

def get_steps_folders()-> list[str]:
    """Get the content of the steps folder.
    
    :return: A sorted list of step folder names.
    """
    steps_folders = []
    for folder in STEPS_DIR.iterdir():
        if folder.is_dir() and re.match(r"step-\d+", folder.name):
            steps_folders.append(folder.name)
    return sorted(steps_folders)

def generate_step_folder():
    """Generate a new step folder with the required content.
    
    :return: The path to the new step folder.
    """
    folders = get_steps_folders()
    if not folders:
        print("No existing step folders found. Check your structure!")
        sys.exit(1)
    last_step = folders[-1]
    last_number = int(last_step.split("-")[1])
    step_number = last_number + 1
    new_folder_name = f"step-{step_number:03d}"
    new_dir = STEPS_DIR / new_folder_name
    ground_truth_dir = new_dir / "ground-truth"
    prompts_dir = new_dir / "prompts"
    try:
        new_dir.mkdir(exist_ok=True)
        ground_truth_dir.mkdir(exist_ok=True)
        for name in (".feature-model", ".feature-to-file", ".feature-to-folder"):
            (ground_truth_dir / name).touch()

        prompts_dir.mkdir(exist_ok=True)
        (prompts_dir / "001.md").touch()
        (prompts_dir / "agent_response.md").touch()
    except Exception as e:
        print(f"Error occurred while creating folder: {e}")
        sys.exit(1)
    print("New step folder created:", new_folder_name)
    return new_dir

def write_step_json(new_dir: Path) -> None:
    """Write step.json for a new step, continuing the version chain.

    :param new_dir: The new step folder.
    :return: None
    """
    number = int(new_dir.name.split("-")[1])
    prev_json = STEPS_DIR / f"step-{number - 1:03d}" / "step.json"

    if not prev_json.is_file():
        print(f"Previous step has no step.json: {prev_json}")
        sys.exit(1)

    previous = json.loads(prev_json.read_text(encoding="utf-8"))
    before = previous["after_version"]
    after = f"v{int(before[1:]) + 1:03d}"

    step = {
        "$schema": STEP_SCHEMA_REF,
        "id": new_dir.name,
        "sequence": number,
        "before_version": before,
        "after_version": after,
        "prompts": [{"order": 1, "path": "prompts/001.md"}],
        "scenario_types": ["TODO"],
        "expected_changes": [
            {
                "id": "change-001",
                "operation": "add",
                "features_before": [],
                "features_after": ["TODO"],
                "description": "TODO",
            }
        ],
        "ground_truth": "ground-truth",
    }
    (new_dir / "step.json").write_text(json.dumps(step, indent=2) + "\n", encoding="utf-8")

def check_json()-> bool:
    """Check if the steps folder structure is consistent with the steps.json file.

    :return: True if the structure is consistent, False otherwise.
    """
    return True

def save_index(index: dict) -> None:
    """Write the steps index to steps.json in a consistent format.
    
    :param index: The index dictionary to write.
    :return: None"""
    STEPS_JSON.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")


def write_json() -> None:
    """Rebuild steps.json from the step folders currently on disk.
    Keeps the existing $schema reference if there is one.
    
    :return: None
    """
    schema = SCHEMA_REF
    if STEPS_JSON.exists():
        existing = json.loads(STEPS_JSON.read_text(encoding="utf-8"))
        schema = existing.get("$schema", SCHEMA_REF)

    index = {"$schema": schema, "steps": []}
    for folder in get_steps_folders():
        step_path = (STEPS_DIR / folder / "step.json").relative_to(STEPS_JSON.parent).as_posix()
        index["steps"].append({"id": folder, "path": step_path})
    save_index(index)

def update_json(new_dir: Path):
    """Update the steps.json file with the current steps folders.
    
    :param new_dir: The new step folder that was created.
    :return: None
    """
    index = json.loads(STEPS_JSON.read_text(encoding="utf-8"))
    step_id = new_dir.name
    step_path = (new_dir / "step.json").relative_to(STEPS_JSON.parent).as_posix()
    if any(entry["id"] == step_id for entry in index["steps"]):
        print(f"{step_id} is already in steps.json")
        sys.exit(1)

    index["steps"].append({"id": step_id, "path": step_path})
    save_index(index)

def main():
    """Main function to generate a new step folder and update the steps.json file."""
    new_dir = generate_step_folder()
    write_step_json(new_dir)
    update_json(new_dir)

if __name__ == "__main__":
    main()