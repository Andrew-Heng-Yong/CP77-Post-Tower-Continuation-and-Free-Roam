"""Validate the full graph readbacks and the fresh-route alternatives."""

from copy import deepcopy
from pathlib import Path
import json

from prepare_scripts import HERE, STAGE, digest, pin, require, write_json


def branches(condition):
    return ([child["Data"] for child in condition["conditions"]]
            if condition["$type"] == "questLogicalCondition" and condition["operation"] == "OR" else [condition])


def revise(node, permit):
    if node["$type"] == "questLogicalCondition":
        return sum(revise(child["Data"], permit) for child in node["conditions"])
    if node["$type"] == "questFactsDBCondition":
        leaf = node["type"]["Data"]
        if leaf.get("factName") == permit:
            require(leaf["comparisonType"] == "Equal" and leaf["value"] == 1, f"Wrong gate for {permit}")
            leaf["value"] = 2
            return 1
    return 0


def required(node, permit):
    if node["$type"] == "questLogicalCondition":
        combine = {"AND": any, "OR": all}[node["operation"]]
        return combine(required(child["Data"], permit) for child in node["conditions"])
    if node["$type"] != "questFactsDBCondition":
        return False
    leaf = node["type"]["Data"]
    return leaf.get("factName") == permit and leaf["comparisonType"] == "Equal" and leaf["value"] == 2


def main():
    specs = json.loads((HERE / "entry_gates.json").read_bytes())
    records = json.loads((STAGE / "gates.json").read_bytes())
    require({row["depot"] for row in records} == {spec["depot"] for spec in specs}, "Graph inventory drift")
    checks = []
    for record in records:
        original = json.loads(Path(record["before"]).read_bytes())["Data"]
        expected = deepcopy(original)
        nodes = {r["Data"]["id"]: r["Data"] for r in expected["RootChunk"]["graph"]["Data"]["nodes"]}
        count = 0
        for spec in (spec for spec in specs if spec["depot"] == record["depot"]):
            for node in spec["nodes"]:
                current = branches(nodes[node]["condition"]["Data"])
                permit = spec["permit"]
                frozen = []
                for index, subtree in enumerate(current):
                    edited = revise(subtree, permit) if spec["branches"] == "all" or index in spec["branches"] else 0
                    count += edited
                    if edited:
                        require(required(subtree, permit), f"An OR path bypasses the retired gate on {node}")
                        frozen.append(index)
                require(frozen and len(current) - len(frozen) == spec["fresh_branches"],
                        f"Fresh alternatives differ at {record['depot']}:{node}")
                checks.append(dict(depot=record["depot"], node=node, frozen_branches=frozen,
                                   fresh_branches=spec["fresh_branches"], blocked_at_permits=[0, 1]))
        actual = json.loads(Path(record["after"]).read_bytes())["Data"]
        require(expected == actual, f"Unplanned graph or resource edit: {record['depot']}")
        require(count == record["comparisons"], f"Comparison count drift: {record['depot']}")
        pin(Path(record["path"]), record["sha256"])
    proof = STAGE / "gate_checks.json"
    write_json(proof, dict(status="PASS", resources=len(records), gates=checks,
                          gates_sha256=digest(STAGE / "gates.json")))
    print(f"Verified {len(checks)} gates. All other serialized graph data matches, including issued-owner paths.")


if __name__ == "__main__":
    main()
