"""Compact applicability index; stock definitions remain separate from execution."""
from pathlib import Path
import sys,zlib,collections,argparse
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args()
tp=O/'shared/tdb_targets_01/targets.json';rp=O/'shared/tdb_records_01/records.json';t=read(tp);r=read(rp);out=Path(args.output).resolve();assert not out.exists()
def tid(name):
 if str(name).isdigit():return str(int(name))
 b=name.encode();return str((len(b)<<32)|zlib.crc32(b))
for test in r['hash_tests']:assert test['pass']
by={x['id']:x for x in r['records']};rows=[]
positions={x['id']:i for i,x in enumerate(r['records'])}
database_hashes={x['path']:sha(x['path'])for x in r['databases']}
assert all(database_hashes[x['path']]==x['sha256']for x in r['databases'])
capture_pin=sha(rp);targets_pin=sha(tp)
for quest in sorted({u['quest']for u in t['uses']}):
 uses=[u for u in t['uses']if u['quest']==quest];ids=sorted({tid(u['record'])for u in uses});targets=[]
 for ident in ids:
  record=by.get(ident);assert record is not None,'Direct target omitted by bounded capture'
  definitions=record['database_definitions']
  fields=[x['fields'] for x in definitions]
  targets.append({'id':ident,'requested_aliases':sorted({u['record']for u in uses if tid(u['record'])==ident}),'exists_in_stock':record['exists'],'record_types':sorted({x['record_type']for x in definitions}),'databases':[x['database']for x in definitions],'base_ep1_definitions_identical':len(fields)>1 and all(x==fields[0]for x in fields[1:]),'record_json_path':'records/'+str(positions[ident]),'immediate_references':record['record_references'],'uncaptured_immediate_references':[x for x in record['record_references']if x!='0'and x not in by]})
 data={'quest_id':quest,'status':'STOCK_TARGET_DEFINITIONS_SOURCE_PINNED_REQUIRES_ROUTE_APPLICABILITY','targets':targets,'uses':uses,'capture':{'path':str(rp),'sha256':capture_pin,'targets_path':str(tp),'targets_sha256':targets_pin},'limits':r['limits']+['Direct targets include catalogue candidates, including foreign/unreachable references; actual executing-owner applicability requires per-quest review.']}
 write(out/(quest+'.json'),data);rows.append({'quest_id':quest,'direct_targets':len(ids),'found':sum(x['exists_in_stock']for x in targets),'missing':[x['id']for x in targets if not x['exists_in_stock']],'base_ep1_conflicts':[x['id']for x in targets if len(x['databases'])>1 and not x['base_ep1_definitions_identical']],'applicability_file':str(out/(quest+'.json')),'sha256':sha(out/(quest+'.json'))})
summary={'status':'PASS_BOUNDED_STOCK_TARGET_INDEX_NOT_RUNTIME_PARITY','quests_with_record_occurrences':len(rows),'original_target_aliases':len(t['targets']),'captured_records':len(by),'stock_records_found':sum(x['exists']for x in by.values()),'missing_records':[x['id']for x in by.values()if not x['exists']],'bounded_out_unique':len({x['id']for x in r['bounded_out']}),'per_quest':rows,'input_pins':{str(tp):sha(tp),str(rp):sha(rp),str(O/'read_stock_records.ps1'):sha(O/'read_stock_records.ps1')},'databases':r['databases'],'limits':r['limits']}
write(out/'index.json',summary);print({k:summary[k]for k in ['status','quests_with_record_occurrences','captured_records','missing_records','bounded_out_unique']})
