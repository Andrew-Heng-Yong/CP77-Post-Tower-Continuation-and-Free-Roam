"""Caller wait/clear, typed phone operations, scoped historical omissions and stock evidence."""
from pathlib import Path
import sys,copy,json,argparse,re
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
from common import read,write,sha,walk
from model import Resource
def run(O):
 assert not O.exists();tests=[];M=read(H/'inspection_01/models.json')|read(H/'phone_models_01.json');pins=read(H/'inspection_01/source_pins.json')+read(H/'phone_pins_01.json');rows=[];typed=[]
 def ck(k,v,e):
  tests.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e})
  if not v:write(O/'failed_tests.json',tests);raise AssertionError(k)
 # Every scene producer's native caller wait and actual reset owner, including native Janet's different protocol.
 p=read(H/'verification_03/phone_inventory.json')
 for z in p['producer_requests']:
  if z['graph']!='scene':continue
  g=M[z['depot']]['graphs']['scene'];done=z['request'][:-9].replace('audio_','holo_')+'_done';waits=[i for i,n in g['nodes'].items()if any(x.get('factName')==done for x in n['reads'])];clear=[i for i,n in g['nodes'].items()if any(x.get('factName')==done and x.get('value')==0 for x in n['writes'])];controller=z['contact'];scene=('base'if controller=='mr_hands'else'ep1')+'\\quest\\holocalls\\'+controller+'\\'+controller+'_holocall.scene';nativeclear=[i for i,n in M[scene]['graphs']['scene']['nodes'].items()if any(x.get('factName')==done and x.get('value')==0 for x in n['writes'])];row={'depot':z['depot'],'producer':z['node'],'request':z['request'],'native_waits':waits,'caller_clears':clear,'real_controller_clear_nodes':nativeclear};ck('actual caller wait/reset ownership '+z['depot']+'/'+z['node'],bool(waits)and(bool(clear)or(controller=='janet'and bool(nativeclear))),row);rows.append(row)
 special=[z for z in rows if not z['caller_clears']];ck('Janet caller protocol precisely scoped',len(special)==1 and special[0]['producer']=='1594'and special[0]['native_waits']==['1598']and'383'in special[0]['real_controller_clear_nodes'],'Original Janet start has no local caller clear; native holocall scene owns reset383. Do not invent a missing-clear fix from a generic template.')
 for d,m in M.items():
  if not d.startswith('ep1\\openworld\\street_stories')or not any(q in d for q in I.Q):continue
  for gp,g in m['graphs'].items():
   for i,n in g['nodes'].items():
    if n['sms']or any(re.search(r'Phone|CallContact|Holocall|SendMessage|AddRemoveContact',x.get('$type',''))for x in walk(n['payload'])):typed.append({'depot':d,'graph':gp,'node':i,'type':n['type'],'payload':n['payload'],'in':[e for e in g['edges']if e[2]==i],'out':[e for e in g['edges']if e[0]==i]})
 ck('all native typed phone operations inventoried',bool(typed)and not any(x.get('$type')in ['questCallContact_NodeType','questPhoneCall_NodeType']for z in typed for x in walk(z['payload'])),'Native own scope uses genuine journalSMS/contact, muted/restriction controls and fact-driven calls; no discarded direct custom CallContact producer')
 # Source inventory is not forced into all-facts coverage. Exact missing fields are preserved with their writer routes.
 admissions=read(H/'verification_03/admission.json');om=[]
 for q,z in admissions.items():
  for f,rr in z['omitted_native_facts'].items():
   ck('exact unlisted cleanup/debrief field provenance '+f,all(r['depot'].endswith(('_cleanup.questphase','_holocall_debrief.scene'))for r in rr),rr);om.append({'quest_id':q,'fact':f,'writers':rr,'status':'CONDITIONAL_HISTORY_FIELD_NOT_LISTED','limit':'Native start/journal/private receipts can protect normal paths, but no blanket arbitrary-save admission proof is made; no synthetic reset or expanded admission.'})
  for jp,rs in z['omitted_journals'].items():om.append({'quest_id':q,'path':jp,'references':rs,'status':'SOURCE_SCOPED_OMITTED_JOURNAL','classification':'Separate Spy loot/Steven followup, legacy alias/read-only objective or map pin; exact references retained, not assumed universally inactive.'})
 ck('unlisted cleanup fields remain visible',len([x for x in om if'fact'in x])==8,'1Dodger+4Spy+3Talent exact fields; not blanketPASS')
 # Existing stock capture, bounddepth and runtime override limitations remain explicit.
 stock=[]
 for q in I.Q:
  f=I.F/'shared/tdb_applicability_02'/str(q+'.json');z=read(f);pins.append({'path':str(f),'sha256':sha(f)});stock.append(z);rewards=[x for x in z['targets']if any(s.startswith('QuestRewards.'+q)for s in x['requested_aliases'])];ck('stock direct reward records '+q,bool(rewards)and all(x['exists_in_stock']for x in rewards),rewards)
 # Source-backed bugfix scopes and native diagnostics, not fresh speculative restoration.
 bugs=[{'depot':d,'root_prefabs':m['root_prefabs'],'graphs':m['graphs']}for d,m in M.items()if d.endswith('_bugfixing.questphase')and any(q in d for q in I.Q)]
 bd=next(d for d in M if d.endswith('sts_ep1_10_bugfixing.questphase'));bug=M[bd]['graphs']['root/6'];world='ep1\\openworld\\world_stories\\wst_ep1_11\\wst_ep1_11.questphase';wm,wp=I.load(world);pins.append(wp)
 ck('Dodger Bill gate monitor receipt is prearmed future wait',all(e in bug['edges']for e in [['2','False','3','In'],['3','Out','6','In'],['6','Out','11','In'],['11','Out','4','In']]),'Native CP77-54247 is set before Billdefault wait. No new bypass/reset is justified merely from this pattern.')
 ck('native Bill world already owns same gate open/unpower',all(wm['graphs']['root']['nodes'][str(i)]['payload']['type']['params'][0]['deviceAction']['$value']==a for i,a in [(57,'ForceOpen'),(58,'ForceUnpower')]),'Exact source duplicate support actions exist in the owned Bill world story; avoids promoting a missing future-monitor hypothesis without a genuine uncovered route.')
 # Two additional actual raw faults in caller wait and PH3 scope.
 mutations=[]
 target=next(x for x in read(H/'readback_01/manifest.json')if x['depot'].endswith('sts_ep1_08_target_meeting.scene'));r=copy.deepcopy(read(target['json']));changed=0
 for x in walk(r):
  if x.get('factName')=='holo_mark_bana_calls_v_start_done'and x.get('$type')=='questVarComparison_ConditionType':x['factName']='QR5_missing_caller_wait';changed+=1
 mm=Resource(r).normalize();ck('actual raw missing Mark caller wait',changed>0 and not any(x.get('factName')=='holo_mark_bana_calls_v_start_done'for x in mm['graphs']['scene']['nodes']['1560']['reads']),'Organitopia waits actual Mark start ACK, not generic source-presence')
 write(O/'mutated_caller.json',r);mutations.append({'fault':'Missing_Mark_native_caller_wait','path':str(O/'mutated_caller.json'),'sha256':sha(O/'mutated_caller.json')})
 st=next(x for x in read(H/'readback_01/manifest.json')if x['depot'].endswith('studio_support.questphase'));r=copy.deepcopy(read(st['json']));zz=Resource(r);gg=zz.d(zz.root['graph']);nn=next(zz.d(h)for h in gg['nodes']if zz.d(h)['id']==3);nn['phaseInstancePrefabs']=[];mm=Resource(r).normalize();ck('actual raw missing shared studios',not mm['graphs']['root']['nodes']['3']['prefabs']and len(M[st['depot']]['graphs']['root']['nodes']['3']['prefabs'])==2,'PH3 shared PIP regression, not an empty-root shortcut');write(O/'mutated_studio.json',r);mutations.append({'fault':'Missing_PH3_native_studios','path':str(O/'mutated_studio.json'),'sha256':sha(O/'mutated_studio.json')})
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'caller_protocols.json',rows);write(O/'typed_phone_actions.json',typed);write(O/'explicit_omissions.json',om);write(O/'stock_applicability.json',stock);write(O/'bugfix_scopes.json',bugs);write(O/'mutations.json',mutations);summary={'status':'PASS_SCOPED_CALLER_AND_DEPENDENCY_CONTROLS_WITH_VISIBLE_LIMITS','checks':len(tests),'mutations':2,'caller_scene_producers':len(rows),'typed_phone_nodes':len(typed),'fully_static_verified':False,'runtime_changes':[]};write(O/'summary.json',summary);print(json.dumps(summary))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);run(Path(ap.parse_args().output).resolve())
