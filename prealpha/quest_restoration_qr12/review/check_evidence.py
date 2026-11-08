"""Independent recheck of existing QR12 JSON, not a save parser or game reader."""
from pathlib import Path
import collections,hashlib,json,subprocess
H=Path(__file__).resolve().parent;Q=H.parent;W=Q.parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def vals(p,n):return [v['value_u32']if v['value_u32']<2**31 else v['value_u32']-2**32 for v in p['facts'].get(n,[])]
def pos(p,n):return any(v>0 for v in vals(p,n))
def main():
 inv=read(Q/'inventory.json');jobs=read(Q/'parse_jobs.json')['jobs'];coverage=read(Q/'coverage.json');parsed={};checks=[]
 for item in coverage['parser_inputs']:
  path=Path(item['path']);assert sha(path)==item['sha256'];data=read(path)
  assert data['parser_sha256']=='E607F058C74822B157CAE97F827310C4353CB323D440AE1E3A591307717645FD'
  for row in data['results']:
   assert row['sha256']not in parsed
   assert row['status']=='PARSED_SAVED_FACTS_AND_OPAQUE_SURFACES'and row['parse_result']=='NoError'and row['unchanged_after_read']
   parsed[row['sha256']]=row
 assert set(parsed)=={x['sha256']for x in jobs}=={x['sha256']for x in inv['rows']}
 checks.append('all recorded reader inputs match pinned hashes and exactly cover unique jobs/inventory bodies')
 current=[x for x in inv['rows']if x['kind']=='GAME_SAVE'];backups=[x for x in inv['rows']if x['kind']=='OFFLINE_BACKUP']
 assert len(current)==coverage['slots']==102 and len(backups)==coverage['offline_backups']==102 and len(parsed)==171
 checks.append('102 current slots plus102 retained backup references collapse to171 unique bodies')
 positive_counts={n:{'unique':sum(pos(p,n)for p in parsed.values()),'current':sum(pos(parsed[x['sha256']],n)for x in current)}for n in coverage['saved_positive_counts']}
 assert all(v=={'unique':coverage['saved_positive_counts'][n]['distinct_bodies'],'current':coverage['saved_positive_counts'][n]['game_slots']}for n,v in positive_counts.items())
 checks.append('selected saved-positive totals independently match coverage')
 cvi_nonpositive=[x for x in current if not pos(parsed[x['sha256']],'cvi_02_finished')]
 assert {x['slot_directory']for x in cvi_nonpositive}=={'EndGameSave-0','EndGameSave-1','EndGameSave-2'}
 assert all('q307'not in x['finished_quests']or x['metadata'].get('isPointOfNoReturn')for x in cvi_nonpositive)
 checks.append('only three current CVI nonpositive bodies are nonqualifying ending/PONR fixtures')
 conflicting=[{'body_sha256':k,'fact':n,'values':sorted(set(vals(p,n)))}for k,p in parsed.items()for n in p['facts']if len(set(vals(p,n)))>1]
 owner_types=collections.Counter(o['type']for p in parsed.values()for o in p['owner_surface'])
 journal_states={x['state']for p in parsed.values()for x in p['journal_raw_matches']}
 assert journal_states<= {'OPAQUE_NOT_DECODED'}
 checks.append('journal raw matches never promoted to decoded journal states')
 purchase=sorted({v for p in parsed.values()for v in vals(p,'carbought_counter')});assert purchase==coverage['purchases_observed_values']==[1]
 checks.append('serialized purchase counter evidence contains only value1, without runtime/entitlement inference')
 histories=[]
 for name in ('history_master_01.json','history_package_01.json'):
  data=read(Q/name);cache=next(json.loads(x['decoded_json'])for x in data['rows']if x['class']=='PTFR.HistorySnapshotHS1.SnapshotStateHS1')
  origin=cache['origin']['$value']['$value'];assert origin=='post_ending_fallback'
  histories.append({'path':name,'source_save_sha256':data['sha256'],'origin':origin})
 checks.append('selected saved HS1 caches explicitly originate after ending and are not earned-history certificates')
 queue=read(Q/'runtime_test_queue.json');assert queue['ready']==[]and queue['human_Brendan_history_answer']=='Don’t remember'
 checks.append('queue retains empty READY and user uncertainty, rather than inventing Brendan history')
 # Filename census only; do not read any additional save body.
 all_paths=subprocess.check_output(['rg','--files','-uu','-g','sav.dat'],cwd=W,text=True).splitlines()
 known={str(Path(x['source']).absolute()).lower()for x in inv['rows']if x['kind']=='OFFLINE_BACKUP'}|{str(Path(x['path']).absolute()).lower()for x in inv['excluded_backups']}
 omitted=[str(W/x)for x in all_paths if str((W/x).absolute()).lower()not in known]
 result={'status':'PASS_EXISTING_EVIDENCE_RECHECK','checks':checks,'unique_bodies':len(parsed),'current_slots':len(current),'retained_backups':len(backups),
  'positive_counts':positive_counts,'conflicting_selected_fact_rows':conflicting,'owner_types':dict(owner_types),
  'cvi_nonpositive':[{'slot':x['slot_directory'],'sha256':x['sha256'],'metadata':x['metadata']}for x in cvi_nonpositive],
  'selected_HS1':histories,'repo_sav_paths_not_in_inventory_or_explicit_exclusions':omitted,
  'limits':'Only existing JSON evidence and repository filenames rechecked; no save body parsed/read, game API called, DLL loaded or data modified. Empty READY is a conservative certification boundary, not proof that no fixture could exist.'}
 dest=H/'evidence_check_01.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print({'status':result['status'],'checks':len(checks),'conflicting_fact_rows':len(conflicting),'unaccounted_repo_sav_paths':len(omitted),'owner_types':dict(owner_types)})
if __name__=='__main__':main()
