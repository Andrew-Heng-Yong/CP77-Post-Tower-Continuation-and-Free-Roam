"""Independently compare indexed scene records with their source exports."""

import argparse
import gzip
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


TASK = Path(__file__).resolve().parent
WORKSPACE = TASK.parents[1]
EVIDENCE = TASK / "evidence_01"


def read_json(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8-sig") as stream:
        return json.load(stream)


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def source_value(value):
    if not isinstance(value, dict):
        return str(value) if value is not None else None
    for field in ("id", "ruid", "$value", "mask", "val"):
        if field in value:
            return str(value[field])
    return None


def objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from objects(child)


def verify_scene(connection, row, failures):
    document = read_json(row["json"])
    handles = {
        str(value["HandleId"]): value["Data"]
        for value in objects(document)
        if "HandleId" in value and "Data" in value
    }

    def dereference(value):
        if not isinstance(value, dict):
            return value
        if "Data" in value and "HandleId" in value:
            return value["Data"]
        if "HandleRefId" in value:
            return handles.get(str(value["HandleRefId"]))
        return value

    roots = [("root", document["Data"]["RootChunk"])]
    for ordinal, embedded in enumerate(document["Data"].get("EmbeddedFiles", [])):
        content = embedded.get("Content", {})
        if "sceneGraph" in content or "screenplayStore" in content:
            roots.append((f"embedded/{ordinal}/{source_value(embedded.get('FileName'))}", content))
    for subresource, root in roots:
        root_id = row["resource_id"] + "/" + subresource
        graph = dereference(root.get("sceneGraph"))
        nodes = [dereference(value) for value in graph.get("graph", [])] if isinstance(graph, dict) else []
        expected_nodes = {source_value(node.get("nodeId")) for node in nodes}
        actual_nodes = {
            value[0] for value in connection.execute(
                "SELECT node_id FROM nodes WHERE root_id=? AND graph_path='scene'", (root_id,)
            )
        }
        if expected_nodes != actual_nodes:
            failures.append({"resource": row["resource_id"], "root": subresource, "kind": "NODE_INVENTORY"})
        expected_entries = [
            (source_value(entry.get("name")), source_value(entry.get("nodeId")))
            for entry in root.get("entryPoints", [])
        ]
        actual_entries = list(connection.execute(
            "SELECT name,node_id FROM entries WHERE root_id=? AND graph_path='scene'", (root_id,)
        ))
        if Counter(expected_entries) != Counter(actual_entries):
            failures.append({"resource": row["resource_id"], "root": subresource,
                             "kind": "SCENE_ENTRY_NAMES_AND_TARGETS"})
        expected_events = []
        expected_edges = []
        expected_choices = []
        option_definitions = {
            source_value(option.get("itemId")): option
            for option in root.get("screenplayStore", {}).get("options", [])
        }
        for node in nodes:
            node_id = source_value(node.get("nodeId"))
            for ordinal, handle in enumerate(node.get("events", [])):
                event = dereference(handle)
                expected_events.append((
                    node_id, ordinal, source_value(event.get("id")), event.get("$type"),
                    source_value(event.get("screenplayLineId")),
                    source_value(event.get("startTime")), source_value(event.get("duration")),
                ))
            for socket in node.get("outputSockets", []):
                stamp = socket.get("stamp", {})
                output = f"{stamp.get('name',0)}:{stamp.get('ordinal',0)}"
                for destination in socket.get("destinations", []):
                    input_stamp = destination.get("isockStamp", {})
                    expected_edges.append((
                        node_id, output, source_value(destination.get("nodeId")),
                        f"{input_stamp.get('name',0)}:{input_stamp.get('ordinal',0)}",
                    ))
            if node.get("$type") != "scnChoiceNode":
                continue
            for ordinal, option in enumerate(node.get("options", [])):
                option_id = source_value(option.get("screenplayOptionId"))
                definition = option_definitions.get(option_id, {})
                expected_choices.append((
                    node_id, ordinal, option_id, source_value(definition.get("locstringId")),
                    f"0:{ordinal}",
                ))
        actual_events = list(connection.execute(
            """SELECT node_id,event_ordinal,event_id,type,line_id,start_time,duration FROM events
            WHERE root_id=? AND graph_path='scene'""", (root_id,)
        ))
        actual_edges = list(connection.execute(
            """SELECT source_node,output_stamp,destination_node,input_stamp FROM edges
            WHERE root_id=? AND graph_path='scene'""", (root_id,)
        ))
        actual_choices = list(connection.execute(
            """SELECT node_id,option_ordinal,option_id,loc_id,output_stamp FROM choices
            WHERE root_id=? AND graph_path='scene'""", (root_id,)
        ))
        for kind, expected, actual in (
            ("EVENT_IDENTITIES_AND_TIMES", expected_events, actual_events),
            ("SOCKET_NAMES_ORDINALS_AND_MULTIPLICITY", expected_edges, actual_edges),
            ("CHOICE_IDENTITIES_AND_CAPTIONS", expected_choices, actual_choices),
        ):
            if Counter(expected) != Counter(actual):
                failures.append({
                    "resource": row["resource_id"], "root": subresource, "kind": kind,
                    "expected_count": len(expected), "actual_count": len(actual),
                    "missing_sample": list((Counter(expected) - Counter(actual)).items())[:3],
                    "extra_sample": list((Counter(actual) - Counter(expected)).items())[:3],
                })
        expected_lines = {
            source_value(line.get("itemId")): (
                source_value(line.get("speaker")), source_value(line.get("addressee")),
                source_value(line.get("locstringId")),
                source_value(line.get("usage", {}).get("playerGenderMask")),
                source_value(line.get("maleLipsyncAnimationName")),
                source_value(line.get("femaleLipsyncAnimationName")),
            )
            for line in root.get("screenplayStore", {}).get("lines", [])
        }
        actual_lines = {
            values[0]: tuple(values[1:]) for values in connection.execute(
                """SELECT line_id,speaker_id,addressee_id,loc_id,gender_mask,male_lipsync,
                female_lipsync FROM lines WHERE root_id=?""", (root_id,)
            )
        }
        if expected_lines != actual_lines:
            failures.append({"resource": row["resource_id"], "root": subresource,
                             "kind": "LINE_SPEAKER_ADDRESSEE_AND_GENDER_BINDINGS"})
        expected_actors = {
            source_value(actor.get("actorId")): actor
            for actor in root.get("actors", []) + root.get("playerActors", [])
        }
        actual_actors = {
            values[0]: json.loads(values[1]) for values in connection.execute(
                "SELECT actor_id,binding_json FROM actors WHERE root_id=?", (root_id,)
            )
        }
        if expected_actors != actual_actors:
            failures.append({"resource": row["resource_id"], "root": subresource,
                             "kind": "ACTOR_AND_PLAYER_BINDING_INVENTORY"})
        store = root.get("locStore", {})
        payloads = store.get("vpEntries", [])
        expected_localization = []
        for ordinal, descriptor in enumerate(store.get("vdEntries", [])):
            index = descriptor["vpeIndex"]
            if not 0 <= index < len(payloads):
                continue
            expected_localization.append((
                source_value(descriptor.get("locstringId")), descriptor["localeId"],
                source_value(descriptor.get("signature")), payloads[index].get("content", ""),
                f"locStore/vdEntries/{ordinal}",
            ))
        actual_localization = list(connection.execute(
            "SELECT loc_id,locale,signature,text,source_path FROM localization WHERE root_id=?",
            (root_id,),
        ))
        if Counter(expected_localization) != Counter(actual_localization):
            failures.append({"resource": row["resource_id"], "root": subresource,
                             "kind": "EMBEDDED_LOCALIZATION_IDENTITIES_AND_PAYLOADS"})


def verify_text_domains(connection, failures):
    external = defaultdict(set)
    embedded = defaultdict(set)
    for root_id, loc_id, text in connection.execute(
        "SELECT root_id,loc_id,text FROM localization WHERE locale='en_us' AND text<>''"
    ):
        target = external[loc_id] if root_id is None else embedded[(root_id, loc_id)]
        target.add(text)
    checked = 0
    for item_id, kind, root_id, loc_id, text, source in connection.execute(
        """SELECT item_id,kind,root_id,loc_id,text,text_source FROM search_items
        WHERE kind IN ('DIALOGUE_EVENT','STORED_LINE','CHOICE')"""
    ):
        if kind == "CHOICE":
            permitted = embedded[(root_id, loc_id)]
            expected_source = "EMBEDDED_CHOICE_VARIANTS" if permitted else "UNRESOLVED"
        elif external[loc_id]:
            permitted = external[loc_id]
            expected_source = "EXTERNAL_SUBTITLE_VARIANTS"
        else:
            permitted = embedded[(root_id, loc_id)]
            expected_source = "EMBEDDED_ENGLISH_CANDIDATE" if permitted else "UNRESOLVED"
        # Preserve every line of every variant while allowing variant display order to differ.
        actual_pieces = Counter(text.split("\n")) if text else Counter()
        expected_pieces = Counter(piece for value in permitted for piece in value.split("\n"))
        if source != expected_source or actual_pieces != expected_pieces:
            failures.append({"kind": "TEXT_DOMAIN", "item_id": item_id})
        if bool(text) != bool(permitted):
            failures.append({"kind": "TEXT_AVAILABILITY", "item_id": item_id})
        checked += 1
    return checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", default="index_01")
    arguments = parser.parse_args()
    output = (TASK / arguments.index).resolve()
    if output.parent != TASK:
        parser.error("Use a task-local index directory")
    database = output / "dialogue.partial.sqlite3"
    if (output / "verification.json").exists():
        raise SystemExit("Use a fresh verification successor")
    build = read_json(output / "index_build.json")
    if sha256(database) != build["database_sha256"]:
        raise SystemExit("Unverified database changed after building")
    rows = [
        json.loads(line)
        for line in (EVIDENCE / "exports.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    prepared = read_json(EVIDENCE / "prepared.json")
    connection = sqlite3.connect(database)
    failures = []
    metadata = dict(connection.execute("SELECT key,value FROM metadata"))
    if metadata["indexer_sha256"] != sha256(TASK / "build_index.py"):
        failures.append({"kind": "INDEXER_SOURCE_CHANGED"})
    if metadata["model_sha256"] != sha256(WORKSPACE / "tools/parity_audit/model.py"):
        failures.append({"kind": "NORMALIZER_SOURCE_CHANGED"})
    if metadata["capture_manifest_sha256"] != sha256(EVIDENCE / "exports.jsonl"):
        failures.append({"kind": "EXPORT_MANIFEST_CHANGED"})
    qualified = "text_qualifier_sha256" in metadata
    if qualified and metadata["text_qualifier_sha256"] != sha256(TASK / "qualify_text.py"):
        failures.append({"kind": "TEXT_QUALIFIER_SOURCE_CHANGED"})
    expected_scene_ids = {row["resource_id"] for row in prepared["scenes"]}
    indexed_scene_ids = {
        row[0] for row in connection.execute("SELECT resource_id FROM resources WHERE kind='SCENE'")
    }
    if expected_scene_ids != indexed_scene_ids:
        failures.append({"kind": "SCENE_PROVIDER_INPUT_INVENTORY"})
    checked_files = {}
    for row in rows:
        for field, hash_field in (("raw", "sha256"), ("json", "json_sha256")):
            if not row.get(field):
                continue
            path = Path(row[field])
            if path not in checked_files:
                checked_files[path] = sha256(path) if path.is_file() else None
            if checked_files[path] != row[hash_field]:
                failures.append({"kind": "SOURCE_OR_EXPORT_CHANGED", "path": str(path)})
    statuses = dict(connection.execute("SELECT status,count(*) FROM resources GROUP BY status"))
    if statuses.get("INDEX_ERROR"):
        failures.append({"kind": "INDEX_ERRORS_REMAIN", "count": statuses["INDEX_ERROR"]})
    indexed = dict(connection.execute("SELECT resource_id,status FROM resources"))
    checked_scenes = 0
    for row in rows:
        if row["kind"] != "SCENE" or indexed[row["resource_id"]] != "INDEXED":
            continue
        verify_scene(connection, row, failures)
        checked_scenes += 1
        if checked_scenes % 500 == 0:
            print(json.dumps({"source_scenes_checked": checked_scenes,
                              "failures": len(failures)}), flush=True)
    for row in prepared["checks"]:
        path = Path(row["path"])
        actual = sha256(path) if path.is_file() else None
        if actual != row["expected"]:
            failures.append({"kind": "PROTECTED_INPUT_CHANGED", "path": str(path)})
    capture_summary = read_json(EVIDENCE / "capture_summary.json")
    for row in capture_summary["archives"]:
        path = Path(row["path"])
        current = path.stat()
        expected_ns = (int(row["mtime_ticks"]) - 621355968000000000) * 100
        if current.st_size != row["bytes"] or current.st_mtime_ns != expected_ns:
            failures.append({"kind": "ARCHIVE_METADATA_CHANGED", "path": str(path)})
    integrity = connection.execute("PRAGMA integrity_check").fetchall()
    if integrity != [("ok",)]:
        failures.append({"kind": "SQLITE_INTEGRITY", "result": integrity})
    connection.execute("INSERT INTO search_fts(search_fts,rank) VALUES('integrity-check',1)")
    event_count = connection.execute(
        "SELECT count(*) FROM events WHERE type='scnDialogLineEvent'"
    ).fetchone()[0]
    item_count = connection.execute(
        "SELECT count(*) FROM search_items WHERE kind='DIALOGUE_EVENT'"
    ).fetchone()[0]
    if event_count != item_count:
        failures.append({"kind": "DIALOGUE_SEARCH_ITEM_COVERAGE"})
    missing_english = connection.execute(
        "SELECT count(*) FROM search_items WHERE kind IN ('DIALOGUE_EVENT','CHOICE') AND text=''"
    ).fetchone()[0]
    text_domain_checks = verify_text_domains(connection, failures) if qualified else 0
    role_counts = [
        {"kind": kind, "speaker_role": speaker, "addressee_role": addressee, "count": count}
        for kind, speaker, addressee, count in connection.execute(
            """SELECT kind,speaker_role,addressee_role,count(*) FROM search_items
            WHERE kind IN ('DIALOGUE_EVENT','STORED_LINE','CHOICE')
            GROUP BY kind,speaker_role,addressee_role"""
        )
    ]
    issue_counts = dict(connection.execute("SELECT kind,count(*) FROM issues GROUP BY kind"))
    aux_missing = list(connection.execute(
        """SELECT DISTINCT a.resource_id,a.target_depot FROM aux_links a
        WHERE a.target_depot LIKE '%.scene' AND NOT EXISTS(
        SELECT 1 FROM resources r WHERE r.depot=a.target_depot OR r.depot_key=a.target_depot)"""
    ))
    result = {
        "status": "PASS" if not failures else "FAIL",
        "verified_utc": datetime.now(timezone.utc).isoformat(),
        "source_scenes_checked": checked_scenes,
        "source_and_export_files_hashed": len(checked_files),
        "protected_input_checks": len(prepared["checks"]),
        "scene_provider_inputs_accounted_for": len(indexed_scene_ids),
        "resource_statuses": statuses,
        "dialogue_search_items": item_count,
        "dialogue_or_choice_items_without_english": missing_english,
        "text_domain_items_checked": text_domain_checks,
        "role_counts": role_counts,
        "source_issue_counts": issue_counts,
        "conversation_scene_targets_missing_from_index": aux_missing,
        "failures": failures,
        "limits": [
            "Structural reachability ignores condition feasibility, timing and saved-owner execution.",
            "Johnny role matching uses exact actor aliases, the known voice tag and Character.Silverhand bindings.",
            "English text retains external provider candidates and embedded en_us variants. Gender masks and both lipsync-name fields are preserved.",
            "Source structural issues and opaque inputs remain explicit. The index does not authorize cuts.",
        ],
    }
    with (output / "verification.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    if failures:
        connection.close()
        raise SystemExit(f"Verification recorded {len(failures)} failures")
    connection.execute("UPDATE metadata SET value='VERIFIED' WHERE key='status'")
    connection.execute("INSERT INTO metadata VALUES('verified_utc',?)", (result["verified_utc"],))
    connection.commit()
    connection.close()
    final_database = output / "dialogue.sqlite3"
    database.rename(final_database)
    with (output / "database_manifest.json").open("x", encoding="utf-8") as stream:
        json.dump({"path": str(final_database), "sha256": sha256(final_database),
                   "bytes": final_database.stat().st_size}, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"status": "VERIFIED", "scenes_checked": checked_scenes,
                      "source_issues": issue_counts, "database": str(final_database)}))


if __name__ == "__main__":
    main()
