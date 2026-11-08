"""Add a root lookup index to the unsealed verification candidate."""

import hashlib
import json
import sqlite3
from pathlib import Path


task = Path(__file__).resolve().parent
output = task / "index_02"
database = output / "dialogue.partial.sqlite3"
receipt = output / "lookup_optimization.json"
if receipt.exists():
    raise SystemExit("Lookup optimization already recorded")
connection = sqlite3.connect(database, timeout=60)
status = connection.execute("SELECT value FROM metadata WHERE key='status'").fetchone()[0]
if status != "INDEXED_PENDING_VERIFICATION":
    raise SystemExit("Only the unsealed candidate accepts lookup optimization")
before = connection.execute(
    "EXPLAIN QUERY PLAN SELECT loc_id FROM localization WHERE root_id=?", ("probe",)
).fetchall()
connection.execute("CREATE INDEX localization_root_lookup ON localization(root_id)")
connection.commit()
after = connection.execute(
    "EXPLAIN QUERY PLAN SELECT loc_id FROM localization WHERE root_id=?", ("probe",)
).fetchall()
connection.close()
with Path(__file__).open("rb") as stream:
    tool_hash = hashlib.file_digest(stream, "sha256").hexdigest().upper()
result = {
    "status": "LOOKUP_INDEX_ADDED",
    "sql": "CREATE INDEX localization_root_lookup ON localization(root_id)",
    "before_query_plan": before,
    "after_query_plan": after,
    "tool_sha256": tool_hash,
    "scope": "Audit-database lookup index. Scene, event, actor, line and localization records are preserved.",
}
with receipt.open("x", encoding="utf-8") as stream:
    json.dump(result, stream, indent=2)
    stream.write("\n")
print(json.dumps(result, indent=2))
