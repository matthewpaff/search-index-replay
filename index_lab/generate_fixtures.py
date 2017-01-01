"""Original document event cases; these are not Elasticsearch records."""


def upsert(key, version, document):
    return {"op": "upsert", "id": key, "version": version, "document": document}


def delete(key, version):
    return {"op": "delete", "id": key, "version": version}


def outcome(kind, key, version, label):
    return {"op": kind, "id": key, "version": version, "outcome": label}


def document(key, version, value):
    return {"id": key, "version": version, "document": value}


def version_row(key, version, deleted=False):
    return {"id": key, "version": version, "deleted": deleted}


def make_case(index):
    key, kind = "doc-{}".format(index), index % 12
    first = {"title": "Sample {}".format(index), "category": "reference"}
    replacement = {"title": "Replacement {}".format(index)}
    data = {"events": [upsert(key, 1, first)]}
    if kind == 0:
        data["events"][0]["version"] = True
        description = "reject booleans as document versions"
    elif kind == 1:
        data["events"][0]["version"] = 0
        description = "reject zero-valued document versions"
    elif kind == 2:
        data["events"][0]["op"] = "merge"
        description = "reject unsupported index operations"
    elif kind == 3:
        data["events"][0]["document"] = "not-an-object"
        description = "reject non-object document payloads"
    elif kind == 4:
        data["events"][0]["id"] = " "
        description = "reject blank document identifiers"
    elif kind == 5:
        data["events"] = [{**delete(key, 1), "document": first}]
        description = "reject unexpected payloads on delete events"
    elif kind == 6:
        data["events"] = []
        expected = {"results": [], "documents": [], "versions": []}
        description = "replay an empty index event collection"
    elif kind == 7:
        version = 1 + index % 7
        data["events"] = [upsert(key, version, first)]
        expected = {"results": [outcome("upsert", key, version, "indexed")],
                    "documents": [document(key, version, first)], "versions": [version_row(key, version)]}
        description = "index an initial document with its supplied version"
    elif kind == 8:
        data["events"] = [upsert(key, 2, first), upsert(key, 2, replacement)]
        expected = {"results": [outcome("upsert", key, 2, "indexed"), outcome("upsert", key, 2, "duplicate")],
                    "documents": [document(key, 2, first)], "versions": [version_row(key, 2)]}
        description = "retain the first payload on duplicate document versions"
    elif kind == 9:
        data["events"] = [upsert(key, 5, first), upsert(key, 3, replacement)]
        expected = {"results": [outcome("upsert", key, 5, "indexed"), outcome("upsert", key, 3, "stale")],
                    "documents": [document(key, 5, first)], "versions": [version_row(key, 5)]}
        description = "ignore out-of-order updates below the stored version"
    elif kind == 10:
        data["events"] = [upsert(key, 2, first), delete(key, 4), upsert(key, 3, replacement)]
        expected = {"results": [outcome("upsert", key, 2, "indexed"), outcome("delete", key, 4, "deleted"), outcome("upsert", key, 3, "stale")],
                    "documents": [], "versions": [version_row(key, 4, True)]}
        description = "retain deletion tombstones against late older updates"
    else:
        other = key + "-other"
        data["events"] = [delete(key, 3), upsert(key, 2, first), upsert(other, 1, replacement)]
        expected = {"results": [outcome("delete", key, 3, "deleted"), outcome("upsert", key, 2, "stale"), outcome("upsert", other, 1, "indexed")],
                    "documents": [document(other, 1, replacement)], "versions": [version_row(key, 3, True), version_row(other, 1)]}
        description = "isolate new document indexing from unrelated tombstones"
    result = {"id": "index-{:04d}".format(index), "description": description, "input": data}
    result.update({"expected_error": True} if kind < 6 else {"expected": expected})
    return result
