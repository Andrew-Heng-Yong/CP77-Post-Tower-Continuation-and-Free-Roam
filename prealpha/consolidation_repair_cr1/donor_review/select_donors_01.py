"""CR1 explicit donor approval contract. Read-only against all historical evidence.

This deliberately approves each depot by purpose; archive filename ordering is
only corroboration. It copies approved bytes into the new CR1 workspace.
"""
import copy
import hashlib
import json
import shutil
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[3]
O = Path(__file__).resolve().parent
A = W / 'diagnostics/sidejob_entry_phone_audit_20261026_01'
sys.path.insert(0, str(W / 'tools'))
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


def rel(p):
    return Path(p).resolve().relative_to(W).as_posix()


def walk(v):
    if isinstance(v, dict):
        yield v
        for c in v.values():
            yield from walk(c)
    elif isinstance(v, list):
        for c in v:
            yield from walk(c)


def fact(v, name, value):
    return any(n.get('factName') == name and n.get('value') == value for n in walk(v))


def pin(p):
    return {'path': rel(p), 'sha256': sha(p)}


# graph tuple: path, changed existing node IDs, restored node IDs,
# edges restored, current edges replaced. No current node may be removed.
def g(changed=(), added=(), restore_edges=0, replace_edges=0, path='root'):
    return (path, list(changed), list(added), restore_edges, replace_edges)


GUARD = ('Restore the previously installed S25 native root/ownership recheck at '
         'both admission nodes; retain the complete quest body, journal paths and '
         'saved node IDs. This tightens owner admission and does not reset facts '
         'or permit replay of a Failed/Succeeded root.')
S25 = ['recovery/fred_scene_fs1_01/receipt.json',
       'prealpha/sidejobs_s25/build/s25_04/build.json']
