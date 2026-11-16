"""Source-pinned KM1 ownership and early-stage review; no game/save mutation."""
from pathlib import Path
from collections import defaultdict
import ast
import base64
import hashlib
import json
import struct
import sys

HERE = Path(__file__).resolve().parent
WS = HERE.parents[1]
sys.path.insert(0, str(WS / 'tools/parity_audit'))
sys.path.insert(0, str(WS / 'prealpha/quest_restoration_qr15/event_stage_01'))
from model import Resource
from common import walk
from analyze_components import decode_paths, phase_hash
from analyze_native_layout import native_records


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest().upper()


def main():
    output = HERE / 'analysis_01.json'
    assert not output.exists()
    providers = read(HERE / 'source_01/providers.json')
    grouped = defaultdict(list)
    for row in providers['resources']:
        assert sha(row['raw']) == row['sha256']
        assert sha(row['json']) == row['json_sha256']
        grouped[row['depot']].append(row)
    assert len(grouped) == 12 and all(len(v) == 1 for v in grouped.values())
    rows = {d: v[0] for d, v in grouped.items()}
    models = {d: Resource(read(r['json'])).normalize() for d, r in rows.items()}
    assert all(not m['errors'] for m in models.values())
    installed = read(WS / 'prealpha/johnny_dialogue_pilot_jp1/deployment_01/installed_manifest_01.json')
    package = WS / 'prealpha/johnny_dialogue_pilot_jp1/candidate_03'
    package_manifest = read(package / 'package_manifest.json')
    for d, r in rows.items():
        if d.startswith('towercontinued'):
            assert r['sha256'] == package_manifest['source_resources'][d] == sha(package / 'archive_source' / d)
    native = r'base\quest\minor_quests\mq016' + chr(92)
    private = 'towercontinued\\sidejobs_s29\\native\\'
    entry = r'towercontinued\sidejobs_s29\entries\mq016_bartmoss.questphase'
    base_quest = models[r'base\quest\cyberpunk2077.quest']
    base_phase = models[r'base\quest\cyberpunk2077.questphase']
    minor = models[r'base\quest\minor_quests\minorquests.questphase']
    freezer = models[private + native + r'phases\mq016_01_freezer.questphase']
    shard = models[private + native + r'phases\mq016_00_shard.questphase']
    main = models[private + native + 'mq016_bartmoss.questphase']
    gate = models[entry]['graphs']['root']
    # Exact source ancestry, including the saved resource root ordinal.
    assert base_quest['graphs']['root']['nodes']['2']['refs'] == [r'base\quest\cyberpunk2077.questphase']
    assert base_phase['graphs']['root/82']['nodes']['6']['refs'] == [r'base\quest\minor_quests\minorquests.questphase']
    assert minor['graphs']['root']['nodes']['5']['refs'] == [native + 'mq016_bartmoss.questphase']
    ancestry = [0, 2, 82, 6, 5]
    for m in [base_quest, base_phase, minor, main]:
        assert not m['root_prefabs']
    for m, gp, i in [(base_quest,'root','2'), (base_phase,'root','82'), (base_phase,'root/82','6'), (minor,'root','5')]:
        assert not m['graphs'][gp]['nodes'][i]['payload']['phaseInstancePrefabs']
    root = base_phase['graphs']['root']
    assert ['106','Out','109','In'] in root['edges']
    assert ['109','Out','107','In'] in root['edges']
    assert root['nodes']['107']['payload']['type'] == 'Terminating'
    assert root['nodes']['109']['writes'] == [{'$type':'questSetVar_NodeType','factName':'q307_main_game_killed','setExactValue':1,'value':1}]
    # All pre-trigger, normal (non-debug) setup operations are bounded here.
    fg = freezer['graphs']['root']
    init = freezer['graphs']['root/2']
    assert ['0','Out','2','In1'] in fg['edges']
    assert ['2','Out1','16','In'] in fg['edges']
    assert ['16','Out','7','Active'] in fg['edges']
    assert ['7','Out','5','In'] in fg['edges']
    assert ['0','Out','10','In'] in init['edges']
    assert ['10','False','7','In'] in init['edges']
    assert ['7','Out','1','In'] in init['edges']
    assert not init['nodes']['7']['reward']
    assert init['nodes']['7']['payload']['type']['params'][0]['enable'] == 0
    assert init['nodes']['7']['node_refs'] == ['#mq016_bartmoss_cyberdeck']
    assert fg['nodes']['7']['journal_paths'] == ['points_of_interest/minor_quests/mq016_bartmoss']
    assert freezer['root_prefabs'] == ['#mq016_pr_freezer']
    assert shard['root_prefabs'] == ['#mq016_pr_shard']
    for i in ['135','65006','5']:
        assert i in gate['nodes']
    assert ['135','Out','65006','In'] in gate['edges']
    assert ['65006','Out','5','In1'] in gate['edges']
    for i in ['65003','65004']:
        hits = [r for r in gate['nodes'][i]['reads'] if r.get('factName') == 'mq016_active']
        assert len(hits) == 1 and hits[0]['value'] == 0
        assert len(gate['nodes'][i]['journal_paths']) == 63
    debug_facts = sorted({r['factName'] for m in [freezer,shard] for g in m['graphs'].values() for n in g['nodes'].values() for r in n['reads'] if r.get('factName','').startswith('mq016_dbg')})
    assert debug_facts == ['mq016_dbg_shard','mq016_dbg_test_def']
    # Only pure function AST is loaded from the legacy freezer decoder.
    decoder_source = WS / 'prealpha/quest_restoration_qr15/rebind_01/analyze.py'
    tree = ast.parse(decoder_source.read_text(encoding='utf-8-sig'))
    fn, = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'decode_freezer']
    namespace = {'struct': struct}
    exec(compile(ast.Module(body=[fn],type_ignores=[]),str(decoder_source),'exec'),namespace)
    decode_freezer = namespace['decode_freezer']
    qr15 = WS / 'prealpha/quest_restoration_qr15'
    capture_path = qr15 / 'event_stage_01/components_01/manifest.json'
    cap = read(capture_path)
    components = {r['name']:r for r in cap['nodes']}
    def component(name):
        r=components[name]
        assert sha(r['path']) == r['sha256']
        return Path(r['path']).read_bytes(), r['id']
    old_path = qr15 / 'earlier_saves_01/capture_03/wa1backup16.json'
    old = read(old_path)
    _, older_paths = decode_paths(base64.b64decode(old['components']['customArray']['base64'],validate=True),old['components']['customArray']['id'])
    older_events = native_records(base64.b64decode(old['components']['eventManager']['base64'],validate=True),old['components']['eventManager']['id'])
    _, newer_paths = decode_paths(*component('customArray'))
    newer_events = native_records(*component('eventManager'))
    newer_frozen = decode_freezer(*component('questPhaseFreezer'))
    def lookup(paths,events,frozen=()):
        prefix = tuple(ancestry)
        selected = {p for p in paths if p[:len(prefix)] == prefix} | {prefix,prefix[:-1]}
        all_by_hash=defaultdict(set)
        for path in set(paths)|selected:
            all_by_hash[phase_hash(path)].add(path)
        hashes={phase_hash(p):p for p in selected}
        assert all(all_by_hash[h]=={p} for h,p in hashes.items())
        def qualifies(h,n):
            return h in hashes and (hashes[h] != prefix[:-1] or n == prefix[-1])
        found=[{'slot':i,'path':hashes[h],'node':n,'type':hex(t)} for i,(t,h,n) in enumerate(events) if t and n != 65535 and qualifies(h,n)]
        frozen_found=[{'group':i,'path':hashes[h],'node':n} for i,(_,owner,members) in enumerate(frozen) for h,n in [owner,*(key for key,_ in members)] if qualifies(h,n)]
        return {'interned_paths':sorted(selected-{prefix[:-1]}),'events':found,'freezer':frozen_found}
    older = lookup(older_paths,older_events)
    newer = lookup(newer_paths,newer_events,newer_frozen)
    assert older['events'] and not newer['events'] and not newer['freezer']
    result = {
        'schema':1,'status':'SOURCE_AND_HISTORICAL_OWNER_REVIEW_COMPLETE',
        'baseline':'JP1 candidate_03; no runtime changes',
        'providers':str(HERE/'source_01/providers.json'),
        'provider_inventory_sha256':sha(HERE/'source_01/providers.json'),
        'native_owner_path':ancestry,
        'retirement_source':{'resource':r'base\quest\cyberpunk2077.questphase','graph':'root','route':'106 (Tower journal Succeeded) -> 109 (receipt) -> 107 (Terminating output)','descendant':'root/82:6 -> minorquests:5 -> MQ016','ancestor_prefabs':'None on the reviewed path'},
        'saved_owner_evidence':{'earlier_body_sha256':old['source_sha256'],'later_body_sha256':cap['source_sha256'],'earlier':older,'later':newer,'scope':'Pinned historical bodies; neither is claimed as the exact currently loaded user fixture. Source termination and the new user matching natural-approach comparison are separate corroborating evidence.'},
        'prepared_stage':{'guard':'Inactive root and all 62 child journal entries; mq016_active=1; all seven other protected MQ016 facts zero; unclaimed private owner; existing startup/common/support gates; no debug branch','original_prefix':['native milestone waits','native mq015_active=0 wait','mq016_done check','mq016_active set exactly to already-required 1','existing Entered receipt','native MQ016 root input'], 'setup':['acquire existing shard and freezer prefab scopes','disable cyberdeck interactions until native pickup enable','set mq016_active exactly to already-required 1','activate native discovery POI','arm original freezer approach/scan wait and shard-read listener'], 'reward_replay':'No item, currency, achievement, reward or counter grant occurs in this normal pre-trigger prefix. Completion/pickup/reward routes remain native and unchanged.', 'debug_zero_required':debug_facts},
        'planned_change':{'resources':[entry],'script':'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds','guard_nodes':['65003','65004'],'identities':'Retain all graph nodes, edges, resources, receipts and XL registrations. Add a narrow prepared-state alternative to both guards and matching two-sample script check; preserve current fresh route.'},
        'remaining_limits':['Runtime wait rebinding and streamed support remain gameplay checks.','Exact current owner is not observed by a live engine inspector.','No global or later-stage KOLD MIRAGE resume support is claimed.'],
        'pins':{str(p):sha(p) for p in [capture_path,old_path,decoder_source,WS/'tools/parity_audit/model.py',WS/'prealpha/quest_restoration_qr15/event_stage_01/analyze_components.py',WS/'prealpha/quest_restoration_qr15/event_stage_01/analyze_native_layout.py']},
        'game_writes':0,'save_writes':0,
    }
    with output.open('x',encoding='utf-8') as f:
        json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'status':result['status'],'older_saved_handlers':len(older['events']),'later_saved_handlers':len(newer['events']),'later_frozen_rows':len(newer['freezer']),'guard_nodes':2,'normal_setup_rewards':0}))


if __name__ == '__main__':
    main()
