"""Search the verified dialogue index or inspect a result's graph context."""

import argparse
import gzip
import hashlib
import json
import sqlite3
from pathlib import Path


TASK = Path(__file__).resolve().parent
DEFAULT_DATABASE = TASK / "index_02/dialogue.sqlite3"
KIND_NAMES = {
    "dialogue": "DIALOGUE_EVENT",
    "choice": "CHOICE",
    "cue": "SCENE_CUE",
    "stored": "STORED_LINE",
    "conversation": "CONVERSATION_GROUP",
    "script": "SCRIPT_SPEECH_CANDIDATE",
}


def asset_context(connection, resource, item, event):
    path = Path(resource["json_path"])
    with path.open("rb") as stream:
        actual_hash = hashlib.file_digest(stream, "sha256").hexdigest().upper()
    if actual_hash != resource["json_sha256"]:
        raise SystemExit("Source export changed after indexing")
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8-sig") as stream:
        document = json.load(stream)
    subresource = connection.execute(
        "SELECT subresource FROM roots WHERE root_id=?", (item["root_id"],)
    ).fetchone()[0]
    if subresource == "root":
        root = document["Data"]["RootChunk"]
    else:
        ordinal = int(subresource.split("/", 2)[1])
        root = document["Data"]["EmbeddedFiles"][ordinal]["Content"]
    line = connection.execute(
        "SELECT speaker_id,addressee_id FROM lines WHERE root_id=? AND line_id=?",
        (item["root_id"], item["line_id"]),
    ).fetchone()
    actor_ids = {str(value) for value in (line or []) if value is not None}
    actor_ids.update(reference["actor_id"] for reference in event["actor_refs"])
    bindings = []
    for actor_id in actor_ids:
        row = connection.execute(
            "SELECT binding_json FROM actors WHERE root_id=? AND actor_id=?",
            (item["root_id"], actor_id),
        ).fetchone()
        if row:
            bindings.append(json.loads(row[0]))
    tables = root.get("resouresReferences", {})
    resolved = []
    pending = [event["payload"], *bindings]
    while pending:
        value = pending.pop()
        if isinstance(value, list):
            pending.extend(value)
        elif isinstance(value, dict):
            kind = value.get("$type", "")
            if kind.startswith("scn") and kind.endswith("SRRefId"):
                stem = kind[3:-7]
                table_name = stem[:1].lower() + stem[1:] + "s"
                table = tables.get(table_name)
                index = value.get("id")
                if isinstance(table, list) and isinstance(index, int) and 0 <= index < len(table):
                    resolved.append({"type": kind, "id": index, "table": table_name,
                                     "value": table[index]})
            pending.extend(value.values())
    return {"actor_bindings": bindings, "resolved_resource_table_entries": resolved}


def open_database(path):
    if not path.is_file():
        raise SystemExit(f"Verified database is missing {path}")
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    status = connection.execute("SELECT value FROM metadata WHERE key='status'").fetchone()
    if not status or status[0] != "VERIFIED":
        raise SystemExit("Use the database sealed by step 2 verification")
    return connection


def search(connection, arguments):
    joins = """LEFT JOIN resources r ON r.resource_id=s.resource_id
    LEFT JOIN nodes n ON n.root_id=s.root_id AND n.graph_path=s.graph_path AND n.node_id=s.node_id"""
    filters = []
    parameters = []
    if arguments.text:
        joins += " JOIN search_fts ON search_fts.rowid=s.item_id"
        filters.append("search_fts MATCH ?")
        parameters.append(arguments.text)
    if arguments.kind == "default":
        filters.append("s.kind IN ('DIALOGUE_EVENT','CHOICE')")
    elif arguments.kind != "all":
        filters.append("s.kind=?")
        parameters.append(KIND_NAMES[arguments.kind])
    for field in ("speaker", "addressee"):
        value = getattr(arguments, field)
        if not value:
            continue
        if value.lower() in ("johnny", "v"):
            filters.append(f"s.{field}_role=?")
            parameters.append(value.upper())
        else:
            filters.append(f"s.{field} LIKE ?")
            parameters.append("%" + value + "%")
    if arguments.actor:
        filters.append("s.actor_roles LIKE ?")
        parameters.append("%" + arguments.actor.upper() + "%")
    if arguments.scene:
        filters.append("s.depot LIKE ?")
        parameters.append("%" + arguments.scene + "%")
    if arguments.scope:
        filters.append("r.scope=?")
        parameters.append(arguments.scope)
    query = """
    SELECT s.item_key,s.kind,s.depot,s.graph_path,s.node_id,s.line_id,
           s.speaker,s.speaker_role,s.addressee,s.addressee_role,s.loc_id,s.text,s.text_source,
           r.scope,r.archive,r.raw_sha256,n.reachable AS structural_reachable,n.entry_names_json
    FROM search_items s """ + joins
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY s.depot,s.root_id,s.graph_path,s.node_id,s.item_id LIMIT ?"
    parameters.append(arguments.limit)
    results = [dict(row) for row in connection.execute(query, parameters)]
    for result in results:
        names = result.pop("entry_names_json")
        result["structural_entry_names"] = json.loads(names) if names else []
    return results


