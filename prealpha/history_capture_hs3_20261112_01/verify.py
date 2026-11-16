"""Independent semantic readback, saved-layout and capture protocol checks."""
import copy
import argparse
import importlib.util
import json
import re
import shutil
import sqlite3
from collections import Counter, defaultdict, deque
from common import HERE, ROOT, REGISTRY, MANIFEST, RED, LUA, ARCHIVE, read, sha, write, baseline


def load_model():
    path=REGISTRY/'model.py';spec=importlib.util.spec_from_file_location('hs3_readback_model',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def reach(graph,start,omit=None):
    adjacency=defaultdict(set)
    for a,sa,ta,b,sb,tb in graph['edges']:
        if ta=='Output' and tb=='Input' and a!=omit and b!=omit: adjacency[a].add(b)
    seen=set(start)-{omit};todo=list(seen)
    while todo:
        for node in adjacency[todo.pop()]-seen:seen.add(node);todo.append(node)
    return seen


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--attempt',type=int,default=3);args=ap.parse_args()
    out=HERE/f'verification_{args.attempt:02}';assert not out.exists();out.mkdir()
    m,game=baseline();plan=read(HERE/'evidence_01/plan.json');model=load_model()
    archive=read(HERE/'archive_02/readback.json');package=HERE/'candidate_04/package'
    original_archive=HERE/'candidate_02/package'/ARCHIVE
    assert sha(original_archive)==archive['archive_sha256']
    target=package/ARCHIVE
    if not target.exists():shutil.copyfile(original_archive,target)
    assert sha(target)==archive['archive_sha256']
    checks=[];diffs=[]
    def check(name,ok):
        assert ok,name
        checks.append(name)
    check('all_1738_existing_archive_payloads_retained',archive['retained']==1738 and archive['members']==1740 and sum(r['retained'] for r in archive['resources'])==1738)
    for gate in plan['gates']:
        prefix=HERE/'archive_02'/str(gate['route'])
        before=model.normalize(model.load_export(str(prefix)+'_before.json'))
        after=model.normalize(model.load_export(str(prefix)+'_after.json'))
        check(f"route_{gate['route']}_all_support_and_root_parameters_preserved",before['support']==after['support'])
        bg={g['path']:g for g in before['graphs']};ag={g['path']:g for g in after['graphs']}
        check(f"route_{gate['route']}_all_graph_identities_preserved",bg.keys()==ag.keys())
        for path,g in bg.items():
            new=ag[path]
            if path!=gate['graph']:
                assert g==new,(gate['route'],path)
                continue
            ns={n['id']:n for n in g['nodes']};new_ns={n['id']:n for n in new['nodes']}
            assert set(new_ns)-set(ns)==set(range(60000,60007))
            assert all(new_ns[n]==old for n,old in ns.items())
            old_edge=(gate['from'],'Out','Output',gate['to'],'In','Input')
            expected=Counter(map(tuple,g['edges']));assert expected[old_edge]==1;expected.subtract([old_edge]);expected=+expected
            extra=[(gate['from'],'Out','Output',60000,'In','Input')]
            extra.extend((n,'Out','Output',n+1,'In','Input') for n in range(60000,60006))
            extra.append((60006,'Out','Output',gate['to'],'In','Input'));expected.update(extra)
            assert Counter(map(tuple,new['edges']))==expected
            check(f"route_{gate['route']}_only_seven_additive_nodes_and_one_replaced_edge",True)
            facts=[(n,new_ns[n]['parameters']['type']['factName'],new_ns[n]['parameters']['type']['value'],new_ns[n]['parameters']['type']['setExactValue']) for n in [60000,60001,60002,60003,60005,60006]]
            assert facts==[(60000,'PTFRHS3_GateResult',0,1),(60001,'PTFRHS3_GateRoute',gate['route'],1),
                           (60002,'PTFRHS3_GateTicket',1,0),(60003,'PTFRHS3_GateOpen',1,1),
                           (60005,'PTFRHS3_GateOpen',0,1),(60006,'PTFRHS3_GatePassed',1,1)]
            condition=new_ns[60004]['parameters']['condition']
            assert condition['operation']=='OR' and condition['conditions'][0]['type']['factName']=='PTFRHS3_GateResult'
            assert condition['conditions'][0]['type']['comparisonType']=='Greater' and condition['conditions'][0]['type']['value']==0
            delay=condition['conditions'][1]['type'];assert delay['seconds']==30 and delay['hours']==delay['minutes']==delay['miliseconds']==0
            writers={n['id'] for n in g['nodes'] if any(x.get('$type')=='questJournalBulkUpdate_NodeType' for x in model.walk(n['parameters']))}
            reachable_writers=writers & reach(g,g['inputs'])
            assert reachable_writers and reachable_writers==writers & reach(new,new['inputs']) and not writers & reach(new,new['inputs'],60004)
            assert gate['to'] not in reach(new,new['inputs'],60005)
            check(f"route_{gate['route']}_gate_dominates_bulk_writers_and_closes_before_native_work",True)
            if gate['route']==2:
                assert ns[46]['parameters']['type']['factName']=='q115_point_of_no_return'
                assert ns[46]['parameters']['type']['value']==1 and 46 not in reach(new,new['inputs'],60004)
            diffs.append({'depot':gate['depot'],'graph':path,'retained_nodes':len(ns),'added_nodes':7,'bulk_writers_after_gate':len(reachable_writers),
                          'native_disconnected_writers_preserved':sorted(writers-reachable_writers),
                          'original_edge':old_edge,'replacement_edges':extra,'ack_or_timeout_seconds':30})
    # Bound the current XL inventory, and check injections targeting either
    # patched resource independently of resource-depot provider checks.
    registrations=read(REGISTRY/'evidence_01/registrations.json')
    paths=set()
    for row in registrations['files']:
        path=row['file'] if 'file' in row else row['path'];paths.add(str(path).lower())
        assert sha(path)==row['sha256'],path
    current={str(p).lower() for p in (game/'archive/pc').rglob('*.xl')}
    assert paths==current,(paths-current,current-paths)
    targets={g['depot'] for g in plan['gates']}
    bindings=[r for r in registrations['phase_bindings'] if r['binding']['parent'].lower() in targets]
    check('current_54_xl_files_unchanged_and_no_injections_into_patched_resources',len(paths)==54 and not bindings)
    old=(game/RED).read_text(encoding='utf-8');new=(package/RED).read_text(encoding='utf-8')
    old_fields=re.findall(r'\bpersistent let [^;]+;',old)
    legacy=new.split('public abstract class SnapshotDataHS3 {',1)[0]
    new_fields=[x for x in re.findall(r'\bpersistent let [^;]+;',legacy) if 'nativeTicketHS3:' not in x]
    check('every_existing_saved_field_and_legacy_index_preserved',new_fields==old_fields and
          old.split('public abstract class SnapshotDataHS1 {',1)[1].split('// ORIGINAL: r6/scripts/TowerContinued_HistorySnapshot_HS1/SnapshotStateHS1.reds')[0]==
          new.split('public abstract class SnapshotDataHS1 {',1)[1].split('// ORIGINAL: r6/scripts/TowerContinued_HistorySnapshot_HS1/SnapshotStateHS1.reds')[0])
    restored=legacy.split('public func Restored() -> Void {',1)[1].split('private func Register()',1)[0]
    check('restore_never_clears_frozen_rows_from_early_boundary_reads','this.Boundary()' not in restored and
          not any(x in restored for x in ('this.rows=','this.frozen=false','this.ready=false','this.fileToken=n""','this.origin=n""')))
    check('native_guards_match_exact_insertion_side_of_q115_point_fact',
          '(route==2 && this.Fact("q115_point_of_no_return")==0 && this.Fact("q307_point_of_no_return")==0)' in new and
          '(route==2 && this.Fact(n"q115_point_of_no_return")==0 && this.Fact(n"q307_point_of_no_return")==0)' in new)
    check('failed_later_capture_cannot_admit_older_history','!this.NativeHistoryCurrentHS3()' in new and
          new.count('this.committedTicket!=this.Fact(n"PTFRHS3_GateTicket")')==2)
    check('no_function_returned_snapshot_struct_field_indexing',not re.search(r'\.(ReadRow|ReadJournal|AdmissionRow)\([^\n]*?\)\.(states|facts|state|counter)',new))
    additions=(HERE/'capture_hs3.reds').read_text()+(HERE/'legacy_members.reds').read_text()
    check('new_runtime_writes_only_its_capture_ack_fact',set(re.findall(r'\.SetFact\(n"([^"]+)"',additions))=={'PTFRHS3_GateResult'} and '.SetFactStr(' not in additions)
    check('dual_exporter_matches_executed_lua_fixtures',sha(package/LUA)==read(HERE/'verification_01/export_fixtures.json')['candidate_sha256'])
    compile_result=read(HERE/'compile_04/result.json')
    check('all_148_registered_sources_compiled_for_selected_candidate',compile_result['status']=='PASS' and compile_result['source_count']==148 and compile_result['staged_hashes'][RED]==sha(package/RED))
    rows=[];changed=[]
    for original in m['core_files']:
        p=package/original['path'];h=sha(p)
        rows.append({'path':original['path'],'bytes':p.stat().st_size,'sha256':h})
        if h!=original['sha256']:changed.append(original['path'])
    check('only_three_of_51_core_files_changed',set(changed)=={RED,LUA,ARCHIVE})
    data=read(HERE/'evidence_01/catalogue.json')
    ids={r['id'] for r in data['quests']}
    check('three_previously_missing_selected_jobs_captured',{'mq006_rollercoaster','mws_se5_07','mws_wat_08_trauma_drama'}<=ids)
    check('machine_gun_progress_facts_and_existing_skippy_quantity_captured','Items.mq007_skippy' in data['items'] and
          any('01_deliver_skippy' in r['path'] for r in data['journals']) and
          {'mq007_skippy_owner_known','mq007_skippy_enemies_lethal','mq007_skippy_enemies_non_lethal','mq007_skippy_enemies_total'}<=set(data['facts']))
    # Worst-width source packet bound, including explicit unknown markers.
    definitions=[{'kind':'journal',**r} for r in data['journals']]+[{'kind':'fact','name':n} for n in data['facts']]+[{'kind':'item_quantity','id':n} for n in data['items']]
    size=sum(len(json.dumps({'definition':d,**({'state':-2147483648,'counter':-2147483648,'optional':-1,'tracked':-1,'stable':False} if d['kind']=='journal' else {'value':-2147483648,'stable':False})},ensure_ascii=False,separators=(',',':')).encode())+1 for d in definitions)+1000
    check('complete_source_catalogue_fits_export_limit',size<8388608)
    write(out/'semantic_diff.json',{'changes':diffs,'source_model_sha256':sha(REGISTRY/'model.py')})
    write(out/'verification.json',{'status':'PASS_BOUNDED_HS3_IMPLEMENTATION_CHECKS','checks':checks,'count':len(checks),
                                  'maximum_estimated_export_bytes':size,'candidate':'candidate_04','archive':'archive_02',
                                  'runtime_qualification':'PENDING','tool_sha256':sha(__file__)})
    write(HERE/'candidate_04/manifest.json',{'core_epoch':'HS3_NATIVE_HISTORY_CAPTURE','predecessor_epoch':m['core_epoch'],
          'baseline_sha256':sha(MANIFEST),'core_files':rows,'required_files':m['required_files'],'changed_files':changed,
          'archive_members':1740,'archive_readback_sha256':sha(HERE/'archive_02/readback.json'),
          'compile_sha256':sha(HERE/'compile_04/result.json'),'verification_sha256':sha(out/'verification.json'),
          'game_root':str(game),'installed':False})
    baseline()
    print(json.dumps({'checks':len(checks),'changed_files':changed,'estimated_export_bytes':size,'status':'PASS_BOUNDED_HS3_IMPLEMENTATION_CHECKS'}))


if __name__=='__main__':main()
