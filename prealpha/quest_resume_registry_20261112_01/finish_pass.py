"""Publish a bounded workspace report and advance the mutable analysis pointer."""
import json
import sqlite3
from collections import Counter
from model import value
from prepare import HERE, read, sha, write


def main():
    out = HERE / 'report_02'
    assert not out.exists(), 'Fresh report required'
    previous = read(HERE / 'checkpoint.json')
    assert previous['registry'] == 'registry_02' and 'contexts' not in previous
    verification = read(HERE / 'contexts_01/verification.json')
    assert verification['status'] == 'PASS_BOUNDED_SOURCE_CONTEXT_READBACK'
    assert verification['contexts_sha256'] == sha(HERE / 'contexts_01/contexts.sqlite3')
    db = sqlite3.connect((HERE / 'registry_02/registry.sqlite3').resolve().as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    routes = sqlite3.connect((HERE / 'routes_02/routes.sqlite3').resolve().as_uri() + '?mode=ro', uri=True)
    boundaries = read(HERE / 'report_01/boundary_review.json')['rows']
    reviewed = []
    for row in boundaries:
        if row['classification'] != 'SOURCE_INTERFACE_REVIEW_REQUIRED':
            continue
        r = dict(row); rid, graph, entry = r['rid'], r['graph'], r['entry']
        r['caller_links'] = [x for text, in routes.execute('SELECT record_json FROM links WHERE root=?', (r['registration_ordinal'],))
                             if (x := json.loads(text))['target'] == [rid, graph, entry]]
        if graph == 'scene':
            support = json.loads(db.execute('SELECT support_json FROM resources WHERE rid=?', (rid,)).fetchone()[0])
            r['available_scene_entries'] = [str(value(x['name'])) for x in support.get('entryPoints', [])]
            assert entry not in r['available_scene_entries']
            r['classification'] = 'CALL_INPUT_ABSENT_FROM_AUTHORED_SCENE_ENTRIES'
            if rid == 14756:
                regular = json.loads(db.execute('SELECT support_json FROM resources WHERE rid=10575').fetchone()[0])
                gold = json.loads(db.execute('SELECT support_json FROM resources WHERE rid=1726').fetchone()[0])
                r['native_comparison'] = {'regular_provider': 10575, 'regular_entries': [str(value(x['name'])) for x in regular['entryPoints']],
                                           'gold_provider': 1726, 'gold_entries': [str(value(x['name'])) for x in gold['entryPoints']]}
                assert entry not in r['native_comparison']['regular_entries'] and entry in r['native_comparison']['gold_entries']
                r['classification'] = 'SCENE_VARIANT_INTERFACE_MISMATCH_REQUIRES_CALLER_FEASIBILITY_REVIEW'
        elif rid == 15439:
            r['classification'] = 'INLINE_SHELL_WITH_CONNECTED_EXTERNAL_PHASE_REVIEW'
        elif rid == 8032:
            r['classification'] = 'EMPTY_INLINE_GRAPH_WITHOUT_EXTERNAL_PHASE'
        else:
            r['classification'] = 'CALL_INPUT_ABSENT_FROM_INLINE_GRAPH_ENTRIES'
        r['next_action'] = 'Resolve actual runtime input handling and path feasibility from the pinned caller before changing any graph. Static MAY connectivity alone is not a gameplay defect.'
        reviewed.append(r)
    assert len(reviewed) == 12
    out.mkdir()
    write(out / 'checkpoint_before.json', previous)
    write(out / 'interface_review.json', {'rows': reviewed, 'counts': dict(Counter(r['classification'] for r in reviewed)),
                                          'status': 'SOURCE_CASES_CLASSIFIED_RUNTIME_SEMANTICS_PENDING'})
    contexts = read(HERE / 'contexts_01/summary.json')
    activities = read(HERE / 'activities_01/summary.json')
    write(out / 'summary.json', {'status': 'SOURCE_INVENTORY_AND_STAGE_CONTEXT_MILESTONE',
                                 'contexts': contexts, 'activities': activities,
                                 'step_1_complete': False, 'semantic_stage_review_complete': False,
                                 'q307_changes': 0, 'game_writes': 0, 'save_writes': 0})
    report = '''# Mid-progress restoration registry — current checkpoint

12 November 2026. Installed baseline: QP2_QUEST_HISTORY_AUTOLOAD.

The source census and stage review packets are built. **Step 1 remains in progress:** these packets are evidence for reviewing safe resumption, not finished resume contracts.

## Coverage

| Scope | Records | Authored phase/objective paths |
| --- | ---: | ---: |
| Selected gigs and side/minor jobs | 160 (80 + 80) | 1,719 |
| Separately scoped activities/services/rewards | 15 | 90 |
| Additional installed scanner/cyberpsycho families | 26 + 17 | 167 |
| Excluded jobs, retained for reconciliation | 52 | In original source registry only |

These are source-reference counts. They include definition-only and edited paths; they are not counts of safe stages or valid combinations of objectives. Eleven other connected quest roots are prerequisite references, not restored quests. One singular `ncpd_scanner_n1` registration is now correctly grouped with the scanner family; report_01 is retained unchanged.

The 175 main/separately scoped records have 13,432 unique stage source sites and 3,275 recursive owner/support scopes. The packets retain journal state inputs, optional flags, local predecessor journal sites, predicates, choices, joins, waits, fanouts, inventory/reward sites, actor/support references and original/private caller identities. Scene socket stamps are mapped to their authored quest-node inputs. Dependencies remain source locations where exact runtime semantics are unknown.

## Findings relevant to the implementation

- The 158-row snapshot lacks Love Rollercoaster, Shape of a Pony and Career Opportunities. The Prophet's Song remains a historical row despite exclusion from new admission. Preserve saved indices and migrate explicitly; do not delete or reorder history rows.
- Machine Gun's Deliver Skippy, Put Skippy Down and Talk to Regina entries are distinct. Native delivery activation and scene completion resolve to different state inputs. The user's corrected fixture is Deliver Skippy. Weapon grants, mode/counter changes and Regina's reward must retain their separate source identities.
- The Gig's tattoo objective and cash reward remain separately indexed. Source ordering alone is not a receipt proving the reward was already paid.
- The remaining 12 generic interface cases have now been classified from exact callers and authored inputs. Three scan-blood calls target a scene whose regular native variant also lacks those entry names; a gold variant contains them. This requires caller/variant and path-feasibility review, not a blind reconnection. Other cases include native input-name differences, an empty inline graph and external-phase shells. All 58 trace boundaries remain explicit; none was converted into runtime proof.

## Validation

The initial census verified 51 installed Core files and 26 required dependencies. It captured 15,741 providers and traced 829 registered PTFR roots. The independent existing graph parser agreed on all 2,091 compared providers. Ten graph fixtures, four caller-input fixtures, thirteen inventory checks and thirteen additional stage-context readback checks passed. All selected/separately scoped stage identities and recursive caller references resolve into the pinned source registry. Machine Gun's delivery/Regina socket mapping and The Gig's tattoo activation were checked against their actual graph data.

## Remaining work before step 1 is complete

1. Review feasible parallel-objective combinations, branch-specific earned prerequisites and valid continuation entries. Structural MAY paths can contain mutually exclusive or impossible routes.
2. Bind stage contracts to original/saved ownership and required actor/support lifecycle, including parent prefabs, callbacks, interruptions and reloads. A source caller is not a live owner.
3. Review one-time rewards, item changes and receipts; no packet is admitted for runtime resumption yet.
4. Close current base-journal definition coverage. Both strict decoders fail on `gameJournalQuestMapPin.mappinData`. A bounded, exact-byte-position retry found repeated anomalies in both current providers and produced no accepted complete export. No stale journal or broadly ignored parser error was substituted.
5. Resolve provider precedence and interface semantics where the inventory records competing payloads or absent inputs. The unrelated q303 scene decode failure remains outside the selected scope.

No mod resources, scripts, q307 behavior, saves, facts or installation were changed. No game was launched and no gameplay qualification is claimed. The next step is semantic stage/owner/reward review using these packets; implementation should consume reviewed contracts, not assume every indexed path is resumable.
'''
    (out / 'REPORT.md').write_text(report, encoding='utf-8')
    inputs = ['contexts_01/manifest.json', 'contexts_01/verification.json', 'activities_01/manifest.json',
              'evidence_05/journal_decode.json', 'report_01/manifest.json']
    manifest = {'files': {str(p.relative_to(HERE)): sha(p) for p in out.iterdir() if p.is_file()},
                'inputs': {p: sha(HERE / p) for p in inputs},
                'tools': {p.name: sha(p) for p in HERE.glob('*.py')}}
    write(out / 'manifest.json', manifest)
    checkpoint = {**previous, 'contexts': 'contexts_01', 'activities': 'activities_01',
                  'report': 'report_02/REPORT.md', 'report_manifest_sha256': sha(out / 'manifest.json'),
                  'next': 'Review feasible stage combinations and earned predicates, saved/original owner and support lifecycle, and one-time receipts. Resolve pinned decoder/provider/interface boundaries; no runtime admission changes yet.'}
    assert read(HERE / 'checkpoint.json') == previous
    (HERE / 'checkpoint.json').write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    db.close(); routes.close()
    print(json.dumps({'report': checkpoint['report'], 'step_1_complete': False, 'interface_cases_classified': len(reviewed)}))


if __name__ == '__main__':
    main()