CONFIG = {
 'sidejobs_s23/base_b/mq038.questphase': ('JD1 Dennis', 'Restore JD1 Dennis phone-handler Issued acknowledgement in wait 1003 before fresh Big in Japan admission; the restored native controller is already packaged.', [g([1003])], ['docs/judy_dennis_jd1.md']),
 'gig_phone_u9/fixer_cleanup.questphase': ('JD1 and prior phone cleanup', 'Restore the accumulated scoped cleanup branches: 49 root nodes and six inline courier nodes. Original 23 root payloads remain exact; receipt-gated character/NCPD branches and native cleanup are restored without global phone initialization or clearing queued requests.', [g([], [334,466,600,601,700,701,800,801,802,803,804,805,806,807,808,809,900,901,902,903,910,911,1000,1001,1002,1003,1010,1011,1200,1201,1202,1203,1204,1205,1206,1207,1208,1209,1210,1211,1240,1251,1252,1253,1254,1255,1300,1301,1302],82,3),g([], [0,1,2,3,68,69],7,0,'root/601')], ['docs/judy_dennis_jd1.md', 'diagnostics/sidejob_entry_phone_audit_20261026_01/phone_entry/cleanup_census_01.json']),
 'relationship_mirrors/m10_owner.questphase': ('H1 mirror lease', 'Restore PTFRRM10_Suspended == 0 AND gates at existing nodes 7 and 13, retaining each original condition and every edge. This lets the H1 lease suspend the existing mirror owner; no owner identity changes.', [g([7,13])], ['research/housing_h1/compatibility/assessment_02.json','prealpha/housing_h1/native/build_06.ps1']),
 'b0_h10_persistent/h10_owner.questphase': ('H1 H10 entitlement', 'Restore the H1 availability gate (Ready == 0 OR h10_Entitled == 1) AND the complete previous node-2 condition. Existing node IDs and every edge stay exact; housing access coordination is restored.', [g([2])], ['research/housing_h1/compatibility/assessment_02.json','prealpha/housing_h1/native/build_06.ps1']),
 'sidejobs_s25/families/sq025_fresh.questphase': ('SR1 Delamain receipt', 'Restore shared SupportIssued receipt 65020 between existing 92 and persistent controller 94. It records the existing controller for the S29 adoption guards, preventing a second support owner; no controller restart.', [g([], [65020],2,1)], ['docs/sidejob_repair_sr1_production.md']),
 'sidejobs_s23/base_b/mq030.questphase': ('SR1 Bullets shop rearm', 'Restore wait 1021 and its two edges that rearm the copied Zane shop owner after the encounter releases it; preserve all original encounter and phone nodes.', [g([], [1021],2,0)], ['docs/sidejob_repair_sr1_production.md']),
 'b0_story_eight/yoko.scene': ('SR1 This Corrosion choices', 'Restore node-779 component conversation options 4–7 with scoped quest prerequisites and their original continuations. Retain all other scene nodes, dialogue, cast, workspots and scene identity.', [779], ['docs/sidejob_repair_sr1_production.md']),
 'sidejobs_s23/base_a/mq024_sandra.questphase': ('S25 Full Disclosure', GUARD, [g([1001,1002])], S25),
 'sidejobs_s23/base_a/mq041_corpo.questphase': ('S25 War Pigs', GUARD, [g([1001,1002])], S25),
 'sidejobs_s22/delamain/support.questphase': ('S25 Delamain support exclusion', 'Restore S25 fresh-owner exclusion in both S22 support admission conditions 1002/1003; retain the native phone body and all saved identities. This is coordinated with SR1 shared receipt restoration.', [g([1002,1003])], S25),
 'side_job_pilot_s1/owner.questphase': ('S25 Happy Together guard', 'Restore native Inactive-root check at existing admission wait 402. Do not arm this legacy owner or alter its runtime selection; all body nodes and reward guards remain unchanged.', [g([402])], S25),
 'b0_story_eight/viktor.scene': ('S25 Viktor debt choice', 'Restore the two paid-debt options on nodes 351/840 with paid permission and active quest prerequisites, leading to retained native debt continuations. Other scene graph nodes, dialogue and actor bindings are exact.', [351,840], S25),
 'sidejobs_s22/the_gig_reward_resume.questphase': ('S25 The Gig reward continuation', GUARD, [g([1001,1002])], S25),
 'sidejobs_s22/moving_heat_boot.questphase': ('S25 Moving Heat', GUARD, [g([2,3])], S25),
 'sidejobs_s23/base_a/mq012_stud.questphase': ('S25 A Day in the Life', GUARD, [g([1001,1002])], S25),
 'sidejobs_s23/base_a/mq002_veterans.questphase': ('S25 Gun Music', GUARD, [g([1001,1002])], S25),
 'sidejobs_s23/base_b/mq026.questphase': ('S25 Prophet sibling exclusion', 'Restore PTFRS25_MQ026_FRESH_Issued == 0 exclusion in existing nodes 1002 and 1004. Preserve the existing partial-progress/native gates; do not start a fresh sibling over its owner.', [g([1002,1004])], S25),
 'b0_story_services/fred.questphase': ('S25 boxing selector plus FS1 release', 'Restore native boxing scene selector 300/301 and FS1 private-scene release/rearm 400–403. Private ambient admission/release uses 8m/12m, while original boxing admission/unload retains 50m/100m. The archived S25 package is the exact later FS1 installed revision.', [g([4,5],[300,301,400,401,402,403],13,2,'root/5/14')], S25+['docs/fred_scene_fs1.md']),
 'b0_wilson_vendor/body.questphase': ('S25 The Gun dispatch', 'Restore fresh gun-order scene dispatch 100/101 under the existing Wilson body; retain the default vendor branch, original dialogue and rewards.', [g([], [100,101],4,1)], S25),
 'sidejobs_s23/base_a_v2/mq007_resume_boot.questphase': ('S25 Machine Gun continuation', GUARD, [g([1001,1002])], S25),
 'sidejobs_s23/base_a/mq044_jakes_vehicle.questphase': ('S25 Sex on Wheels', GUARD, [g([1001,1002])], S25),
 'sidejobs_s22/mq025_progress.questphase': ('S25 Beat on the Brat continuation', GUARD, [g([1001,1002])], S25),
 'sidejobs_s22/delamain/owner.questphase': ('S25 Delamain owner guard', GUARD, [g([1002,1003])], S25),
 'sidejobs_s23/base_a/mq007_smartgun.questphase': ('S25 Machine Gun fresh owner', GUARD, [g([1001,1002])], S25),
 'sidejobs_s23/ep1/mq306_boot.questphase': ('S25 Balls to the Wall', GUARD, [g([2,3])], S25),
 'sidejobs_s23/base_a/mq021_guide.questphase': ('S25 Stadium Love', GUARD, [g([1001,1002])], S25),
 'sidejobs_s23/base_a/mq035_ozob.questphase': ('S25 Send in the Clowns', GUARD, [g([1001,1002])], S25),
 'b0_wilson_vendor/owner.questphase': ('S23/H2 Wilson owner release', 'Restore the bounded owner handoff/release acknowledgement at nodes 100–103 and node-3 lease gate. H2 receipt exactly pins this S23 archive; restoring only the S25 body would omit this required coordination.', [g([3],[100,101,102,103],6,1)], ['recovery/h10_h2_01/receipt.json']),
 'afterlife_interactions_r8/rogue.scene': ('PA6 Rogue lipsync bounds repair', 'Restore the exact PA6 fault repair: remove unused duplicate Rogue lipsync resource slot and change V index 2 to 1. Keep all 47 scene nodes, physical Rogue actor, dialogue, workspots, saved scene interface and interruptions exact. PA6 tied this out-of-bounds index to a captured crash.', [], ['prealpha/postending_pa6/rogue/build/rogue_02/tests.json','research/postending_pa6/rogue/crash_probe.json','prealpha/postending_pa6/rogue/test.py']),
 'special_gigs_u9/gang_retaliation.questphase': ('U10 scoped retaliation', 'Restore the two U10 Started-owner gates around the unchanged native retaliation conditions and the two activation edges. No historical gang retaliation fact is reset; content remains restricted to the corresponding restored gig owners.', [g([37],[],1,0,'root/22/33/227'),g([79],[],1,0,'root/22/37/298')], ['prealpha/gigs_u10/native/build_03.ps1','prealpha/gigs_u10/native/test_04.py','research/gigs_u10/native/assessment_03.json']),
}


