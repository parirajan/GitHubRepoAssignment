import json
from pathlib import Path

from exclude_specific_entries import ExcludeSpecificEntries


# ---- stub, replace with your real lookup -----------------
def getElementByUidFromTargetEnv(uid, *args, **kwargs):
    """
    Dummy implementation just to satisfy the interface.
    In real life this would query the target environment.
    Raise an exception to simulate 'not found'.
    """
    existing_ids = set()  # or {'123', '456'} if you want to test
    if str(uid) in existing_ids:
        return {"uid": uid}   # found
    else:
        raise KeyError("ITEM_NOT_FOUND")
# -----------------------------------------------------------


def iter_journal_entries(fp):
    """
    Generator that yields one JSON object at a time.

    If your file is truly NDJSON (one JSON object per line), this version works:

        for line in fp:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)

    BUT if your entries are pretty-printed over multiple lines, use a small
    buffer that accumulates until a full JSON object parses.
    """
    buffer = ""
    for line in fp:
        if not line.strip():
            continue
        buffer += line
        try:
            obj = json.loads(buffer)
            yield obj
            buffer = ""  # reset buffer after successful parse
        except json.JSONDecodeError:
            # not a complete object yet, keep appending lines
            continue

    if buffer.strip():
        # last partial object (if any)
        yield json.loads(buffer)


def main(in_file: Path, out_file: Path):
    excluder = ExcludeSpecificEntries()

    with in_file.open() as f_in, out_file.open("w") as f_out:
        for entry in iter_journal_entries(f_in):
            # IMPORTANT: map to your real journal structure
            should_exclude = excluder.apply(entry, getElementByUidFromTargetEnv)

            if not should_exclude:
                # write as NDJSON: one JSON object per line
                f_out.write(json.dumps(entry))
                f_out.write("\n")


if __name__ == "__main__":
    in_path = Path("journal.json")          # your input file
    out_path = Path("journal_filtered.json")
    main(in_path, out_path)
