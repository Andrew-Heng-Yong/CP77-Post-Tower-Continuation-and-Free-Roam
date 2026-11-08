"""Bounded final-source applicability review; reuses attributed actual fixtures."""
from pathlib import Path
import argparse,json,hashlib,difflib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OLD='C8EE599B3898E4A7C28B5E4FA51D1B768D7EA53C24B7913AC0213B1D9F64DD7A'
FINAL='CE020172988081100199A35C9FAA9131444DB4DED52893480F2BA746EFFDA39E'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def main(out):
 out=out.resolve();assert out.is_relative_to(HERE)and not out.exists();out.mkdir(parents=True);checks=[];pins=[]
 def ck(n,v,e=None):checks.append({'check':n,'pass':bool(v),'evidence':e});assert v,n
 def pin(p,h=None):
  p=Path(p);actual=sha(p);ck('Exact pin '+p.name,h is None or actual==h);pins.append({'path':str(p),'sha256':actual});return p
 a=ROOT/'prealpha/quest_restoration_qr9/worker_a';old=pin(HERE/'reviews/installer_01/deploy_qr9_guarded.ps1',OLD);final=pin(a/'deploy_qr9_guarded_final.ps1',FINAL);pin(a/'deploy_qr9_guarded.ps1',FINAL)
 prior=read(pin(HERE/'reviews/installer_01/review.json'));ck('Four independent actual synthetic scenarios passed on attributed C8EE source',prior['source_sha256']==OLD and prior['checks_passed']==84 and len(prior['cases'])==4 and all(x['result']=='PASS'for x in prior['cases']))
 ck('All independent subprocess calls explicitly used C fixture roots',all('-FixtureRoot'in x['argv']and str(HERE)in x['argv'][x['argv'].index('-FixtureRoot')+1]for x in prior['commands']))
 before=old.read_text(encoding='utf-8-sig').splitlines();after=final.read_text(encoding='utf-8-sig').splitlines();ops=difflib.SequenceMatcher(a=before,b=after,autojunk=False).get_opcodes();added=[];delta=[]
 for tag,i,j,k,l in ops:
  if tag=='equal':continue
  ck('Final successor preserves every old source line',tag=='insert');added+=after[k:l];delta.append({'kind':tag,'old_line':i+1,'new_line':k+1,'inserted':after[k:l]})
 ck('Final delta is exactly enum+Recover+outer-finally guards',len(added)==6 and any(x.startswith(' if($j.operation -notin')for x in added)and any('Recover requires an interrupted transaction' in x for x in added)and 'try {'in added and '} finally {'in added and any('$script:transactionLock.Dispose()'in x for x in added)and added[-1]=='}')
 text=final.read_text(encoding='utf-8-sig');ck('Stable mutation lock independent of recovery path',"$lockRoot=if($fixture){$FixtureRoot}else{$worker}"in text and '[IO.FileShare]::None'in text and "Unexpected installer lock contents"in text)
 mainbody=text.split('# Resolve real paths only from the pinned manifest.',1)[1];ck('Fresh closed-game/package/dependency/managed checks follow lock acquisition',mainbody.index('LockMutations')<mainbody.index("CheckPackage;CheckDependencies 'After';CheckManaged 'Before'")and 'LockMutations\nClosed'in mainbody)
 ck('Recover committed states refused, incomplete states explicitly allowed',"$script:journal.state -notin @('PREPARING','PREPARED','APPLYING','ROLLING_BACK','RECOVERY_REQUIRED')"in text)
 ck('No automatic process close or launch',all(s not in text for s in ['Stop-Process','Start-Process','taskkill','SaveGame(']))
 ck('Unknown files and saves never restored by recovery',"Unknown mixed target requires manual review"in text and "saves were not restored or edited"in text and "Original ManualSave-23 must remain intact"in text)
 core=read(pin(a/'core_manifest_02.json','06CD479C47E32403371E360092648431EAE1BC93DEE3E61BD6822560133CBCF1'));diag=read(pin(a/'diagnostics_manifest_01.json','C41A1547DB7B33F0F97B68ADC7509E937A6487B85D95E34F7AAFBF83991C38E1'));bm=read(pin(ROOT/'prealpha/quest_restoration_qr9/worker_b/addon_manifest_04.json'))
 ck('Core exact51/two existing replacements',len(core['files'])==51 and len([r for r in core['files']if r['before']!=r['after']])==2 and set(core['changing_paths'])=={'archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl'})
 ck('Addon separately pins exact B04 two absent paths',len(diag['files'])==2 and all(r['before']is None for r in diag['files'])and {r['path']:r['after']for r in diag['files']}=={r['path']:r['sha256']for r in bm['files']})
 ck('Master backup explicitly outside Saved Games and never automatically restored',core['master_backup']['slot']=='ManualSave-23'and len(core['master_backup']['files'])==3 and 'No Saved Games writes'in core['master_backup']['policy']and 'never automatically restored'in core['master_backup']['policy'])
 history=read(pin(a/'fixture_result_02.json'));guarded=read(pin(a/'final_fixture_result_01.json'));actual=read(pin(a/'exact_payload_result_01.json'));receipt=read(pin(a/'receipt_guards_result_01.json','12F1C18EB08FCC6B87137A03627A06FCF39D19D6F94FCA0F04205B62B40D4D73'))
 ck('Historical29 tests remain correctly attributed',history['cases']==29 and history['status']=='PASS_WORKSPACE_ONLY_TRANSACTION_FIXTURES'and history['script_sha256']!=FINAL)
 ck('C8EE7 affected-path/lock tests remain correctly attributed',guarded['script_sha256']==OLD and guarded['cases']==7 and all(r['status']=='PASS'for r in guarded['results']))
 ck('Different-recovery contention and post-lock drift were exercised',{'different_recovery_contention','post_lock_dependency_drift'}<={x['case']for x in guarded['results']})
 ck('Actual51/2 workspace payload tests attributed to C8EE, not final rerun',actual['script_sha256']==OLD and actual['status']=='PASS_ACTUAL_CORE51_AND_ADDON2_WORKSPACE_TRANSACTIONS')
 ck('Final exact CE020 receipt/disposal focused tests passed',receipt['script_sha256']==FINAL and receipt['status']=='PASS_RECEIPT_BOUNDARIES_AND_EXPLICIT_LOCK_DISPOSAL'and len(receipt['cases'])==4 and not receipt['errors'])
 ck('Final fixture gate recorded no real game/save calls',receipt['real_game_calls']==0 and receipt['real_save_calls']==0)
 result={'status':'APPROVE_FROZEN_OFFLINE_INSTALLER_WITH_EXPLICIT_AUTHORIZATION_AND_RUNTIME_LIMITS','source_sha256':FINAL,'checks':checks,'checks_passed':len(checks),'independent_fixture_evidence':{'path':str(HERE/'reviews/installer_01/review.json'),'source_sha256':OLD,'checks':84,'cases':4},'final_source_delta':delta,'scope_rule':'C8EE actual transaction controls apply to byte-preserved behavior. Final CE020 added only enum/Recover/finally guards, directly exercised by A exact-final focused fixtures. No historical/full-suite run is falsely attributed to final bytes.','source_pins':pins,'real_installer_preflight':'NOT_RUN','real_install_rollback_recover':'NOT_RUN','real_game_save_fact_writes':0,'remaining_limits':['Independent read-only preparation checker is separate from a real installer Preflight. Actual permissions are unexercised.','No gameplay or native New Save bootstrap has run. No arbitrary save/update compatibility certification.','Only the user may execute the reviewed commands after explicit authorization. Preserve journals/backups; rollback does not undo persisted owners/rewards.'],'code_sha256':sha(__file__)}
 (out/'review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print({'checks':len(checks),'review':str(out/'review.json'),'source':FINAL})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
