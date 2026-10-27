"""Version the three approved outside-whitelist side jobs; keep Motorbreath held."""

from pathlib import Path
import copy
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / "research/gig_restoration/lore_whitelists_v6_1_dependencies.json"
NEW = ROOT / "research/gig_restoration/lore_whitelists_v6_2_sidejobs.json"
POINTER = ROOT / "research/gig_restoration/lore_whitelist_current.json"

assert not NEW.exists(), "Use a successor whitelist version"
source = json.loads(OLD.read_text(encoding="utf-8"))
assert source["counts"]["ignore_two_year_gap"] == {"gigs": 80, "side_and_minor_jobs": 78, "total": 158}
assert source["audit_scope"]["decisions"] == {"INCLUDE": 158, "EXCLUDE": 51, "SEPARATE_SCOPE": 18}

approvals = {
    "mq006_rollercoaster": {
        "reason": "Jean's native repair-and-ride side job is independent of Johnny's personal story; his finale ride reactions are supporting commentary. The existing V-only repeatable coaster is a distinct earned follow-on, not the story job.",
        "requirements": "Preserve Jean/party introduction, repair, ride, original q110 and saved-history limits, once-only reward and repeatable-owner handoff. Hide Johnny's body and independent visual props while retaining permitted voice. Never acquire a second cart owner over an active ride or restart completed/unfinished MQ006.",
    },
    "mws_se5_07": {
        "reason": "Shape of a Pony has a shipped 141-node quest phase, journal and El Capitan messages, world encounter, and Porsche reward. Johnny speaks briefly in two scenes; he is not the job's premise.",
        "requirements": "Require native side-content and Porsche eligibility. Preserve prior ownership, completed journal, message branches and one-time vehicle entitlement. Hide Johnny's visible actor/effects while retaining permitted voice; no reward without the original quest route.",
    },
    "mws_wat_08_trauma_drama": {
        "reason": "Career Opportunities has a shipped 77-node quest phase, journal/manufacturer messages, Trauma Team scene and reward collection. Johnny has no spoken scene line in the inspected scene.",
        "requirements": "Require earned Trauma Drama arcade eligibility/high score, preserve existing reward and quest progress, keep original manufacturer messages and world encounter. Hide Johnny's visible actor/effects without altering the Trauma Team scene or granting an unearned reward.",
    },
}
rows = {row["id"]: row for row in source["decision_registry"]}
assert all(rows[k]["decision"] == "SEPARATE_SCOPE" for k in approvals)
for job_id, text in approvals.items():
    row = rows[job_id]
    row["decision"] = "INCLUDE"
    row["selection_final"] = True
    row["change"] = "ADDED_2026_10_26_SIDEJOB_REVIEW"
    row["strict_variant"] = False
    row["reason"] = text["reason"]
    row["requirements"] = text["requirements"]
    row["new_runtime_admission"] = False
    row["prior_evidence"] = "docs/whitelist_outside_review_20261026.md"
    row["evidence_limit"] = "TARGETED_NATIVE_REVIEW_RUNTIME_AND_LIVE_PENDING"

held = rows["mq057_motorbreath"]
assert held["decision"] == "EXCLUDE"
held["reason"] = "Selection hold: Johnny is not central in the inspected MQ057 native quest, but River's post-Tower state, original prerequisites, messages and reward route have not yet been reconciled."
held["requirements"] = "Do not admit Motorbreath or rewrite River state until a separate continuity and saved-owner audit closes. Its previous Error 404 election rationale was copied here in error. Preserve genuinely earned mq057_done for Where Eagles Dare."
held["prior_evidence"] = "docs/whitelist_outside_review_20261026.md"
held["evidence_limit"] = "NATIVE_12_PHASES_3_SCENES_SELECTION_HOLD"

names = source["ignore_two_year_gap"]["side_and_minor_jobs"]
for job_id in approvals:
    title = rows[job_id]["title"]
    assert title not in names
    names.append(title)
source["counts"]["ignore_two_year_gap"] = {"gigs": 80, "side_and_minor_jobs": 81, "total": 161}
source["audit_scope"]["decisions"] = {"INCLUDE": 161, "EXCLUDE": 51, "SEPARATE_SCOPE": 15}
source["revision"] = "6.2"
source["date"] = "2026-10-26"
source["status"] = "THREE_SIDEJOBS_SELECTED_IMPLEMENTATION_AND_LIVE_PENDING"
source["supersedes"] = "research/gig_restoration/lore_whitelists_v6_1_dependencies.json"
source["selection_basis"] += " On 26 October, Love Rollercoaster, Shape of a Pony and Career Opportunities were added after inspecting their original quest/scene resources. Motorbreath remains on hold."
source["audit_scope"]["remaining_work"] = "Implement and test the three added side jobs; separately audit held Motorbreath."
source["runtime_status"] = {"new_sidejobs_selected": 3, "new_sidejobs_installed": 0, "live_quest_tree_verified": False, "evidence": "docs/whitelist_outside_review_20261026.md"}

assert len(source["decision_registry"]) == 227
assert sum(row["decision"] == "INCLUDE" for row in source["decision_registry"]) == 161
assert sum(row["decision"] == "SEPARATE_SCOPE" for row in source["decision_registry"]) == 15
assert rows["mq057_motorbreath"]["decision"] == "EXCLUDE"
NEW.write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

pointer = json.loads(POINTER.read_text(encoding="utf-8"))
assert pointer["selection_file"] == OLD.relative_to(ROOT).as_posix()
pointer["selection_file"] = NEW.relative_to(ROOT).as_posix()
pointer["sha256"] = hashlib.sha256(NEW.read_bytes()).hexdigest().upper()
pointer["status"] = "THREE_NEW_SIDEJOBS_SELECTED_IMPLEMENTATION_PENDING_MOTORBREATH_HELD"
pointer["entry_coverage_s29"]["status"] = "PRIOR_158_ENTRIES_INSTALLED_THREE_NEW_SELECTIONS_PENDING"
pointer["selection_update_20261026"] = {
    "included_sidejobs": 81,
    "added_ids": list(approvals),
    "held_id": "mq057_motorbreath",
    "audit": "docs/whitelist_outside_review_20261026.md",
    "runtime_installed": False,
}
POINTER.write_text(json.dumps(pointer, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"selection": str(NEW), "sha256": pointer["sha256"], "sidejobs": 81, "held": "mq057_motorbreath"}))
