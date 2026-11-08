"""Prepare the two-file optional addon and pinned read-only signal catalogue.
Run once in fresh QR9 worker output; no game/deployment/runtime calls.
"""
from pathlib import Path
import sys,json,hashlib,re,datetime
W=Path(__file__).resolve().parents[3];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from model import Resource
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest().upper()
def save(p,v):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def uniq(xs):return sorted(set(xs))
def main():
 addon=H/'addon';prefix='bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics';dest=addon/prefix
 if (dest/'watch.json').exists()or(H/'addon_manifest.json').exists():raise RuntimeError('Fresh configuration output required')
 pins=read(H/'resource_readbacks_01/manifest.json');models={};catalog={}
 for p in pins:
  assert sha(p['raw'])==p['raw_sha256']and sha(p['json'])==p['json_sha256'];m=Resource(read(p['json'])).normalize();assert not m['errors'];models[p['depot'].split('\\')[-1]]=m
  for gp,g in m['graphs'].items():
   for i,n in g['nodes'].items():
    for mode in('reads','writes'):
     for f in n[mode]:
      if 'factName'in f:catalog.setdefault(f['factName'],[]).append({'depot':p['depot'],'raw_sha256':p['raw_sha256'],'graph':gp,'node':i,'access':mode,'operation':f})
 allfacts=set(catalog);core='PostTowerFreeRoamActive PTFRP0_DR13 q307_active q307_done q307_finished q307_2079 q307_main_game_killed q307_ep1_killed q115_point_of_no_return q305_johnny_scene_active PTFRU9_Support_Issued PTFRU9_Support_Fault'.split()
 def facts(m):return {f['factName']for g in models[m]['graphs'].values()for n in g['nodes'].values()for f in n['reads']+n['writes']if'factName'in f}
 cvi=facts('sts_pac_cvi_02_entry.questphase');ron=facts('ronald_news_future.questphase');ni=facts('mq060_nitro.questphase');sk=facts('mq007_smartgun.questphase')|facts('mq007_resume_boot.questphase');me=facts('mq030.questphase');br=facts('mq037.questphase')
 cv={n for n in cvi if n.startswith(('PTFRQR7_CVI02','PTFRU9_sts_pac_cvi_02','new_','holo_mr_hands'))or n in('cvi_02_start','cvi_02_finished','ep1_installed')}
 rn=ron|{n for n in allfacts if n.startswith('PTFRU9_sts_ep1_')and n.endswith(('Started','OwnerFinished','MainFinished'))}
 specs={
 'S00':set(core)|set('PTFRQR7_RonaldNews_Issued PTFRQR7_RonaldNews_Retired PTFRQR7_CVI02_CustomControllerIssued q302_ronald_messages_enabled cvi_02_finished'.split()),
 'S01':set(core)|cv,
 'S02':set(core)|rn,
 'S03':set(core)|{n for n in ni if n.startswith(('mq060_','PTFRS29_mq060_'))or n=='carbought_counter'},
 'S04':set(core)|{n for n in sk if n.startswith(('PTFRQR4_MQ007','PTFRS23_MQ007'))or n in('mq007_done','mq007_opt_A','mq007_skippy_owner_known','mq007_skippy_re_acquiring_done')},
 'S05':set(core)|{n for n in me if n.startswith(('mq030_','PTFRS23_MQ030','PTFRB0ZAN'))or n=='cct_dtn_cloth_01_default_on'},
 'S06':set(core)|{n for n in br if n.startswith(('mq037_','PTFRS23_MQ037'))or n=='hey_rey_techstore_01_default_on'},
 'S07':set(core)|cv|ron,
 'S08':set(core)|cv|rn}
 cat=read(W/'research/gig_restoration/lore_whitelists_v6_2_sidejobs.json');jp={r['id']:r.get('journal_path')for r in cat['decision_registry']}
 def j(path,cl='gameJournalQuest'):return {'path':path,'class':cl}
 tower=j('ep1/quests/main_quest/q307_before_tomorrow');contact=j('ep1/contacts/ronald','gameJournalContact')
 journals={'S00':[tower,contact],'S01':[tower,j(jp['sts_pac_cvi_02'])],'S02':[contact]+[j(jp['sts_ep1_'+c])for c in('01','03','08','12')],
 'S03':[j('quests/minor_quest/mq060_nitro')],'S04':[j('quests/minor_quest/mq007_smartgun')],'S05':[j('quests/minor_quest/mq030_melisa')],'S06':[j('quests/minor_quest/'+p)for p in('mq037_brendan','mq037_brendan_dumpster','mq037_brendan_hooligan001')]}
 journals['S07']=journals['S01']+journals['S02'];journals['S08']=journals['S07']
 assert all(0<len(v)<=96 and v<=allfacts for v in specs.values())
 rows={k:{'facts':uniq(v),'journals':journals[k],'description':'Bounded signal observations for '+k+'; no automatic graph/ownership/eligibility proof'}for k,v in specs.items()}
 cet=W.parent # actual static input below; never loaded as a DLL
 cet=Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/bin/x64/plugins/cyber_engine_tweaks.asi');cetbytes=cet.read_bytes()
 source_catalog=H/'signal_catalog.json';save(source_catalog,{'status':'SOURCE_PINNED_SIGNALS_NOT_EXECUTION_PROBES','source_epoch':'QR8:02','inputs':pins,'facts':catalog,'journal_identity_source':{'path':str(W/'research/gig_restoration/lore_whitelists_v6_2_sidejobs.json'),'sha256':sha(W/'research/gig_restoration/lore_whitelists_v6_2_sidejobs.json')},'signal_semantics':'A named receipt/request/ACK/cleanup fact has an authored source role; its observed value or callback is not an executing graph/node/controller query.'})
 cfg={'schema':1,'module':'PTFR_QR9_Diagnostics','version':'QR9B01','declared_build':{'source_lua_sha256':sha(dest/'init.lua'),'signal_catalog_sha256':sha(source_catalog),'core_epoch':'QR8:02','core_manifest_sha256':sha(W/'prealpha/quest_restoration_qr8/source_epoch_02.json'),'core_archive_sha256':'2AB35CC95931CD3C7BB2FB3A4C8B52746DE7847D42AE1DD3503A90A965FD2039','CET_expected_sha256':sha(cet)},'profiles':rows}
 save(dest/'watch.json',cfg)
 save(H/'api_proof.json',{'status':'LOCAL_API_SURFACE_AND_KNOWN_PATTERN_VERIFIED_RUNTIME_NOT_RUN','CET':{'path':str(cet),'sha256':sha(cet),'bytes':len(cetbytes),'literal_export_names':{n:cetbytes.count(n.encode()+b'\0')for n in['GetMod','NewProxy','registerForEvent','onUpdate','onShutdown','ObserveBefore']},'version_observation':'Existing CET log1.38.0 [HEAD], not asserted equal to upstream source.'},'local_sources':[{'path':str(W/p),'sha256':sha(W/p)}for p in['diagnostics/PTFR_Afterlife_TriggerAudit/init.lua','tools/test_afterlife_trigger_audit.py','diagnostics/PTFR_Phase2B_P0/init.lua','prealpha/quest_restoration_qr8/candidate_01/package/bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/init.lua','prealpha/quest_restoration_qr8/candidate_01/package/r6/scripts/PTFR_Consolidated/PTFR_ActivityStateR3.reds']], 'API_support':{'GetMod':'Known CET export literal and installed mod return-api convention. Directory name must remain exact. No external dofile loader.','NewProxy/RegisterListener/UnregisterListener':'Existing local event-only observer pattern and historical runtime logger; Int32 proxy callbacks, explicit listener IDs. Calls guarded/fail closed; runtime callback delivery and cleanup not certified by source.','onInit/onUpdate/onShutdown':'Known local CET event convention, current ASI export strings. onUpdate only timer plus at most2-second session/journal/phone state checks while user capture active. No fact polling fallback.','PlayerPuppet.OnDetach':'Existing historical local ObserveBefore pattern. Registration request is not proof of hook delivery; guarded fallback detects only observed attached/pregame/entity changes. Stop before deliberate reload.','journal':'Current compiled REDS uses GameInstance.GetJournalManager/GetEntryByString/GetEntryState. Lua exposure/read success not executed; per-field errors and NOT_OBSERVED retained.','phone':'Current compiled REDS calls PhoneManager.IsPhoneCallActive. Getter says reported phone state, not actual audio/callback/controller identity.','actual graph/engine receipt/queue/clock/saveID':'No supported Lua getter bound here. Always NOT_OBSERVED; source signals are not substituted.'},'upstream_corroboration':{'url':'https://github.com/maximegmd/CyberEngineTweaks/blob/master/src/scripting/Scripting.cpp','meaning':'Official source NewProxy/Observe export names corroborate known pattern; not binary equivalence to installed HEAD.'},'actual_game_API_calls_in_preparation':0})
 save(H/'addon_manifest.json',{'schema':1,'status':'OPTIONAL_DIAGNOSTIC_PREPARED_NOT_DEPLOYED','source_root':str(addon),'core_package_unchanged':True,'core_epoch':'QR8:02','files':[{'path':prefix+'/'+n,'sha256':sha(dest/n),'bytes':(dest/n).stat().st_size,'before':'ABSENT_REQUIRED'}for n in('init.lua','watch.json')],'dependencies':[{'path':'bin/x64/plugins/cyber_engine_tweaks.asi','sha256':sha(cet),'scope':'Pinned existing CET, not installed/updated by addon'}],'runtime_log_pattern':prefix+'/QR9_capture_*.jsonl','rollback_scope':'Only exact unchanged two managed addon files may be removed; preserve generated logs, unknown files and directory. No recursive delete. No core51 changes.','default_duration_s':300,'maximum_duration_s':900,'maximum_rows':2048,'maximum_bytes':8388608,'runtime_calls':0,'game_writes':0,'save_writes':0})
 print('Two-file addon prepared', {k:len(v['facts'])for k,v in rows.items()})
if __name__=='__main__':main()
