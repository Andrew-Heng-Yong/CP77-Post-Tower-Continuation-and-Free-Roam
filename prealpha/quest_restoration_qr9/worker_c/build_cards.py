"""Render concise human cards from source-pinned QR8 scope and frozen QR9 tools.

Only fresh Worker C outputs are written. No game/save/CET/installer invocation.
"""
from pathlib import Path
import argparse,json,hashlib,csv,re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
STATUSES=['PASS','FAIL','NOT_TESTED','NOT_TESTABLE','INCONCLUSIVE']
CASES={
 'S00':['visible_smoke','registration_attempt','private_owner_activation'],
 'S01':['success','failure','muted_no_scene'],
 'S02':['ordinary_future','late_future_pre_gate','timer_reload_and_queue'],
 'S03':['prospective_positive','prospective_negative','already_issued'],
 'S04':['future_return','timer_reload'],
 'S05':['handoff_cleanup','cleanup_reload'],
 'S06':['unearned_containment','progressed_preservation'],
 'S07':['completed_history','old_entered_no_arm','old_native_pending_clock','missing_enrollment_or_contact','old_cvi_request'],
 'S08':['native_interrupt','permitted_stage_reload','completed_revisit']}

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def write(p,x):
 p=Path(p);assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main(out,integration):
 out=out.resolve();assert out.is_relative_to(HERE) and not out.exists();out.mkdir(parents=True)
 spec=read(HERE/'card_spec.json');tools=read(integration);pins=[];checks=[]
 def ck(n,v):checks.append({'check':n,'pass':bool(v)});assert v,n
 def pin(p,h=None):
  p=Path(p);actual=sha(p);ck('Pinned '+p.name,h is None or actual==h);pins.append({'path':str(p.resolve()),'sha256':actual});return p
 qr8=ROOT/'prealpha/quest_restoration_qr8';accepted=read(pin(qr8/'acceptance_tests.json'));ep=read(pin(qr8/'source_epoch_02.json',accepted['candidate_binding']['manifest_sha256']));sealed=read(pin(qr8/'completion.json'))
 ck('Exact canonical QR8:02 scope',ep['epoch_key']=='QR8:02' and sealed['canonical_epoch']['key']=='QR8:02' and sealed['canonical_epoch']['sha256']==accepted['candidate_binding']['manifest_sha256'] and spec['source_epoch']=='QR8:02')
 pin(HERE/'card_spec.json');pin(integration)
 ck('Frozen actual offline integration contract, no placeholders',tools['status']=='FROZEN_OFFLINE_VERIFIED_COMMAND_CONTRACT' and not tools.get('unresolved'))
 for p in tools['source_pins']:pin(p['path'],p['sha256'])
 dg=tools['diagnostics'];deploy=tools['deployment'];save=tools['working_save']
 ck('Diagnostics exact lowercase API',all(x in dg for x in ['start_template','stop','status','mark_template','duration_seconds','log_directory','collect_command','collect_command_template','coverage_limits']))
 ck('Start API accepts only fixed profile substitution','{profile}' in dg['start_template'] and dg['duration_seconds']==300)
 ck('Working-save procedure is reviewed and not assumed folder recognition',save['status']=='REVIEWED_USER_OPERATED_PROCEDURE' and save['recognized_copy_not_assumed'] is True)
 ck('No installation or game action executed by this guide',tools['game_launches']==0 and tools['deployments']==0 and tools['save_or_fact_writes_by_codex']==0)
 ck('Nine source checklist IDs preserved',[c['id'] for c in spec['cards']]==[t['id']for t in accepted['tests']])
 ck('Known finished CVI/Saints/Spy not presented as fresh fixtures',spec['known_master']['known_finished']==['sts_pac_cvi_02','sts_ep1_01','sts_ep1_08'] and 'already completed' in spec['cards'][1]['availability'] and 'already completed' in spec['cards'][2]['availability'])
 cards=[];results=[]
 for c in spec['cards']:
  ck(c['id']+' has six concrete card obligations',all(c.get(k)for k in ['requires','actions','visible','diagnostic','stop','return']))
  card=dict(c);card['capture_start']=dg['start_template'].format(profile=c['profile']);card['capture_stop']=dg['stop'];card['capture_status']=dg['status'];card['log_directory']=dg['log_directory'];card['collect_command']=dg['collect_command_template'].format(profile=c['profile'],run_id=c['id']+'_01');card['current_result']='NOT_TESTABLE'if c['id']=='S01'else'NOT_TESTED';card['gameplay_executed']=False;cards.append(card)
  ck(c['id']+' collection binds its own profile',('--card '+c['profile'])in card['collect_command'])
  for variant in CASES[c['id']]:
   results.append({'test_id':c['id'],'variant':variant,'status':'NOT_TESTED','fixture_availability':'UNCONFIRMED','working_save_label':None,'capture_run_ids':[],'visible_observation':None,'diagnostic_observation':None,'log_paths':[],'visual_evidence_paths':[],'limitations':[],'analysis_notes':None})
 # Fixture unavailability is a classification, never evidence of gameplay execution.
 for r in results:
  if r['test_id']=='S01':r['fixture_availability']='NOT_TESTABLE_ON_CONFIRMED_MASTER_ALREADY_COMPLETED';r['status']='NOT_TESTABLE';r['limitations']=['Scoped to selected ManualSave-23 completed CVI02 history; not unavailable on all possible genuine saves.']
 ck('Known unavailable S01 classified without any gameplay execution',all(r['status']==('NOT_TESTABLE'if r['test_id']=='S01'else'NOT_TESTED')for r in results))
 ck('Result vocabulary exactly matches human request',spec['common']['results']==STATUSES)
 write(out/'test_cards.json',{'schema':'ptfr.qr9.manual_cards.v1','binding':accepted['candidate_binding'],'known_master':spec['known_master'],'tools':tools,'common':spec['common'],'fixture_groups':spec['fixture_groups'],'static_holds':spec['static_holds'],'cards':cards,'gameplay_executed':False,'fixture_classification':'S01 NOT_TESTABLE on selected completed-CVI02 master; others NOT_TESTED','automation_used':False})
 write(out/'test_results_template.json',{'schema':'ptfr.qr9.runtime_results.v1','allowed_statuses':STATUSES,'binding':accepted['candidate_binding'],'status_rule':spec['common']['result_rule'],'observations':results})
 with(out/'test_results_template.csv').open('w',encoding='utf-8',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader()
  for r in results:w.writerow({k:json.dumps(v,ensure_ascii=False)if isinstance(v,list)else ''if v is None else v for k,v in r.items()})
 sections=['# QR9 manual test cards','Prepared only. Codex has not deployed, launched or controlled the game. Wait for explicit deployment authorization. Start with S00 only.','## Before playing']
 sections+=['- '+s for s in spec['common']['before_any_card']]
 sections+=['','Confirmed master: **ManualSave-23** (29 October,7:23 PM), user-declared genuine post-Tower lineage. It stays untouched. '+save['summary'],'','Reviewed save procedure: '+save['document'],'','Deployment/rollback procedure: '+deploy['document'],'','## Capture and return','The commands below are for the user to enter manually in CET, after approved installation. The default capture auto-stops after300 seconds; explicit stop is still safe.','',f'Status: `{dg["status"]}`. Variant marker, if useful: `'+dg['mark_template'].format(label='S02_ordinary_future')+'`.','', 'Logs: `'+dg['log_directory']+'`. After stopping and normal quit, use the exact collection command on the relevant card. This first example is **S00 only**:','', '```powershell',dg['collect_command'],'```','', 'Each listed collection command creates its first fresh Sxx_01 bundle. For a repeated card, request/use a new RunId such as Sxx_02 while keeping its --card profile unchanged; never overwrite a previous bundle.','',spec['common']['return'],'', 'No manual fact/node list is required. Screenshots only for a visual problem.']
 sections+=['- '+s for s in spec['common']['during_capture']]
 sections+=['','Stop rule: '+spec['common']['stop_rule'],'','## Cards']
 for c in cards:
  sections+=['','### '+c['id']+' — '+c['title'],'','**Fixture:** '+c['availability'],'','**Before:** '+' '.join(c['requires']),'','**Start:** `'+c['capture_start']+'`','']
  sections += [str(i+1)+'. '+a for i,a in enumerate(c['actions'])]
  sections += ['','**Visible:** '+' '.join(c['visible']),'','**Logs:** '+' '.join(c['diagnostic']),'','**Stop:** `'+c['capture_stop']+'`. '+c['stop'],'','**Collect after quit:**','```powershell',c['collect_command'],'```','', '**Return:** '+c['return'],'','**Branch:** '+c['branch_rule']]
 sections+=['','## Reuse or isolate a branch']+['- '+g['id']+': '+g['rule']for g in spec['fixture_groups']]
 sections+=['','## Limits carried forward']+['- '+s for s in spec['static_holds']]
 sections+=['','## Recording a result',spec['common']['result_rule'],'Use the JSON/CSV template or just send the brief observation and bundle; Codex can fill the technical fields. Unavailable prerequisites are not evidence of a gameplay defect.']
 (out/'MANUAL_TEST_CARDS.md').write_text('\n'.join(sections)+'\n',encoding='utf-8')
 first=cards[0];first_lines=['# First test — S00 only','Prepared only; wait for explicit deployment authorization and successful verification.','',save['summary'],'Read the reviewed working-save procedure: '+save['document'],'Keep original ManualSave-23 and its verified offline backup unchanged. Do not rename a copied folder and assume it is a recognized slot.','','## Bootstrap only if no native working slot exists','Follow the reviewed user-only backup procedure first. In game, load ManualSave-23 only for this bootstrap, then immediately use native Save Game → New Save. Never select overwrite23. Record the actual newly created native slot. If saving is unavailable, stop; no workaround.','Any bootstrap capture is a separate segment, not a disposable-startup PASS. Stop capture before deliberate reload. The later working-slot reload does not recreate the first registration attempt.','','## Short smoke on the native working slot','1. With capture stopped, return normally to the main menu. Enter `'+first['capture_start']+'` manually in CET.','2. Load only the identified native working slot.','3. Move normally and open/close the map for1–2 minutes. Accept no gig and overwrite no master.','4. Enter `'+first['capture_stop']+'`, then quit normally.','5. Collect the bundle using the reviewed command in MANUAL_TEST_CARDS.md. Send: working-slot label, loaded? control/map okay? unexpected quest/call/error?','6. Use the reviewed read-only verification to check original23 and backup after the run; if either changed, preserve the backup and stop. No automatic save restore.','','Logs: '+dg['log_directory'],'Early startup/numeric phase execution may remain unobserved. A receipt proves an attempt, not successful-owner activation.','Fresh CVI02/Saints/Spy are unavailable on this master; do not replay them. No generic Ana test is requested.']
 (out/'FIRST_TEST.md').write_text('\n'.join(first_lines)+'\n',encoding='utf-8')
 write(out/'verification.json',{'status':'PASS_OFFLINE_MANUAL_GUIDE_COMPLETENESS_NOT_GAMEPLAY','checks':checks,'checks_passed':len(checks),'cards':len(cards),'result_rows':len(results),'no_gameplay_executed':True,'status_counts':{s:sum(r['status']==s for r in results)for s in STATUSES},'source_pins':pins,'collector_executed':False,'game_launches':0,'deployments':0,'save_or_fact_writes':0,'code_sha256':sha(__file__)})
 print({'cards':len(cards),'result_rows':len(results),'checks':len(checks),'out':str(out)})

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--integration',type=Path,required=True);a=p.parse_args();main(a.output,a.integration)