def phase_comparison(donor, current, expected, is_fred=False):
    ds = {g['path']: g for g in flatten(donor, donor.obj['Data']['RootChunk'])}
    cs = {g['path']: g for g in flatten(current, current.obj['Data']['RootChunk'])}
    result = []
    for path in sorted(ds.keys() | cs.keys()):
        dn = {n['id']: n for n in ds.get(path, {}).get('nodes', [])}
        cn = {n['id']: n for n in cs.get(path, {}).get('nodes', [])}
        assert cn.keys() <= dn.keys(), (path, 'removes saved node')
        changed = sorted(i for i in cn.keys() & dn.keys() if cn[i] != dn[i])
        for i in cn.keys() & dn.keys():
            assert cn[i]['$type'] == dn[i]['$type'], (path, i, 'saved node type')
        added = sorted(dn.keys() - cn.keys())
        de = {tuple(e) for e in ds.get(path, {}).get('edges', [])}
        ce = {tuple(e) for e in cs.get(path, {}).get('edges', [])}
        if changed or added or de != ce:
            result.append((path, changed, added, len(de-ce), len(ce-de)))
    assert sorted(result) == sorted(expected), ('unapproved graph delta', result, expected)
    # Root resource identity / non-graph properties cannot change unnoticed.
    dr = copy.deepcopy(donor.obj['Data']['RootChunk'])
    cr = copy.deepcopy(current.obj['Data']['RootChunk'])
    dr.pop('graph'); cr.pop('graph')
    if is_fred:
        # FS1 used serialized source output. Only this compiler metadata value
        # differs; this is not a graph or persisted-owner identity property.
        assert dr['cookingPlatform']=='PLATFORM_None' and cr['cookingPlatform']=='PLATFORM_PC'
        dr['cookingPlatform']=cr['cookingPlatform']
    assert donor.payload(dr) == current.payload(cr), 'phase root metadata drift'
    return result, ds, cs


def scene_comparison(donor, current, expected, is_rogue):
    dr = donor.obj['Data']['RootChunk']; cr = current.obj['Data']['RootChunk']
    dg = donor.payload(dr['sceneGraph']); cg = current.payload(cr['sceneGraph'])
    dn = {n['nodeId']['id']: n for n in dg['graph']}
    cn = {n['nodeId']['id']: n for n in cg['graph']}
    assert dn.keys() == cn.keys(), 'scene node identity drift'
    assert sorted(i for i in dn if dn[i] != cn[i]) == expected
    dg.pop('graph'); cg.pop('graph')
    assert dg == cg, 'scene graph interface drift'
    d = donor.payload({k:v for k,v in dr.items() if k != 'sceneGraph'})
    c = current.payload({k:v for k,v in cr.items() if k != 'sceneGraph'})
    if is_rogue:
        assert len(c['resouresReferences']['lipsyncAnimSets']) == 3
        assert c['resouresReferences']['lipsyncAnimSets'][0] == c['resouresReferences']['lipsyncAnimSets'][1]
        c['resouresReferences']['lipsyncAnimSets'].pop(1)
        assert c['playerActors'][0]['lipsyncAnimSet']['id'] == 2
        c['playerActors'][0]['lipsyncAnimSet']['id'] = 1
        assert len(dn) == 47
    assert d == c, 'scene actor/dialogue/non-graph drift'
    return {'retained_nodes':len(dn),'changed_nodes':expected,
            'non_graph':'PA6 exact duplicate removal and V2->1' if is_rogue else 'exact'}, dn, cn


