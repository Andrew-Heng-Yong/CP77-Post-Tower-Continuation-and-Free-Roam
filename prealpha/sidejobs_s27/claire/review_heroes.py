"""Independent, read-only Heroes component review; writes a new bound report."""
import copy
import json
from pathlib import Path
from prepare import ROOT, read, sha, graphs, value, walk

BUILD = ROOT / 'prealpha/sidejobs_s27/heroes/build/heroes_03'
DEST = ROOT / 'research/sidejobs_s27/claire/heroes_review_01.json'
checks = []


def check(label, truth):
    assert truth, label
    checks.append(label)


def nn(g):
    return {n['id']: n for n in g['nodes']}


def ee(g):
    return set(map(tuple, g['edges']))


def facts(c):
    return {(v['factName'], v['comparisonType'], v['value'])
            for v in walk(c) if v.get('$type') == 'questVarComparison_ConditionType'}


def main():
    manifest = BUILD / 'component.json'
    m = read(manifest)
    c = read(ROOT / m['contract'])
    o = c['owners'][0]
    t = read(BUILD / 'tests.json')
    check('Reviewed final heroes_03 manifest identity', sha(manifest) == '8865357C75CE0A24DD06E786CFFED30A22917632D6FDFCFE43C8A1AF71AAB10C')
    check('Contract05 identity', sha(ROOT / m['contract']) == m['contract_sha256'] == 'E375781C7F27549E34EA5B87B3033C644AD64B1515B94D8D3A396DFFEC5F41FC')
    check('Component tests bind this manifest and contract', t['component_sha256'] == sha(manifest) and t['contract_sha256'] == m['contract_sha256'] and t['status'] == 'PASS_COMPONENT_NOT_LIVE')
    check('Test source identity', t['tester_sha256'] == sha(ROOT / 'prealpha/sidejobs_s27/heroes/test.py'))
    for p, h in m['source_pins'].items():
        check('Source pin: ' + p, sha(ROOT / p) == h)
    for r in m['resource_details']:
        check('Resource: ' + r['depot'], sha(BUILD / r['relative']) == r['sha256'])
        check('Readback: ' + r['depot'], sha(BUILD / r['readback']) == r['readback_sha256'])
    check('Only two new mod resources/boots, no overrides', len(m['resources']) == 2 and len(m['boots']) == 2 and not m['override_donors'] and all(p.startswith('towercontinued\\sidejobs_s27\\heroes\\') for p in m['resources']))
    h = graphs(BUILD / 'readback/heroes_package.json')
    s = graphs(BUILD / 'readback/mama_default.json')
    hn, sn = nn(h['root']), nn(s['root'])
    check('No hidden graphs in quest wrapper', set(h) == {'root'})
    check('Exact bounded main node set', set(hn) == {42, 89, 119, 1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1010})
    for witness in m['native_copies']:
        orig = graphs(ROOT / (witness['source'].replace('/raw/', '/json/') + '.json'))
        newgraph, sub = witness['target_graph'].split('/', 1)
        target = h if newgraph == 'heroes_package' else s
        old = copy.deepcopy(nn(orig[witness['source_graph']])[witness['source_id']])
        old['id'] = witness['target_id']
        check('Native payload: ' + witness['target_graph'] + '/' + str(witness['target_id']), old == nn(target[sub])[witness['target_id']])
        oldprefix = witness['source_graph'] + '/' + str(witness['source_id'])
        newprefix = sub + '/' + str(witness['target_id'])
        for path, g in orig.items():
            if path == oldprefix or path.startswith(oldprefix + '/'):
                to = newprefix + path[len(oldprefix):]
                check('Nested native payloads and edges: ' + to, target[to]['nodes'] == g['nodes'] and ee(target[to]) == ee(g))
    expected = {(1000,'Out',1001,'In'), (1001,'Out',1002,'In'), (1002,'Out',1003,'In'), (1003,'Out',89,'In'), (89,'Out',119,'In'), (119,'Out',1004,'In'), (1004,'False',1002,'In'), (1004,'True',1005,'In'), (1005,'Out',1006,'In'), (1006,'Out',1010,'In'), (1010,'Out',42,'In'), (42,'Out2',1007,'In'), (42,'Out1',1008,'In')}
    check('Contact follows one-shot issuance and precedes stock intro', ee(h['root']) == expected)
    contact = hn[1010]['type']['params'][0]
    check('Native Mama contact, notification policy intact', contact['contact']['realPath'] == 'contacts/mama_welles' and contact['addContact'] == 1)
    check('Direct native intro, no funeral/storage phase reference', value(hn[42]['phaseResource']['DepotPath']) == 'base\\quest\\side_quests\\sq018\\phases\\sq018_00_holocall.questphase')
    check('Unexpected funeral return fails without starting funeral', hn[1008]['type']['factName'] == o['tag'] + '_Fault' and hn[1007]['type']['factName'] == o['tag'] + '_Finished')
    for n in h['root']['nodes']:
        check('No custom inventory/reward/journal/world writes: ' + str(n['id']), n['$type'] not in {'questRewardManagerNodeDefinition', 'questJournalNodeDefinition', 'questItemManagerNodeDefinition', 'questSpawnManagerNodeDefinition', 'questWorldDataManagerNodeDefinition'})
        if n['$type'] == 'questFactsDBManagerNodeDefinition':
            check('Only own one-shot flag write: ' + str(n['id']), n['type']['factName'].startswith(o['tag'] + '_') and n['type']['value'] == 1 and n['type']['setExactValue'] == 1)
    shared = c['common_equal'] | o['facts_equal'] | {o['tag'] + '_Permit': 1, o['tag'] + '_Issued': 0, o['tag'] + '_Finished': 0, o['tag'] + '_Fault': 0, 'PTFRS27_PHONE_MAMA_Issued': 1}
    expectedfacts = {(k, 'Equal', v) for k, v in shared.items()}
    expectedfacts |= {(k, 'GreaterOrEqual', v['min']) for k, v in o['fact_ranges'].items()}
    expectedfacts |= {(k, 'LessOrEqual', v['max']) for k, v in o['fact_ranges'].items()}
    expectedjournals = {(j['path'], j['class'], 'Inactive') for j in o['journals']}
    check('Only sq018 whitelist root, all descendants guarded inactive', o['ids'] == ['sq018_jackie'] and all(j['states'] == [1] for j in o['journals']) and sum(j['class'] == 'gameJournalQuest' for j in o['journals']) == 1)
    check('Runtime contract has no circular support-issued predicate', 'PTFRS27_PHONE_MAMA_Issued' not in o['facts_equal'])
    intro = graphs(ROOT / (o['native_only_checks'][0]['source'].replace('/raw/', '/json/') + '.json'))
    default = graphs(ROOT / (o['service_source'].replace('/raw/', '/json/') + '.json'))
    inventory = copy.deepcopy(nn(intro['root/47'])[5]['condition'])
    inventory['type']['quantity'] = 0
    distance = nn(default['root/7/27/3/16'])[58]['condition']['conditions'][0]
    for ident in (1002,1004):
        guard = hn[ident]['condition']
        check('Entry guard AND: ' + str(ident), guard['operation'] == 'AND')
        check('All exact fresh/common/support predicates: ' + str(ident), facts(guard) == expectedfacts)
        journals = {(v['path']['realPath'],value(v['path']['className']),v['state']) for v in walk(guard) if v.get('$type') == 'questJournalEntryState_ConditionType'}
        check('All journal predicates: ' + str(ident), journals == expectedjournals)
        check('Key absence and Coyote offsite final recheck: ' + str(ident), guard['conditions'][-2:] == [inventory,distance])
    check('Completed, active, and outcome history protected', o['facts_equal']['sq018_done'] == o['facts_equal']['sq018_active'] == o['facts_equal']['q005_jackie_to_mama'] == o['facts_equal']['q005_jackie_stay_notell'] == 0)
    check('Native earned enable prerequisite retained', o['fact_ranges']['sq018_enable']['min'] == 1)
    check('Coyote active quest and ambient call excluded', o['facts_equal']['mq040_active'] == o['facts_equal']['pepe_dd_holo'] == 0)
    n = nn(intro['root']); p = nn(intro['root/47'])
    for ident in (15,64):
        check('Stock package route selected by original q005 choice: ' + str(ident), facts(n[ident]['condition']) == {('q005_jackie_to_mama','Equal',0),('q005_jackie_stay_notell','Equal',0)})
    check('Original package show at H10', value(n[59]['type']['params'][0]['prefabNodeRef']) == '#loc_megabuilding_a_devices' and value(n[59]['type']['params'][0]['variantStates'][0]['name']) == 'var_package' and n[59]['type']['params'][0]['variantStates'][0]['show'] == 1)
    check('Original key wait before package hide', p[5]['condition']['type']['quantity'] == 1 and p[5]['condition']['type']['itemID']['hash'] == 120771320143 and (5,'Out',16,'In') in ee(intro['root/47']))
    check('Original package hidden only at pickup continuation', p[16]['type']['params'][0]['variantStates'][0]['show'] == 0 and value(p[16]['type']['params'][0]['variantStates'][0]['name']) == 'var_package')
    check('Native motorcycle choice kept, not forced', facts(p[11]['condition']) == {('q003_jackie_motorcycle_upgraded','Greater',0)} and p[12]['type']['vehicle'] == 'Vehicle.v_sportbike2_arch_jackie_player' and p[13]['type']['vehicle'] == 'Vehicle.v_sportbike2_arch_jackie_tuned_player')
    expectedcompletion = {(64,'True',68,'In2'),(47,'Out1',68,'In1'),(68,'Out1',75,'In'),(75,'Out',76,'In'),(76,'Out',41,'Succeeded'),(41,'Out',20,'In'),(20,'Out',18,'In'),(18,'Out',30,'In'),(30,'Out',19,'In'),(19,'Out',27,'In'),(27,'Out',23,'In'),(23,'Out',69,'In')}
    check('Native call and pickup converge before original reward/completion', expectedcompletion <= ee(intro['root']))
    check('Native single reward identity', n[20]['type']['rewards'][0]['hash'] == 150486381774)
    check('Native Mama spawn/default then completion', n[75]['actions'][0]['type']['action'] == 'Reactivate' and value(n[75]['actions'][0]['type']['reference']) == '#mama_welles' and n[76]['type']['factName'] == 'mama_welles_default_on' and n[76]['type']['value'] == 1)
    closed = n[29]['type']['params']; opened = n[27]['type']['params']
    check('Same native Coyote doors close then reopen', [value(x['objectRef']) for x in closed] == [value(x['objectRef']) for x in opened] and all(value(x['deviceAction']) == 'ForceDisabled' for x in closed) and all(value(x['deviceAction']) == 'ForceEnabled' for x in opened))
    check('Service is only native Mama loop', set(sn) == {16,17,1000,1001,1002,1003} and all(k == 'root' or k.startswith('root/17') for k in s))
    servicefacts = c['common_equal'] | {o['tag']+'_Issued':1,o['tag']+'_Finished':1,o['tag']+'_Fault':0,'PTFRS27_PHONE_MAMA_Issued':1,'PTFRS27_HEROES_MAMA_Issued':0}
    check('Service waits for own successful completion and support', facts(sn[1002]['condition']) == {(k,'Equal',v) for k,v in servicefacts.items()})
    check('Only individual service loop wired', ee(s['root']) == {(1000,'Out',1001,'In'),(1001,'Out',1002,'In'),(1002,'Out',1003,'In'),(1003,'Out',16,'In'),(16,'Out',17,'In1'),(17,'Out1',16,'In')})
    h10 = [ROOT/'research/b0_h10_persistent/validation/h10_interactions.scene.json']
    h10 += [ROOT/f'research/b0_h10_all_interactions/validation/{name}.scene.json' for name in ('mirror','shower','sleep','sofa','wardrobe')]
    h10pins = {}
    for file in h10:
        text = file.read_text(encoding='utf-8-sig')
        h10pins[file.relative_to(ROOT).as_posix()] = sha(file)
        check('Scoped H10 service has no competing package variant write: ' + file.name, 'var_package' not in text)
    check('Final inputs unchanged during review', sha(manifest) == t['component_sha256'] and all(sha(ROOT/p) == v for p,v in m['source_pins'].items()))
    report = {
        'status':'PASS_INDEPENDENT_COMPONENT_REVIEW_NOT_LIVE',
        'component':manifest.relative_to(ROOT).as_posix(), 'component_sha256':sha(manifest),
        'contract':m['contract'], 'contract_sha256':m['contract_sha256'],
        'reviewer':Path(__file__).relative_to(ROOT).as_posix(), 'reviewer_sha256':sha(__file__),
        'tests_sha256':sha(BUILD/'tests.json'), 'checks':len(checks), 'passed_checks':checks,
        'additional_source_pins':h10pins, 'blocking_findings':[],
        'scope':'Wholly unstarted original Heroes package branch only. No funeral/Failed/progressed restart or completed replay.',
        'assessment':[
            'No custom item/reward/journal reset or broad NPC owner copied. Issued precedes native contact and original intro; final guard repeats native support/keyabsence/offsite checks.',
            'Stock q005 outcome branch, original package show/key pickup/hide, correct bike variant, reward, Mama spawn/default switch and Coyote reopening retained by direct original phase reference.',
            'Only Mama individual stock default loop added after this owner successfully finishes. Native physical/phone triggers and cleanup nested graphs match; other world NPC owners not copied.',
            'Inspected H10 interaction scenes have no var_package writers; this is scoped non-conflict evidence, not physical package pickup proof or a full world resource audit.'
        ],
        'limitations':[
            'Fresh all-Inactive/local-zero/keyabsent admission protects ordinary completed history; not a reconstruction of a full item/reward payout ledger after external resets.',
            'No live call/SMS/package pickup/reward/Mama/door/reload proof. H10 physical package access under repurchase policy remains a required playtest.',
            'Parent must bind official archive/raw-to-JSON witnesses, dependency closure, shared phone cleanup/controller and aggregate runtime/compiler/deployment proofs.',
            'Latest unfinished restart request is broader; this adds a safe fresh subset and must not be described as all unfinished jobs restored.'
        ], 'game_writes':False
    }
    assert not DEST.exists(), 'Review output immutable; choose successor path'
    DEST.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('status','component_sha256','checks','blocking_findings')},indent=2))


if __name__ == '__main__':
    main()
