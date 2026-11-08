"""Attach evidence and a next action to every inventory boundary."""

import json
from collections import defaultdict, Counter
from pathlib import Path

from prepare import TASK, STEP1, read, write

OUT = TASK / 'evidence_09'


def main():
    if OUT.exists():
        raise SystemExit('Use fresh boundary output')
    assessment = TASK / 'evidence_07'
    frozen = read(TASK / 'evidence_03/frozen_inventory.json')['rows']
    known_keys = {r['key'] for r in frozen}
    missing = defaultdict(list)
    for line in (assessment / 'reference_leads.jsonl').read_text().splitlines():
        row = json.loads(line)
        if (Path(row['target_depot']).suffix.lower() in
                {'.scene', '.quest', '.questphase', '.gamedef', '.game', '.conversations'}
                and row['target_key'] not in known_keys):
            missing[(row['target_key'], row['target_depot'])].append(row)
    missing_rows = [{'target_key': key, 'target_depot': depot, 'source_references': sources,
                     'classification': 'NO_STANDALONE_GRAPH_PROVIDER_IN_DEFINED_ARCHIVE_INVENTORY',
                     'next_action': 'Check the exact caller, embedded-file ownership and route eligibility. An absent standalone archive entry is not proof of a broken or playable route.'}
                    for (key, depot), sources in sorted(missing.items())]
    issues = read(assessment / 'voiceset_dispatch_inventory.json')['normalization_issues']
    graph_issues = [{**r, 'classification': 'SOURCE_GRAPH_INTERFACE_REQUIRES_REVIEW',
                    'next_action': 'Step 2 must inspect source connection handles and cross-graph/embedded interfaces before claiming connected dispatch coverage. Do not infer a vanilla defect from this normalizer result.'}
                   for r in issues]
    ledger = [
        {'id': 'BOUNDARY-OPAQUE', 'evidence': 'evidence_07/opaque_boundary_review.json',
         'count': 55, 'status': 'HEADER_IMPORTS_RECOVERED_OBJECTS_STILL_OPAQUE',
         'next_stage': 'STEP2_SCENE_DECODING_AND_STEP3_PLACEMENT_REVIEW',
         'next_action': 'Recover the one q303 scene using a supported decoder or retain a documented coverage hold; qualify placement/owner limits for 54 sector payloads before related edits.'},
        {'id': 'BOUNDARY-PROVIDERS', 'evidence': 'evidence_07/provider_collision_review.json',
         'count': 25, 'status': 'DIFFERENT_PAYLOADS_ALL_RETAINED_WINNER_NOT_PROVED',
         'next_stage': 'BEFORE_ANY_AFFECTED_EVENT_EDIT',
         'next_action': 'Establish the executing provider from the actual load configuration/observation for each affected occurrence. Sixteen byte-identical provider groups need no dialogue-byte disambiguation.'},
        {'id': 'BOUNDARY-MISSING-ORIGINAL', 'evidence': 'evidence_07/missing_reference_review.json',
         'count': 65, 'status': 'NO_PROVIDER_AFTER_NORMALIZED_LOOKUP',
         'next_stage': 'STEP3_ROUTE_SCOPE_OR_EXTERNAL_COMPATIBILITY_REVIEW',
         'next_action': 'Use each recorded caller or source literal to resolve relevance. The other 26 original apparent misses are verified ResourcePath case aliases: 25 present private PTFR phases and one external-mod Mitch entity.'},
        {'id': 'BOUNDARY-MISSING-CONVERSATIONS', 'evidence': 'evidence_07/conversation_inventory.json',
         'count': 25, 'status': 'REFERENCED_SCENE_TARGETS_WITHOUT_STANDALONE_PROVIDER',
         'next_stage': 'STEP3_ROUTE_REVIEW',
         'next_action': 'Review source conversation groups, conditions and possible embedded ownership. Do not synthesize absent scene text.'},
        {'id': 'BOUNDARY-MISSING-SUPPORT', 'evidence': 'evidence_07/support_inventory.json',
         'count': 58, 'status': 'REFERENCED_SUPPORT_PATHS_WITHOUT_PROVIDER',
         'next_stage': 'STEP3_RELATED_ACTOR_AND_CALLER_REVIEW',
         'next_action': 'Preserve these workspot references as unknown availability until their exact actor/caller is relevant. One also appears in the original missing-reference list, so counts overlap.'},
        {'id': 'BOUNDARY-MISSING-GLOBAL-GRAPHS', 'evidence': 'evidence_09/additional_missing_graph_references.json',
         'count': len(missing_rows), 'status': 'EXPANDED_CALLER_CENSUS_HAS_UNRESOLVED_STANDALONE_TARGETS',
         'next_stage': 'STEP3_ROUTE_AND_EMBEDDED_OWNER_REVIEW',
         'next_action': 'Use the retained source/hash and reference kind to inspect only relevant caller paths. These include old, inactive and embedded references and overlap earlier lists.'},
        {'id': 'BOUNDARY-GLOBAL-ROUTES', 'evidence': 'evidence_07/outside_scene_review.json',
         'count': 4513, 'status': 'INDEXED_POST_TOWER_ELIGIBILITY_UNCLASSIFIED',
         'next_stage': 'STEP3_ROUTE_REVIEW',
         'next_action': 'Review actual entries, scheduling and saved owners. Keep 3,811 scenes without an inbound lead in the defined inputs in the inventory; absence of a reference lead is not proof of irrelevance.'},
        {'id': 'BOUNDARY-DYNAMIC', 'evidence': 'evidence_07/speech_source_review.json',
         'status': 'COMPILED_NATIVE_SELECTION_AND_ARBITRARY_PLUGIN_FLOW_NOT_EXECUTION_PROVED',
         'next_stage': 'STEP2_DISPATCH_INDEX_AND_LATER_ROUTE_OR_RUNTIME_QUALIFICATION',
         'next_action': 'Use the source-defined voiceset calls and voice-tag metadata first. Track native compiled scripts, TweakDB selection, arbitrary external plugins, media events and generated paths as limits. No static inventory certifies every future sound dispatch.'},
        {'id': 'BOUNDARY-EXTERNAL-MAPS', 'evidence': 'evidence_07/speech_source_review.json',
         'count': 3, 'status': 'EXTERNAL_PLUGIN_VOICE_MAP_REGISTRATIONS_IDENTIFIED',
         'next_stage': 'STEP2_COMPATIBILITY_BOUNDARY_AND_LATER_RELATED_EVENT_REVIEW',
         'next_action': 'Lizzie voice-map registration paths are pinned in their installed source. Trace affected events before choosing any compatibility adaptation; unrelated-mod edits are outside this task.'},
        {'id': 'BOUNDARY-DISPATCH-GRAPHS', 'evidence': 'evidence_09/graph_interface_boundaries.json',
         'count': len(graph_issues), 'status': 'NORMALIZER_INTERFACE_GAPS_RETAINED',
         'next_stage': 'STEP2_DISPATCH_INDEX_VERIFICATION',
         'next_action': 'Inspect exact source connection and embedded interfaces before promoting structural reachability into connected caller coverage.'},
        {'id': 'BOUNDARY-ENGLISH', 'evidence': 'evidence_07/additional_english_subtitles.json',
         'count': 41, 'status': 'ADDITIONAL_SUBTITLE_PROVIDERS_REQUIRE_INDEX_SUCCESSOR',
         'next_stage': 'STEP2',
         'next_action': 'Add all exact provider identities and original variants in a fresh index successor, qualify spoken text separately from choice captions, and remeasure unresolved text. Three newly matched Johnny events are source candidates, not proven post-Tower occurrences.'},
    ]
    assert all(row.get('evidence') and row.get('next_action') and row.get('next_stage') for row in ledger)
    OUT.mkdir()
    write(OUT / 'additional_missing_graph_references.json', missing_rows)
    write(OUT / 'graph_interface_boundaries.json', graph_issues)
    write(OUT / 'boundary_ledger.json', {'boundaries': ledger,
        'supersedes': 'evidence_08/boundary_ledger.json',
        'correction': 'The 26 case aliases comprise 25 private PTFR phases and one external-mod Mitch entity. Total classifications are unchanged. The original ledger and code remain preserved.',
        'counts_overlap': True,
        'completion_definition': 'Every defined inventory input is accounted for; unresolved execution, decode, provider and dynamic boundaries retain evidence and a next action. This is not universal gameplay or transcript coverage.'})
    write(OUT / 'summary.json', {'boundary_categories': len(ledger),
        'expanded_missing_standalone_graph_targets': len(missing_rows),
        'expanded_missing_targets_by_extension': dict(Counter(Path(r['target_depot']).suffix for r in missing_rows)),
        'graph_interface_boundaries': len(graph_issues),
        'step1_completion': 'SOURCE_INVENTORY_COMPLETE_WITH_BOUNDARIES',
        'step2_next': 'SUPPLEMENTAL_COVERAGE_SUCCESSOR_REQUIRED',
        'step3_started': False, 'game_writes': 0, 'save_writes': 0})
    print(json.dumps(read(OUT / 'summary.json'), indent=2))


if __name__ == '__main__':
    main()
