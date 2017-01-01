"""Replay supplied document events in memory, retaining deletion tombstones."""
from copy import deepcopy


def replay_index(data):
    if not isinstance(data, dict) or set(data) != {"events"} or not isinstance(data["events"], list) or len(data["events"]) > 1000:
        raise ValueError("Supply an object with at most 1000 events")
    documents, versions, results = {}, {}, []
    for event in data["events"]:
        if not isinstance(event, dict):
            raise ValueError("Index event must be an object")
        kind = event.get("op")
        if kind not in ("upsert", "delete"):
            raise ValueError("Operation must be upsert or delete")
        required = {"op", "id", "version", "document"} if kind == "upsert" else {"op", "id", "version"}
        if set(event) != required:
            raise ValueError("Unexpected or missing index event fields")
        key, version = event["id"], event["version"]
        if not isinstance(key, str) or not 1 <= len(key) <= 80 or any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in key):
            raise ValueError("Document ID must contain 1-80 characters without whitespace or controls")
        if type(version) is not int or not 1 <= version <= 10 ** 12:
            raise ValueError("Version must be an integer from 1 to 10^12")
        if kind == "upsert" and (not isinstance(event["document"], dict) or len(event["document"]) > 100 or any(not isinstance(field, str) for field in event["document"])):
            raise ValueError("Document must be an object with at most 100 string-keyed fields")
        previous = versions.get(key, 0)
        if version == previous:
            outcome = "duplicate"
        elif version < previous:
            outcome = "stale"
        else:
            versions[key] = version
            if kind == "upsert":
                documents[key] = deepcopy(event["document"])
                outcome = "indexed"
            else:
                documents.pop(key, None)
                outcome = "deleted"
        results.append({"op": kind, "id": key, "version": version, "outcome": outcome})
    return {"results": results,
            "documents": [{"id": key, "version": versions[key], "document": deepcopy(documents[key])} for key in sorted(documents)],
            "versions": [{"id": key, "version": versions[key], "deleted": key not in documents} for key in sorted(versions)]}