def main():
    inventory = read(A / 'collision_decoded_01/inventory.json')
    collisions = read(A / 'collision_donors_01.json')
    prior_manifest = W / 'recovery/full_consolidation_v1_01/install_manifest_01.json'
    old = {r['path']: r for r in read(prior_manifest)['old_files']}
    col = {r['depot']: r for r in collisions['rows']}
    assert len(CONFIG) == len(inventory) == len(col) == 30
    assert set(CONFIG) == {r['depot'].replace('\\','/').removeprefix('towercontinued/') for r in inventory}
    archive_pins = {}
    rows = []
    checks = []
    for r in inventory:
        key = r['depot'].replace('\\','/').removeprefix('towercontinued/')
        label, rationale, expected, evidence = CONFIG[key]
        assert sha(r['donor_raw']) == r['donor_sha256']
        assert sha(r['current_raw']) == r['current_sha256']
        assert r['donor_sha256'] != r['current_sha256']
        archive = Path(r['donor_archive'])
        install = 'archive/pc/mod/' + archive.name
        if archive.name not in archive_pins:
            archive_pins[archive.name] = pin(archive)
            assert archive_pins[archive.name]['sha256'] == old[install]['sha256']
            assert archive.stat().st_size == old[install]['bytes']
        variants = col[r['depot']]['variants']
        assert variants[0]['sha256'] == r['donor_sha256']
        assert Path(variants[0]['archive']).name == archive.name
        assert variants[-1]['sha256'] == r['current_sha256']
        donor = SafeResource(read(r['donor_json']))
        current = SafeResource(read(r['current_json']))
        if key.endswith('.questphase'):
            comparison, ds, cs = phase_comparison(donor, current, expected,key.endswith('fred.questphase'))
            def node(path, ident):
                return next(n for n in ds[path]['nodes'] if n['id'] == ident)
            if key.endswith('m10_owner.questphase'):
                for ident in [7,13]:
                    d = node('root',ident)['condition']
                    c = next(n for n in cs['root']['nodes'] if n['id']==ident)['condition']
                    assert d['operation']=='AND' and d['conditions'][0] == c
                    assert fact(d['conditions'][1], 'PTFRRM10_Suspended', 0)
            if key.endswith('h10_owner.questphase'):
                d = node('root',2)['condition']
                c = next(n for n in cs['root']['nodes'] if n['id']==2)['condition']
                assert d['operation']=='AND' and d['conditions'][0] == c
                assert d['conditions'][1]['operation']=='OR'
                assert fact(d['conditions'][1],'PTFRH1_Ready',0) and fact(d['conditions'][1],'PTFRH1_h10_Entitled',1)
            if key.endswith('mq038.questphase'):
                assert fact(node('root',1003), 'PTFRJD1_Dennis_Issued', 1)
            if key.endswith('fixer_cleanup.questphase'):
                assert len(ds['root']['nodes'])==72 and len(cs['root']['nodes'])==23
            if key.endswith('fred.questphase'):
                d=node('root/5/14',4); e=node('root/5/14',5)
                assert sorted(n['distanceValue'] for n in walk(d) if 'distanceValue'in n)==[8,50]
                assert sorted(n['distanceValue'] for n in walk(e) if 'distanceValue'in n)==[12,100]
                receipt=read(W/'recovery/fred_scene_fs1_01/receipt.json')
                assert receipt['files'][0]['after']==archive_pins[archive.name]['sha256']
            if key=='b0_wilson_vendor/owner.questphase':
                receipt=read(W/'recovery/h10_h2_01/receipt.json')
                assert next(x for x in receipt['files'] if x['target']==install)['after']==archive_pins[archive.name]['sha256']
            if key.endswith('gang_retaliation.questphase'):
                for path,ident,owner,target in [('root/22/33/227',37,'PTFRU10_sts_hey_rey_02_Started',38),('root/22/37/298',79,'PTFRU10_sts_wbr_jpn_12_Started',81)]:
                    d=node(path,ident)['condition']
                    c=next(n for n in cs[path]['nodes'] if n['id']==ident)['condition']
                    assert d['operation']=='AND' and d['conditions'][1]==c
                    assert fact(d['conditions'][0],owner,1)
                    assert [0,'Out',target,'In'] in ds[path]['edges']
        else:
            comparison, _, _ = scene_comparison(donor,current,expected,key.endswith('rogue.scene'))
        target = O / 'selected_raw' / Path(r['depot'].replace('\\','/'))
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(r['donor_raw'],target)
        assert sha(target)==r['donor_sha256']
        evidence_pins = [pin(W / p) for p in evidence]
        rows.append({'depot':r['depot'],'key':col[r['depot']]['key'],
            'decision':'RESTORE_REVIEWED_PRECONSOLIDATION_REPAIR',
            'repair':label,'rationale':rationale,
            'current_sha256':r['current_sha256'],'selected_sha256':r['donor_sha256'],
            'source':rel(target),'original_extracted_source':rel(r['donor_raw']),
            'archived_source':archive_pins[archive.name],
            'decoded_sources':[pin(r['donor_json']),pin(r['current_json'])],
            'evidence':evidence_pins,'semantic_delta_current_to_selected':comparison,
            'root_metadata_exception':{'cookingPlatform':['PLATFORM_PC','PLATFORM_None']} if key.endswith('fred.questphase') else None})
        checks.append({'depot':r['depot'],'status':'PASS',
                       'checks':['raw and decoded source pins','archived source equals saved preconsolidation manifest','explicit reviewed semantic delta','no removed current node IDs or changed current node types','phase metadata audited with recorded Fred cookingPlatform exception; scene interface/cast/dialogue preserved','copied selection hash exact']})
    contract={'schema':'PTFR_CR1_EXPLICIT_DONORS_V1','status':'APPROVED_30_RESOURCE_RECONCILIATION',
        'selection_policy':'Each named depot is independently approved. Never infer an unlisted winner by archive order.',
        'baseline':'S30 candidate_02 1172-member combined archive',
        'resource_count':30,'install_path_count_change':0,
        'source_evidence':[pin(prior_manifest),pin(A/'collision_decoded_01/inventory.json'),pin(A/'collision_donors_01.json')],
        'rows':rows,'limitations':['Static restoration of prior repairs; no live gameplay assertion.',
          'Existing saved owners retain saved node identities. Restored resource definition does not guarantee a running saved node will revisit its admission gate.',
          'No fact reset, root replay, global initializer restart, new journal admission, whitelist expansion or installation is performed by this review.',
          'No donor is rejected, but each depends on the existing complete consolidated runtime; these are not standalone hotfix packages.',
          'The H1 archive is pinned to the final preconsolidation manifest, not falsely equated with the initial H1 install receipt. H2 pins S23 Wilson; FS1 pins the later S25 archive.']}
    (O/'selection_01.json').write_text(json.dumps(contract,indent=2)+'\n',encoding='utf8')
    review={'status':'PASS','contract_sha256':sha(O/'selection_01.json'),'resources':len(rows),
        'archived_donor_packages':len(archive_pins),'checks':checks,'game_writes':0,'save_writes':0}
    (O/'review_01.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf8')
    md=['# CR1 explicit donor reconciliation','',
      'All 30 overlapping depots are approved individually for restoration from the hash-pinned preconsolidation backups. The S25 donor includes the later FS1 fix, S23 includes H2, and S29 includes the installed SR1 production repair. H1 is pinned to the final preconsolidation manifest and its member-level compatibility review, not its older initial package hash.','',
      'The selector verifies every selected raw payload and archived package, bounds every changed graph/node set, retains existing node types and IDs, and checks the H1 lease gates, Fred distances, exact PA6 scene delta and U10 owner gates. Scene cast/dialogue/interface remain exact. Phase root metadata remains exact except Fred cookingPlatform PC-to-None, inherited from the installed FS1 serialized source and recorded in the contract. No donor is rejected.','',
      '| Depot (under `towercontinued/`) | Reviewed repair and rationale |','| --- | --- |']
    for r in rows:
        md.append('| `'+r['depot'].replace('\\','/').removeprefix('towercontinued/')+'` | **'+r['repair']+'**: '+r['rationale']+' |')
    md += ['', 'Run `select_donors_01.py` to regenerate the contract and selected workspace payloads. `selection_01.json` is the build contract; `review_01.json` records its successful checks.', '',
      'This restores resource definitions; it does not clear facts, issue replacement owners, restart a global phone initializer or guarantee that an already-running saved owner revisits an admission node. Installation, archive readback, full compilation, all 81 sidejob checks, save preservation and rollback verification remain the parent CR1 workflow. Gameplay remains live pending.','']
    (O/'review_01.md').write_text('\n'.join(md),encoding='utf8')
    print(json.dumps({'status':review['status'],'resources':len(rows),'archives':len(archive_pins),'contract':rel(O/'selection_01.json'),'sha256':review['contract_sha256']}))


if __name__=='__main__':
    main()
