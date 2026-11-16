"""Readback validation against pinned source identities and real quest cases."""
import json
import sqlite3
from prepare import HERE, read, sha, write


def main():
    source = sqlite3.connect((HERE / 'registry_02/registry.sqlite3').resolve().as_uri() + '?mode=ro', uri=True)
    db = sqlite3.connect((HERE / 'contexts_01/contexts.sqlite3').resolve().as_uri() + '?mode=ro', uri=True)
    summary = read(HERE / 'contexts_01/summary.json')
    checks = []
    def check(name, condition):
        assert condition, name
        checks.append(name)
    check('context_database_integrity', db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok')
    check('registry_source_hash', summary['source_registry_sha256'] == sha(HERE / 'registry_02/registry.sqlite3'))
    check('routes_source_hash', summary['source_routes_sha256'] == sha(HERE / 'routes_02/routes.sqlite3'))
    expected = {(r[0], r[1]) for r in source.execute("SELECT s.quest_id,s.path FROM stages s JOIN quests q ON q.id=s.quest_id WHERE q.selection!='EXCLUDE'")}
    actual = set(db.execute('SELECT quest_id,path FROM stages'))
    check('all_selected_and_separate_scope_stage_paths_preserved', actual == expected)
    check('all_160_selected_quests_present', summary['selected_quests'] == 160)
    check('all_1719_selected_paths_preserved', summary['selected_stage_counts']['paths'] == 1719)
    # Validate repeated feature references once against the source identity set.
    # The same scene feature can appear in hundreds of stage contexts.
    valid_nodes = set(source.execute('SELECT rid,graph,id FROM nodes'))
    referenced_features = set()
    site_count = 0
    for rid, graph, node, record in db.execute('SELECT * FROM sites'):
        r = json.loads(record)
        assert (rid, graph, node) in valid_nodes and r['location'] == [rid, graph, node]
        assert r['review_status'] == 'SOURCE_CONTEXT_ONLY_NOT_A_RESUME_CONTRACT'
        for feature in r['feature_relations'].values():
            for f in feature:
                referenced_features.add((rid, graph, f['node']))
        site_count += 1
    check('every_source_site_and_feature_reference_resolves', site_count == summary['unique_sites'] and referenced_features <= valid_nodes)
    scope_keys = set(db.execute('SELECT rid,graph FROM scopes'))
    for rid, graph, text in db.execute('SELECT * FROM scopes'):
        r = json.loads(text)
        for parent in r['parent_scopes']:
            assert (parent['rid'], parent['graph']) in scope_keys
            assert (parent['rid'], parent['graph'], parent['node']) in valid_nodes
    check('recursive_owner_and_support_scope_references_resolve', True)
    def site(rid, graph, node):
        return json.loads(db.execute('SELECT record_json FROM sites WHERE rid=? AND graph=? AND node=?', (rid, graph, node)).fetchone()[0])
    check('native_deliver_skippy_activation', site(6542, 'root/5', 11)['journal_write_inputs'] == ['Active'])
    check('scene_delivery_completion_mapping', site(2366, 'scene', 177)['journal_write_inputs'] == ['Succeeded'])
    check('scene_talk_to_regina_activation_mapping', site(2366, 'scene', 183)['journal_write_inputs'] == ['Active'])
    check('tattoo_objective_activation', site(3640, 'root', 15)['journal_write_inputs'] == ['Active'])
    check('no_safe_resume_contract_fabricated', all(json.loads(r[0])['resume_contract_status'] == 'NOT_QUALIFIED' for r in db.execute('SELECT record_json FROM stages')))
    db.close(); source.close()
    result = {'status': 'PASS_BOUNDED_SOURCE_CONTEXT_READBACK', 'checks': checks,
              'tool_sha256': sha(__file__), 'contexts_sha256': sha(HERE / 'contexts_01/contexts.sqlite3'),
              'limits': 'No gameplay, admission, branch feasibility, exact receipts or saved-owner proof.'}
    write(HERE / 'contexts_01/verification.json', result)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
