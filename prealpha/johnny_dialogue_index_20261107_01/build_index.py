"""Build a searchable, source-pinned dialogue and scene-context database."""

import argparse
import gzip
import hashlib
import json
import sqlite3
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path


TASK = Path(__file__).resolve().parent
WORKSPACE = TASK.parents[1]
EVIDENCE = TASK / "evidence_01"
sys.path.insert(0, str(WORKSPACE / "tools/parity_audit"))
from model import Resource


def read_json(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8-sig") as stream:
        return json.load(stream)


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def scalar(value):
    if isinstance(value, dict):
        for key in ("$value", "ruid", "val", "id", "value", "mask"):
            if key in value:
                return scalar(value[key])
    return value


def identifier(value):
    result = scalar(value)
    return str(result) if result is not None else None


def walk(value, path=""):
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from walk(child, path + "/" + key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, path + "/" + str(index))


SCHEMA = """
CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE resources(
 resource_id TEXT PRIMARY KEY, kind TEXT, depot TEXT, depot_key TEXT, archive TEXT,
 provider_role TEXT, scope TEXT, raw_sha256 TEXT, raw_path TEXT,
 json_path TEXT, json_sha256 TEXT, status TEXT, root_type TEXT, error TEXT);
CREATE TABLE roots(
 root_id TEXT PRIMARY KEY, resource_id TEXT, subresource TEXT, type TEXT, context_json TEXT);
CREATE TABLE actors(
 root_id TEXT, actor_id TEXT, name TEXT, is_player INTEGER, role TEXT,
 voice_tag TEXT, record_ids_json TEXT, evidence_json TEXT, binding_json TEXT,
 PRIMARY KEY(root_id,actor_id));
CREATE TABLE lines(
 root_id TEXT, line_id TEXT, speaker_id TEXT, addressee_id TEXT, loc_id TEXT,
 gender_mask TEXT, male_lipsync TEXT, female_lipsync TEXT, usage_json TEXT,
 PRIMARY KEY(root_id,line_id));
CREATE TABLE nodes(
 root_id TEXT, graph_path TEXT, node_id TEXT, type TEXT,
 reachable INTEGER, entry_names_json TEXT, conditions_json TEXT,
 reads_json TEXT, writes_json TEXT, payload_json TEXT,
 PRIMARY KEY(root_id,graph_path,node_id));
CREATE TABLE edges(
 root_id TEXT, graph_path TEXT, edge_ordinal INTEGER,
 source_node TEXT, output_stamp TEXT, destination_node TEXT, input_stamp TEXT);
CREATE TABLE entries(root_id TEXT, graph_path TEXT, name TEXT, node_id TEXT);
CREATE TABLE events(
 event_key TEXT PRIMARY KEY, root_id TEXT, graph_path TEXT, node_id TEXT,
 event_ordinal INTEGER, event_id TEXT, type TEXT, line_id TEXT,
 start_time TEXT, duration TEXT, actor_refs_json TEXT, payload_json TEXT);
CREATE TABLE choices(
 choice_key TEXT PRIMARY KEY, root_id TEXT, graph_path TEXT, node_id TEXT,
 option_ordinal INTEGER, option_id TEXT, loc_id TEXT, caption TEXT,
 gender_mask TEXT, output_stamp TEXT, conditions_json TEXT, payload_json TEXT);
CREATE TABLE localization(
 text_id INTEGER PRIMARY KEY, provider_resource_id TEXT, root_id TEXT,
 loc_id TEXT, locale TEXT, gender TEXT, signature TEXT, text TEXT, source_path TEXT);
CREATE INDEX localization_lookup ON localization(locale,loc_id,root_id);
CREATE TABLE aux_links(
 resource_id TEXT, source_path TEXT, target_depot TEXT, conditions_json TEXT, payload_json TEXT);
CREATE TABLE script_calls(
 call_id INTEGER PRIMARY KEY, path TEXT, source_sha256 TEXT, line_number INTEGER, text TEXT);
CREATE TABLE source_references(
 source_depot TEXT, source_archive TEXT, source_sha256 TEXT,
 target_depot TEXT, evidence TEXT, raw_path TEXT);
CREATE INDEX source_references_target ON source_references(target_depot);
CREATE TABLE issues(
 issue_id INTEGER PRIMARY KEY, resource_id TEXT, root_id TEXT, kind TEXT, details_json TEXT);
CREATE TABLE search_items(
 item_id INTEGER PRIMARY KEY, kind TEXT, item_key TEXT, resource_id TEXT, root_id TEXT,
 graph_path TEXT, node_id TEXT, line_id TEXT, loc_id TEXT,
 speaker TEXT, speaker_role TEXT, addressee TEXT, addressee_role TEXT,
 text TEXT, depot TEXT, actor_roles TEXT);
CREATE INDEX search_role ON search_items(speaker_role,addressee_role,kind);
CREATE INDEX search_key ON search_items(item_key);
"""


class Indexer:
    def __init__(self, connection):
        self.db = connection
        self.counts = Counter()
        self.english = {}

    def issue(self, source_id, root_id, kind, details):
        self.db.execute(
            "INSERT INTO issues(resource_id,root_id,kind,details_json) VALUES(?,?,?,?)",
            (source_id, root_id, kind, encode(details)),
        )

    def texts(self, loc_id, embedded):
        external = self.english.get(loc_id, [])
        local = embedded.get(loc_id, [])
        return "\n".join(dict.fromkeys(text for text in external + local if text))

    def search_item(self, values):
        self.db.execute(
            """INSERT INTO search_items(
            kind,item_key,resource_id,root_id,graph_path,node_id,line_id,loc_id,
            speaker,speaker_role,addressee,addressee_role,text,depot,actor_roles)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            values,
        )

    def subtitle_resource(self, row, document):
        for path, value in walk(document):
            if "stringId" not in value or "femaleVariant" not in value:
                continue
            loc_id = identifier(value["stringId"])
            for gender, field in (("female", "femaleVariant"), ("male", "maleVariant")):
                content = value.get(field, "")
                self.db.execute(
                    """INSERT INTO localization(
                    provider_resource_id,root_id,loc_id,locale,gender,signature,text,source_path)
                    VALUES(?,NULL,?,'en_us',?,NULL,?,?)""",
                    (row["resource_id"], loc_id, gender, content, path + "/" + field),
                )
                self.counts["external_subtitle_variants"] += 1

    def actor(self, actor):
        name = str(scalar(actor.get("actorName", actor.get("playerName", ""))) or "")
        player = actor.get("$type") == "scnPlayerActorDef"
        voice = identifier(actor.get("voicetagId"))
        records = sorted({
            str(scalar(value)) for _, value in walk(actor)
            if value.get("$type") == "TweakDBID" and scalar(value) not in ("0", 0, None)
        })
        evidence = []
        if voice == "1103967280742240508":
            evidence.append("KNOWN_JOHNNY_VOICE_TAG")
        if "Character.Silverhand" in records:
            evidence.append("CHARACTER_SILVERHAND_BINDING")
        normalized = "".join(character.lower() for character in name if character.isalnum())
        if normalized in {"johnny", "silverhand", "johnnysilverhand"}:
            evidence.append("EXACT_ACTOR_ALIAS")
        if evidence:
            role = "JOHNNY"
            if player:
                evidence.append("PLAYER_ACTOR_JOHNNY_CONTEXT_REQUIRES_REVIEW")
        elif player:
            role = "V"
            evidence.append("PLAYER_ACTOR_DEFINITION")
        else:
            role = "OTHER"
            if "johnny" in normalized or "silverhand" in normalized:
                evidence.append("NAME_HINT_REQUIRES_REVIEW")
        return {
            "name": name, "role": role, "is_player": player, "voice": voice,
            "records": records, "evidence": evidence,
        }

    def embedded_text(self, source_id, root_id, root):
        store = root.get("locStore", {})
        payloads = store.get("vpEntries", [])
        english = defaultdict(list)
        for ordinal, descriptor in enumerate(store.get("vdEntries", [])):
            index = descriptor.get("vpeIndex")
            if not isinstance(index, int) or not 0 <= index < len(payloads):
                self.issue(source_id, root_id, "LOCALIZATION_PAYLOAD_INDEX", descriptor)
                continue
            payload = payloads[index]
            if payload.get("variantId") != descriptor.get("variantId"):
                self.issue(source_id, root_id, "LOCALIZATION_VARIANT_ID", descriptor)
            loc_id = identifier(descriptor.get("locstringId"))
            locale = str(descriptor.get("localeId", ""))
            content = payload.get("content", "")
            self.db.execute(
                """INSERT INTO localization(
                provider_resource_id,root_id,loc_id,locale,gender,signature,text,source_path)
                VALUES(?,?,?,?,NULL,?,?,?)""",
                (source_id, root_id, loc_id, locale,
                 identifier(descriptor.get("signature")), content,
                 f"locStore/vdEntries/{ordinal}"),
            )
            if locale == "en_us":
                english[loc_id].append(content)
            self.counts["embedded_localization_variants"] += 1
        return english

    def entry_membership(self, graph):
        adjacency = defaultdict(list)
        for source, output, destination, input_stamp in graph["edges"]:
            if output != "CutSource" and input_stamp != "CutDestination":
                adjacency[source].append(destination)
        membership = defaultdict(list)
        for name, seed in graph["entries"].items():
            seen = {seed}
            queue = deque([seed])
            while queue:
                node = queue.popleft()
                membership[node].append(name)
                for destination in adjacency[node]:
                    if destination not in seen:
                        seen.add(destination)
                        queue.append(destination)
        return membership

    def actor_refs(self, event, actors):
        references = []
        for path, value in walk(event):
            kind = value.get("$type")
            if kind == "scnActorId":
                actor_id = identifier(value)
                if actor_id == "4294967295":
                    continue
            elif kind == "scnPerformerId":
                raw_id = scalar(value)
                if not str(raw_id).isdigit() or int(raw_id) & 255 != 1:
                    continue
                actor_id = str(int(raw_id) >> 8)
            else:
                continue
            actor = actors.get(actor_id)
            references.append({
                "path": path, "actor_id": actor_id,
                "name": actor["name"] if actor else None,
                "role": actor["role"] if actor else "UNRESOLVED",
            })
        return references

    def cue_text(self, event):
        tokens = [event.get("$type", "")]
        for _, value in walk(event):
            text = value.get("$value")
            if isinstance(text, str) and text not in ("", "None") and not text.isdigit():
                tokens.append(text)
        return " ".join(dict.fromkeys(tokens))

    def scene(self, row, document):
        roots = [("root", document["Data"]["RootChunk"])]
        for ordinal, embedded in enumerate(document["Data"].get("EmbeddedFiles", [])):
            content = embedded.get("Content", {})
            if "sceneGraph" in content or "screenplayStore" in content:
                roots.append((f"embedded/{ordinal}/{scalar(embedded.get('FileName'))}", content))
        for subresource, root in roots:
            self.scene_root(row, document, subresource, root)

    def scene_root(self, row, document, subresource, root):
        source_id = row["resource_id"]
        root_id = source_id + "/" + subresource
        normalizer = Resource(document)
        normalizer.root = root
        normalizer.obj = {"Data": {"RootChunk": root, "EmbeddedFiles": []}}
        model = normalizer.normalize()
        context = {
            key: normalizer.clean(root[key]) for key in (
                "sceneCategoryTag", "interruptionScenarios", "voInfo", "props",
                "referencePoints", "exitPoints", "executionTags", "executionTagEntries",
            ) if key in root
        }
        self.db.execute(
            "INSERT INTO roots VALUES(?,?,?,?,?)",
            (root_id, source_id, subresource, root.get("$type"), encode(context)),
        )
        for error in model["errors"]:
            self.issue(source_id, root_id, "SOURCE_STRUCTURE_" + error["kind"], error)
        actors = {}
        definitions = root.get("actors", []) + root.get("playerActors", [])
        for definition in definitions:
            actor_id = identifier(definition.get("actorId"))
            if actor_id in actors:
                self.issue(source_id, root_id, "DUPLICATE_ACTOR_ID", {"actor_id": actor_id})
                continue
            actor = self.actor(definition)
            actors[actor_id] = actor
            self.db.execute(
                "INSERT INTO actors VALUES(?,?,?,?,?,?,?,?,?)",
                (root_id, actor_id, actor["name"], int(actor["is_player"]), actor["role"],
                 actor["voice"], encode(actor["records"]), encode(actor["evidence"]),
                 encode(definition)),
            )
            self.counts["actors"] += 1
        embedded_text = self.embedded_text(source_id, root_id, root)
        player_roles = {actor["role"] for actor in actors.values() if actor["is_player"]}
        choice_role = next(iter(player_roles)) if len(player_roles) == 1 else "PLAYER_CONTEXT_UNRESOLVED"
        choice_speaker = "V" if choice_role == "V" else "Player"
        lines = {}
        for line in root.get("screenplayStore", {}).get("lines", []):
            line_id = identifier(line.get("itemId"))
            if line_id in lines:
                self.issue(source_id, root_id, "DUPLICATE_LINE_ID", {"line_id": line_id})
                continue
            lines[line_id] = line
            speaker_id = identifier(line.get("speaker"))
            addressee_id = identifier(line.get("addressee"))
            for field, actor_id in (("speaker", speaker_id), ("addressee", addressee_id)):
                if actor_id not in actors and actor_id not in (None, "4294967295"):
                    self.issue(source_id, root_id, "UNRESOLVED_LINE_ACTOR",
                               {"line_id": line_id, "field": field, "actor_id": actor_id})
            self.db.execute(
                "INSERT INTO lines VALUES(?,?,?,?,?,?,?,?,?)",
                (root_id, line_id, speaker_id, addressee_id,
                 identifier(line.get("locstringId")),
                 identifier(line.get("usage", {}).get("playerGenderMask")),
                 identifier(line.get("maleLipsyncAnimationName")),
                 identifier(line.get("femaleLipsyncAnimationName")),
                 encode(line.get("usage", {}))),
            )
            self.counts["stored_lines"] += 1
        options = {
            identifier(option.get("itemId")): option
            for option in root.get("screenplayStore", {}).get("options", [])
        }
        used_lines = set()
        for graph_path, graph in model["graphs"].items():
            membership = self.entry_membership(graph)
            for name, node_id in graph["entries"].items():
                self.db.execute("INSERT INTO entries VALUES(?,?,?,?)",
                                (root_id, graph_path, name, node_id))
            for ordinal, edge in enumerate(graph["edges"]):
                self.db.execute("INSERT INTO edges VALUES(?,?,?,?,?,?,?)",
                                (root_id, graph_path, ordinal, *edge))
                self.counts["edges"] += 1
            for node_id, node in graph["nodes"].items():
                payload = node["payload"]
                node_payload = {key: value for key, value in payload.items()
                                if key not in ("events", "outputSockets")}
                self.db.execute(
                    "INSERT INTO nodes VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (root_id, graph_path, node_id, node["type"],
                     int(node_id in graph["reachable"]), encode(membership.get(node_id, [])),
                     encode(node["conditions"]), encode(node["reads"]),
                     encode(node["writes"]), encode(node_payload)),
                )
                self.counts["nodes"] += 1
                for ordinal, event in enumerate(payload.get("events") or []):
                    key = f"{root_id}/{graph_path}/{node_id}/event/{ordinal}"
                    line_id = identifier(event.get("screenplayLineId"))
                    references = self.actor_refs(event, actors)
                    self.db.execute(
                        "INSERT INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                        (key, root_id, graph_path, node_id, ordinal,
                         identifier(event.get("id")), event.get("$type"), line_id,
                         identifier(event.get("startTime")), identifier(event.get("duration")),
                         encode(references), encode(event)),
                    )
                    self.counts["events"] += 1
                    if event.get("$type") == "scnDialogLineEvent":
                        if line_id not in lines:
                            self.issue(source_id, root_id, "EVENT_LINE_REFERENCE",
                                       {"event_key": key, "line_id": line_id})
                        used_lines.add(line_id)
                        self.line_item(row, root_id, graph_path, node_id, key,
                                       "DIALOGUE_EVENT", line_id, lines.get(line_id, {}),
                                       actors, embedded_text)
                        self.counts["dialogue_events"] += 1
                    else:
                        roles = sorted({reference["role"] for reference in references})
                        self.search_item((
                            "SCENE_CUE", key, source_id, root_id, graph_path, node_id,
                            None, None, "", "", "", "", self.cue_text(event), row["depot"],
                            " ".join(roles),
                        ))
                choice_options = payload.get("options") if node["type"] == "scnChoiceNode" else []
                for ordinal, choice in enumerate(choice_options or []):
                    option_id = identifier(choice.get("screenplayOptionId"))
                    option = options.get(option_id)
                    if option is None:
                        self.issue(source_id, root_id, "CHOICE_OPTION_REFERENCE",
                                   {"node_id": node_id, "option_id": option_id})
                        option = {}
                    loc_id = identifier(option.get("locstringId"))
                    key = f"{root_id}/{graph_path}/{node_id}/choice/{ordinal}"
                    # Native scene choices use output stamp name 0 and option ordinal.
                    output_stamp = f"0:{ordinal}"
                    self.db.execute(
                        "INSERT INTO choices VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                        (key, root_id, graph_path, node_id, ordinal, option_id, loc_id,
                         identifier(choice.get("caption")),
                         identifier(option.get("usage", {}).get("playerGenderMask")),
                         output_stamp, encode({key: value for key, value in choice.items()
                                               if "Condition" in key or "condition" in key}),
                         encode(choice)),
                    )
                    destinations = [edge for edge in graph["edges"]
                                    if edge[0] == node_id and edge[1] == output_stamp]
                    if not destinations:
                        self.issue(source_id, root_id, "CHOICE_NO_CONNECTED_DESTINATION",
                                   {"node_id": node_id, "ordinal": ordinal,
                                    "output_stamp": output_stamp})
                    self.search_item((
                        "CHOICE", key, source_id, root_id, graph_path, node_id,
                        option_id, loc_id, choice_speaker, choice_role, "", "",
                        self.texts(loc_id, embedded_text), row["depot"], choice_role,
                    ))
                    self.counts["choice_options"] += 1
        for line_id in lines.keys() - used_lines:
            self.line_item(row, root_id, "", "", f"{root_id}/stored/{line_id}",
                           "STORED_LINE", line_id, lines[line_id], actors, embedded_text)

    def line_item(self, row, root_id, graph_path, node_id, key, kind,
                  line_id, line, actors, embedded_text):
        speaker = actors.get(identifier(line.get("speaker")), {})
        addressee = actors.get(identifier(line.get("addressee")), {})
        loc_id = identifier(line.get("locstringId"))
        text = self.texts(loc_id, embedded_text)
        self.search_item((
            kind, key, row["resource_id"], root_id, graph_path, node_id, line_id, loc_id,
            speaker.get("name", ""), speaker.get("role", "UNRESOLVED"),
            addressee.get("name", ""), addressee.get("role", "UNRESOLVED"),
            text, row["depot"], " ".join(sorted({speaker.get("role", ""), addressee.get("role", "")})),
        ))

    def conversations(self, row, document):
        root = document["Data"]["RootChunk"]
        normalizer = Resource(document)
        for ordinal, handle in enumerate(root.get("conversationGroups", [])):
            group = normalizer.clean(handle)
            if not isinstance(group, dict):
                self.issue(row["resource_id"], None, "CONVERSATION_GROUP_UNRESOLVED",
                           {"ordinal": ordinal})
                continue
            for path, value in walk(group):
                if "DepotPath" not in value:
                    continue
                target = identifier(value["DepotPath"])
                self.db.execute(
                    "INSERT INTO aux_links VALUES(?,?,?,?,?)",
                    (row["resource_id"], f"conversationGroups/{ordinal}" + path, target,
                     encode(group.get("condition")), encode(group)),
                )
            self.search_item((
                "CONVERSATION_GROUP", f"{row['resource_id']}/group/{ordinal}",
                row["resource_id"], None, None, None, None, None, "", "", "", "",
                encode(group), row["depot"], "",
            ))
            self.counts["conversation_groups"] += 1
        self.counts["conversation_resources"] += 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="index_01")
    arguments = parser.parse_args()
    output = (TASK / arguments.output).resolve()
    if output.parent != TASK or not output.name.startswith("index_"):
        parser.error("Use a task-local index_ successor directory")
    if output.exists():
        raise SystemExit("Use a fresh database output")
    output.mkdir()
    database = output / "dialogue.partial.sqlite3"
    capture_summary = read_json(EVIDENCE / "capture_summary.json")
    manifest_path = EVIDENCE / "exports.jsonl"
    if sha256(manifest_path) != capture_summary["manifest_sha256"]:
        raise SystemExit("Export manifest hash mismatch")
    if capture_summary["changed_archives"]:
        raise SystemExit("Archives changed during capture")
    rows = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines()]
    prepared = read_json(EVIDENCE / "prepared.json")
    connection = sqlite3.connect(database)
    connection.executescript(SCHEMA)
    connection.execute("PRAGMA temp_store=MEMORY")
    connection.execute("PRAGMA cache_size=-65536")
    indexer = Indexer(connection)
    connection.execute("INSERT INTO metadata VALUES('status','BUILDING')")
    connection.execute("INSERT INTO metadata VALUES('scope',?)",
                       ("Full scene census, auxiliary conversations and English subtitle providers. Post-Tower execution requires review.",))
    connection.execute("INSERT INTO metadata VALUES('indexer_sha256',?)", (sha256(Path(__file__)),))
    connection.execute("INSERT INTO metadata VALUES('model_sha256',?)",
                       (sha256(WORKSPACE / "tools/parity_audit/model.py"),))
    connection.execute("INSERT INTO metadata VALUES('capture_manifest_sha256',?)",
                       (sha256(manifest_path),))
    source_hashes = {row["path"]: row["sha256"] for row in prepared["speech_source_files"]}
    previous_root = Path(prepared["step1_summary"]).parent
    previous_summary = read_json(Path(prepared["step1_summary"]))
    for filename, expected_hash in (
        ("capture.json", previous_summary["bulk_capture_sha256"]),
        ("capture_additions.json", previous_summary["supplemental_capture_sha256"]),
    ):
        previous_path = previous_root / filename
        if sha256(previous_path) != expected_hash:
            raise SystemExit("Step 1 source-reference snapshot changed")
        previous = read_json(previous_path)
        for source in previous["resources"]:
            for field, evidence in (
                ("imports", "SERIALIZED_IMPORT"),
                ("binary_graph_reference_candidates", "BINARY_REFERENCE_CANDIDATE"),
            ):
                for target in source[field]:
                    if target.endswith(".scene"):
                        connection.execute(
                            "INSERT INTO source_references VALUES(?,?,?,?,?,?)",
                            (source["depot"], source["archive"], source["sha256"],
                             target, evidence, source["raw"]),
                        )
    for call in prepared["speech_api_candidates"]:
        connection.execute(
            "INSERT INTO script_calls(path,source_sha256,line_number,text) VALUES(?,?,?,?)",
            (call["path"], source_hashes[call["path"]], call["line"], call["text"]),
        )
        indexer.search_item((
            "SCRIPT_SPEECH_CANDIDATE", call["path"] + ":" + str(call["line"]),
            None, None, None, None, None, None, "", "", "", "",
            call["text"], call["path"], "",
        ))
    ordered = sorted(rows, key=lambda row: (row["kind"] != "ENGLISH_SUBTITLES", row["resource_id"]))
    english_ready = False
    for number, row in enumerate(ordered, 1):
        if row["kind"] != "ENGLISH_SUBTITLES" and not english_ready:
            for loc_id, content in connection.execute(
                "SELECT loc_id,text FROM localization WHERE root_id IS NULL AND locale='en_us'"
            ):
                if content and content not in indexer.english.setdefault(loc_id, []):
                    indexer.english[loc_id].append(content)
            english_ready = True
        source_id = row["resource_id"]
        connection.execute(
            "INSERT INTO resources VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (source_id, row["kind"], row["depot"], row["key"], row["archive"],
             row["provider_role"], row["scope"], row["sha256"], row["raw"],
             row["json"], row["json_sha256"], row["status"], row["root_type"], row["error"]),
        )
        if row["status"] == "OPAQUE":
            indexer.issue(source_id, None, "DECODE_OPAQUE", {"error": row["error"]})
            continue
        connection.execute("SAVEPOINT resource_index")
        try:
            if sha256(row["json"]) != row["json_sha256"]:
                raise ValueError("Export JSON hash changed")
            document = read_json(row["json"])
            for _, value in walk(document):
                target = identifier(value.get("DepotPath")) if "DepotPath" in value else None
                if target and target.endswith(".scene"):
                    connection.execute(
                        "INSERT INTO source_references VALUES(?,?,?,?,?,?)",
                        (row["depot"], row["archive"], row["sha256"], target,
                         "EXPORTED_RESOURCE_REFERENCE", row["raw"]),
                    )
            if row["kind"] == "ENGLISH_SUBTITLES":
                indexer.subtitle_resource(row, document)
            elif row["kind"] == "CONVERSATIONS":
                indexer.conversations(row, document)
            else:
                indexer.scene(row, document)
            connection.execute("RELEASE resource_index")
            connection.execute("UPDATE resources SET status='INDEXED' WHERE resource_id=?", (source_id,))
        except (ValueError, KeyError, TypeError, RecursionError, sqlite3.IntegrityError) as error:
            connection.execute("ROLLBACK TO resource_index")
            connection.execute("RELEASE resource_index")
            connection.execute("UPDATE resources SET status='INDEX_ERROR',error=? WHERE resource_id=?",
                               (str(error), source_id))
            indexer.issue(source_id, None, "INDEX_ERROR", {"error": str(error)})
        if number % 100 == 0:
            connection.commit()
            print(encode({"processed": number, "total": len(ordered),
                          "dialogue_events": indexer.counts["dialogue_events"]}), flush=True)
    connection.executescript("""
    CREATE INDEX nodes_lookup ON nodes(root_id,graph_path,node_id);
    CREATE INDEX events_lookup ON events(root_id,line_id);
    CREATE INDEX choices_lookup ON choices(root_id,node_id);
    CREATE INDEX edges_source ON edges(root_id,graph_path,source_node);
    CREATE INDEX edges_destination ON edges(root_id,graph_path,destination_node);
    CREATE VIRTUAL TABLE search_fts USING fts5(
      text,depot,speaker,addressee,actor_roles,content='search_items',content_rowid='item_id');
    INSERT INTO search_fts(search_fts) VALUES('rebuild');
    """)
    connection.execute("UPDATE metadata SET value='INDEXED_PENDING_VERIFICATION' WHERE key='status'")
    connection.commit()
    actual_counts = {
        table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        for table in ("resources", "roots", "actors", "lines", "nodes", "edges", "events",
                      "choices", "localization", "search_items", "aux_links", "script_calls",
                      "source_references", "issues")
    }
    statuses = dict(connection.execute("SELECT status,count(*) FROM resources GROUP BY status"))
    connection.close()
    with (output / "index_build.json").open("x", encoding="utf-8") as stream:
        json.dump({"counts": actual_counts, "resource_statuses": statuses,
                   "database": str(database), "database_sha256": sha256(database)},
                  stream, indent=2)
        stream.write("\n")
    print(encode({"status": "INDEX_BUILT_PENDING_VERIFICATION", "counts": actual_counts,
                  "resource_statuses": statuses}))


if __name__ == "__main__":
    main()
