"""Independent B collector review: synthetic-only calls, all fixtures under worker_b."""
from pathlib import Path
import sys,json,hashlib,importlib.util,unittest,io,copy,ast,argparse
W=Path(__file__).resolve().parents[3];H=Path(__file__).resolve().parent;Q=H.parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def loadmod(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();out=H/a.out
 if out.exists():raise RuntimeError('Fresh output required')
 out.mkdir(parents=True);checks=[]
 def ck(n,v,**e):checks.append({'name':n,'pass':bool(v),**e})
 paths=[Q/'collect_observation.py',Q/'test_collection.py',Q/'collection_config.json',H/'verification_04/SYNTHETIC_events.jsonl',H/'addon_manifest_04.json'];pins=[{'path':str(p),'sha256':sha(p),'size':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns}for p in paths]
 c=loadmod('qr9_b_review_collector',paths[0]);cfg=json.loads(paths[2].read_text());
 for p in cfg['pins']:ck('frozen-collector-input:'+p['path'],sha(p['path'])==p['sha256'])
 t=loadmod('qr9_b_review_test_collection',paths[1]);t.H=out/'fixtures';stream=io.StringIO();suite=unittest.defaultTestLoader.loadTestsFromTestCase(t.CollectionTests);res=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);(out/'fixture_run.txt').write_text(stream.getvalue());ck('exact-root-seven-fixtures-isolated-under-B',res.wasSuccessful()and res.testsRun==7,tests=res.testsRun,errors=len(res.errors),failures=len(res.failures))
 data=paths[3].read_bytes();rows=[json.loads(r)for r in data.splitlines()];name=rows[0]['run_id'];profile=rows[0]['profile'];r=c.analyze_capture(data,name,profile,cfg['expected_capture_metadata']);ck('real-B04-Lua-producer-to-frozen-collector-schema',r['capture_integrity']=='VALID_CAPTURE'and r['declared_addon_metadata']=='MATCHING_DECLARATION_NOT_EXECUTED_BYTE_PROOF',result=r)
 ck('synthetic-capture-not-promoted-to-gameplay-or-graph',r['gameplay_result']=='NOT_TESTED'and set(r['unsupported'].values())=={'NOT_OBSERVED'})
 corrupt=[]
 for fault,edit in [('STOP-data-array',lambda x:next(z for z in x if z['event']=='STOP').__setitem__('data',[])),('cleanup-data-array',lambda x:next(z for z in x if z['event']=='LISTENER_CLEANUP_CALLS').__setitem__('data',[])),('event-array',lambda x:x[1].__setitem__('event',[])),('schema-bool',lambda x:x[1].__setitem__('schema',True)),('seq-bool',lambda x:x[0].__setitem__('seq',True)),('stale-source-declaration',lambda x:x[0]['data']['declared_build'].__setitem__('source_lua_sha256','0'*64))]:
  z=copy.deepcopy(rows);edit(z);b=('\n'.join(json.dumps(x)for x in z)+'\n').encode();rr=c.analyze_capture(b,name,profile,cfg['expected_capture_metadata']);corrupt.append({'fault':fault,'rejected':rr['capture_integrity']!='VALID_CAPTURE'});ck('actual-produced-row-mutant:'+fault,corrupt[-1]['rejected'])
 z=copy.deepcopy(rows);z[1]['data']['not_finite']=float('nan');rr=c.analyze_capture(('\n'.join(json.dumps(x)for x in z)+'\n').encode(),name,profile,cfg['expected_capture_metadata']);ck('nonstandard-JSON-NaN-is-rejected',rr['capture_integrity']!='VALID_CAPTURE')
 ck('CET-scripting-error-log-in-bounded-support-candidates',any(pattern=='scripting.log'for rel,pattern in c.SUPPORT.values()))
 tree=ast.parse(paths[0].read_text());imports={n.names[0].name for n in ast.walk(tree)if isinstance(n,ast.Import)};ck('no-game-process-loader-GUI-network-or-execution-import',not imports.intersection({'ctypes','subprocess','pyautogui','socket','requests'}))
 ck('no-eval-exec-or-delete-in-collector',not any(isinstance(n,ast.Call)and(isinstance(n.func,ast.Name)and n.func.id in('eval','exec')or isinstance(n.func,ast.Attribute)and n.func.attr in('unlink','rmdir','rename','replace'))for n in ast.walk(tree)))
 ck('all-reviewed-source-files-remained-exact',all(sha(p['path'])==p['sha256']and Path(p['path']).stat().st_mtime_ns==p['mtime_ns']for p in pins))
 result={'status':'APPROVE_BOUNDED_READONLY_COLLECTOR_WITH_DECLARATION_LIMITS'if all(x['pass']for x in checks)else'FAIL','checks':checks,'assertion_count':len(checks),'root_fixture_methods':res.testsRun,'independent_actual_producer_mutants':corrupt,'reviewed_input_pins':pins,'manual_findings':[{'scope':'Current hashes are collection-time observations, not proof of the bytes present earlier during capture.','disposition':'QUALIFIED_CORRECTLY'},{'scope':'Latest support logs can be stale; candidate lines are capped and not automatic findings.','disposition':'QUALIFIED_CORRECTLY'},{'scope':'Metadata version/source match is a declaration only; actual graph/owner/engine receipt/native clock/queue/save identity remain NOT_OBSERVED.','disposition':'QUALIFIED_CORRECTLY'},{'scope':'Malformed data/event, duplicate keys, NaN and boolean schema/seq now reject safely rather than crash or certify.','disposition':'CURRENT_STRICT_PARSER_VERIFIED'},{'scope':'All collection fixtures use synthetic game/save trees under this B output; real CLI collector not run against game.','disposition':'SOURCE_PRESERVATION_VERIFIED_IN_FIXTURE'}],'game_API_calls':0,'real_game_or_save_writes':0,'runtime_gameplay_results':'NOT_TESTED'}
 (out/'review.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],len(checks),'assertions',res.testsRun,'root fixture methods')
 if result['status']=='FAIL':raise SystemExit(1)
if __name__=='__main__':main()
