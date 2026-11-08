"""Separate embedded choice labels from external spoken-subtitle lookups."""

import hashlib
import json
import shutil
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path


TASK = Path(__file__).resolve().parent
SOURCE = TASK / "index_01"
OUTPUT = TASK / "index_02"


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def main():
    if OUTPUT.exists():
        raise SystemExit("Use a fresh text-qualification successor")
    manifest = json.loads((SOURCE / "database_manifest.json").read_text(encoding="utf-8"))
    source = Path(manifest["path"])
    if sha256(source) != manifest["sha256"]:
        raise SystemExit("Verified parent database changed")
    OUTPUT.mkdir()
    database = OUTPUT / "dialogue.partial.sqlite3"
    shutil.copyfile(source, database)
    connection = sqlite3.connect(database)
    connection.execute(
        "ALTER TABLE search_items ADD COLUMN text_source TEXT DEFAULT 'NON_DIALOGUE_SOURCE'"
    )
    external = defaultdict(list)
    embedded = defaultdict(list)
    for root_id, loc_id, text in connection.execute(
        "SELECT root_id,loc_id,text FROM localization WHERE locale='en_us' AND text<>''"
    ):
        values = external[loc_id] if root_id is None else embedded[(root_id, loc_id)]
        if text not in values:
            values.append(text)
    rows = connection.execute(
        """SELECT item_id,kind,root_id,loc_id,text,depot,speaker,addressee,actor_roles
        FROM search_items WHERE kind IN ('DIALOGUE_EVENT','STORED_LINE','CHOICE')"""
    ).fetchall()
    counts = Counter()
    examples = []
    changed = 0
    for item_id, kind, root_id, loc_id, old_text, depot, speaker, addressee, roles in rows:
        if kind == "CHOICE":
            values = embedded.get((root_id, loc_id), [])
            text_source = "EMBEDDED_CHOICE_VARIANTS" if values else "UNRESOLVED"
        elif external.get(loc_id):
            values = external[loc_id]
            text_source = "EXTERNAL_SUBTITLE_VARIANTS"
        else:
            values = embedded.get((root_id, loc_id), [])
            text_source = "EMBEDDED_ENGLISH_CANDIDATE" if values else "UNRESOLVED"
        text = "\n".join(values)
        if text != old_text:
            connection.execute(
                """INSERT INTO search_fts(search_fts,rowid,text,depot,speaker,addressee,actor_roles)
                VALUES('delete',?,?,?,?,?,?)""",
                (item_id, old_text, depot, speaker, addressee, roles),
            )
            connection.execute(
                "UPDATE search_items SET text=?,text_source=? WHERE item_id=?",
                (text, text_source, item_id),
            )
            connection.execute(
                "INSERT INTO search_fts(rowid,text,depot,speaker,addressee,actor_roles) VALUES(?,?,?,?,?,?)",
                (item_id, text, depot, speaker, addressee, roles),
            )
            changed += 1
            if len(examples) < 12:
                examples.append({"item_id": item_id, "kind": kind, "depot": depot,
                                 "loc_id": loc_id, "text_source": text_source})
        else:
            connection.execute(
                "UPDATE search_items SET text_source=? WHERE item_id=?", (text_source, item_id)
            )
        counts[text_source] += 1
    previous_time = connection.execute(
        "SELECT value FROM metadata WHERE key='verified_utc'"
    ).fetchone()[0]
    connection.execute("DELETE FROM metadata WHERE key='verified_utc'")
    connection.execute("UPDATE metadata SET value='INDEXED_PENDING_VERIFICATION' WHERE key='status'")
    connection.executemany("INSERT INTO metadata VALUES(?,?)", [
        ("base_database_sha256", manifest["sha256"]),
        ("base_verified_utc", previous_time),
        ("text_qualifier_sha256", sha256(Path(__file__))),
    ])
    connection.execute("INSERT INTO search_fts(search_fts,rank) VALUES('integrity-check',1)")
    connection.commit()
    parent_build = json.loads((SOURCE / "index_build.json").read_text(encoding="utf-8"))
    actual_counts = {
        table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        for table in parent_build["counts"]
    }
    statuses = dict(connection.execute("SELECT status,count(*) FROM resources GROUP BY status"))
    connection.close()
    result = {
        "status": "QUALIFIED_PENDING_VERIFICATION",
        "parent_database_sha256": manifest["sha256"],
        "text_items_changed": changed,
        "text_source_counts": dict(counts),
        "examples": examples,
        "rule": "Choices use embedded en_us descriptors. Spoken/stored lines prefer exact-ID external subtitle variants and retain explicitly labelled embedded English candidates when external text is absent.",
    }
    with (OUTPUT / "text_qualification.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    with (OUTPUT / "index_build.json").open("x", encoding="utf-8") as stream:
        json.dump({"counts": actual_counts, "resource_statuses": statuses,
                   "database": str(database), "database_sha256": sha256(database)},
                  stream, indent=2)
        stream.write("\n")
    print(json.dumps({key: value for key, value in result.items() if key != "examples"}, indent=2))


if __name__ == "__main__":
    main()
