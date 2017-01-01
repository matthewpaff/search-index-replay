# Search Index Replay

Replay versioned document upserts and deletes with duplicate suppression and deletion tombstones.

Uses Python 3.10+ and its standard library only. No package installation, virtual
environment, external server, Redis, Celery, or network access is required.

## Run

```console
python -m index_lab --help
python -m index_lab examples/sample.json
python -m index_lab --check-fixtures fixtures/cases.jsonl
python generate_fixtures.py --count 20
python -m unittest discover -s tests -v
```

Run from this directory. The optional path defaults to `-`, which reads JSON from
stdin. Output is JSON or a fixture-check summary. Exit codes are 0 success,
1 file failure, and 2 invalid input. Examples and fixtures contain generated data.

Input is an object containing exactly events, a list of at most 1000 operations. An upsert has exactly op, id, version, and document; a delete has exactly op, id, and version. IDs contain 1-80 characters without whitespace or control characters; versions are positive integers up to 10^12, with booleans rejected. Documents are JSON objects with at most 100 string-keyed fields. Only a higher version changes a document; equal versions are duplicate and lower versions stale, even when their payload or operation differs. A delete retains a version tombstone, including for a previously unknown ID, so older updates cannot recreate it. A higher version may recreate a deleted document. Results retain event order; documents and version/tombstone rows sort by ID. Inputs are not modified and stored documents are deep-copied. This in-memory concept exercise does not contact Elasticsearch, persist an index, search documents, resolve concurrent writes, or guarantee production consistency.

## Learning focus

The modeled 2017 search-sync learning theme: event ordering, replay, document versions, and eventual-consistency edge cases. This is an independent concept exercise based on the modeled
roadmap. It makes no claim to be employer-owned or period-authentic production code.

## Structure

- `index_lab/core.py`: validated parsing, storage, or state transitions.
- `index_lab/cli.py`: JSON command interface.
- `index_lab/generate_fixtures.py`: original deterministic validation cases.
- `index_lab/fixture_check.py`: expected-output/error checks.
- `fixtures/cases.jsonl`: 366 generated cases, with explicit descriptions.
- `tests/`: independently selected boundaries and the complete corpus check.

Branches `feature/core`, `feature/cli`, `data/fixtures`, and `docs/usage` retain
snapshots; `main` contains the complete tool. Dates and provenance are also recorded
in TIMELINE.json. Many data cases share a scenario; they are not separate features.

Keep changes focused, use actual dates for new work, and add a regression test
for changed behavior. Licensed under [MIT](LICENSE).

[History and provenance](HISTORY.md).
