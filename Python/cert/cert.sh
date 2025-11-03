# run_filter.py
import json
from pathlib import Path

from exclude_specific_entries import ExcludeSpecificEntries


# This function is injected into .apply()
# In real life this might call a DB, REST API, etc.
def getElementByUidFromTargetEnv(uid, *args, **kwargs):
    """
    Dummy implementation.
    Raise an exception to simulate 'ITEM_NOT_FOUND'.
    """
    # Example: if you want to pretend some IDs exist:
    existing_ids = {"123", "456"}
    if str(uid) in existing_ids:
        return {"uid": uid}  # found
    else:
        raise KeyError("ITEM_NOT_FOUND")


def main(in_path: Path, out_path: Path):
    # 1) Load journal file
    with in_path.open() as f:
        journal_entries = json.load(f)

    # 2) Instantiate filter
    excluder = ExcludeSpecificEntries()

    # 3) Apply filter
    kept_entries = []
    for entry in journal_entries:
        should_exclude = excluder.apply(entry, getElementByUidFromTargetEnv)
        if not should_exclude:
            kept_entries.append(entry)

    # 4) Write filtered journal
    with out_path.open("w") as f:
        json.dump(kept_entries, f, indent=2)


if __name__ == "__main__":
    in_file = Path("journal.json")
    out_file = Path("journal_filtered.json")
    main(in_file, out_file)