def context(connection, key, depth):
    item = connection.execute("SELECT * FROM search_items WHERE item_key=?", (key,)).fetchone()
    if item is None:
        raise SystemExit("Unknown result key")
    result = {"item": dict(item)}
    if item["root_id"]:
        root = connection.execute(
            "SELECT subresource,type,context_json FROM roots WHERE root_id=?",
            (item["root_id"],),
        ).fetchone()
        result["root_context"] = {
            "subresource": root["subresource"], "type": root["type"],
            "metadata": json.loads(root["context_json"]),
        }
    if item["resource_id"]:
        resource = connection.execute(
            "SELECT * FROM resources WHERE resource_id=?", (item["resource_id"],)
        ).fetchone()
        result["resource"] = dict(resource)
        result["source_referrers"] = [
            dict(row) for row in connection.execute(
                """SELECT DISTINCT * FROM source_references WHERE target_depot=?
                ORDER BY source_depot,source_archive,evidence""",
                (resource["depot"],),
            )
        ]
        result["source_referrer_limit"] = "Resource references identify investigation leads. They do not establish a connected invocation or executing owner."
    if item["kind"] == "SCRIPT_SPEECH_CANDIDATE":
        result["script_call"] = dict(connection.execute(
            "SELECT * FROM script_calls WHERE path || ':' || line_number=?",
            (key,),
        ).fetchone())
    if item["kind"] in ("DIALOGUE_EVENT", "SCENE_CUE"):
        event = dict(connection.execute("SELECT * FROM events WHERE event_key=?", (key,)).fetchone())
        event["actor_refs"] = json.loads(event.pop("actor_refs_json"))
        event["payload"] = json.loads(event.pop("payload_json"))
        result["event"] = event
        result["asset_context"] = asset_context(connection, result["resource"], item, event)
    if item["loc_id"]:
        result["localization_candidates"] = [
            dict(row) for row in connection.execute(
                """SELECT * FROM localization WHERE loc_id=?
                AND (root_id=? OR root_id IS NULL)""",
                (item["loc_id"], item["root_id"]),
            )
        ]
        for candidate in result["localization_candidates"]:
            candidate["is_debug_draft"] = candidate["locale"] == "db_db"
    if not item["node_id"]:
        return result
    root_id = item["root_id"]
    graph_path = item["graph_path"]
    selected = {item["node_id"]}
    for _ in range(depth):
        for node_id in list(selected):
            for row in connection.execute(
                """SELECT source_node,destination_node FROM edges
                WHERE root_id=? AND graph_path=? AND (source_node=? OR destination_node=?)""",
                (root_id, graph_path, node_id, node_id),
            ):
                selected.update(row)
    result["nodes"] = []
    result["edges"] = []
    for node_id in sorted(selected):
        node = connection.execute(
            "SELECT * FROM nodes WHERE root_id=? AND graph_path=? AND node_id=?",
            (root_id, graph_path, node_id),
        ).fetchone()
        if node:
            value = dict(node)
            for field in list(value):
                if field.endswith("_json"):
                    value[field[:-5]] = json.loads(value.pop(field))
            value["dialogue"] = [
                dict(row) for row in connection.execute(
                    """SELECT item_key,speaker,addressee,text,line_id FROM search_items
                    WHERE root_id=? AND graph_path=? AND node_id=? AND kind='DIALOGUE_EVENT'""",
                    (root_id, graph_path, node_id),
                )
            ]
            value["choices"] = [
                dict(row) for row in connection.execute(
                    """SELECT c.choice_key,c.option_ordinal,c.option_id,c.loc_id,c.output_stamp,
                    c.conditions_json,s.text FROM choices c LEFT JOIN search_items s ON s.item_key=c.choice_key
                    WHERE c.root_id=? AND c.graph_path=? AND c.node_id=?""",
                    (root_id, graph_path, node_id),
                )
            ]
            value["cues"] = [
                dict(row) for row in connection.execute(
                    """SELECT event_key,type,start_time,duration,actor_refs_json FROM events
                    WHERE root_id=? AND graph_path=? AND node_id=? AND type!='scnDialogLineEvent'""",
                    (root_id, graph_path, node_id),
                )
            ]
            result["nodes"].append(value)
        result["edges"].extend(
            dict(row) for row in connection.execute(
                "SELECT * FROM edges WHERE root_id=? AND graph_path=? AND source_node=?",
                (root_id, graph_path, node_id),
            )
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--text", help="SQLite FTS5 query")
    parser.add_argument("--speaker")
    parser.add_argument("--addressee")
    parser.add_argument("--actor", help="Actor role in a dialogue or presentation cue")
    parser.add_argument("--scene", help="Depot path substring")
    parser.add_argument("--scope", choices=(
        "CURRENT_PTFR_PAYLOAD", "REFERENCE_CENSUS", "GLOBAL_CENSUS_UNCLASSIFIED",
    ))
    parser.add_argument("--kind", default="default",
                        choices=["default", "all", *KIND_NAMES])
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--context", help="Exact item_key returned by a search")
    parser.add_argument("--depth", type=int, default=1, choices=range(0, 6))
    arguments = parser.parse_args()
    if not 1 <= arguments.limit <= 1000:
        parser.error("--limit must be between 1 and 1000")
    connection = open_database(arguments.database)
    try:
        result = (
            context(connection, arguments.context, arguments.depth)
            if arguments.context else search(connection, arguments)
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except sqlite3.OperationalError as error:
        parser.error(str(error))
    finally:
        connection.close()


if __name__ == "__main__":
    main()
