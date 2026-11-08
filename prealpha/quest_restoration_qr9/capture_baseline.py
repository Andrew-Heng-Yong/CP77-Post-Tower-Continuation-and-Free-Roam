"""One shared read-only QR9 baseline. No save copy, CUA or game operation."""
from pathlib import Path
import sys,copy,shutil,datetime,subprocess,hashlib,zipfile,concurrent.futures
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;P=W/'prealpha/quest_restoration_qr8'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,tree_metadata
assert not(O/'baseline.json').exists(),'Fresh QR9 baseline only'
c=read(P/'completion.json');assert sha(P/'completion.json')=='16DEB2A65C02FB3A10FF5AB659764B69C0F7DCC3BFFD9EF276BA02273DCCDFD1'
assert c['status']=='QR8_COMPLETE_STATIC_INTEGRATION_WITH_LIMITED_CONTROLLED_TEST_READINESS'
assert all(sha(r['path'])==r['sha256']for r in c['artifacts'].values())
ep=P/'source_epoch_02.json';e=read(ep);C=Path(e['candidate']);pm=read(C/'package_manifest.json')
assert sha(ep)==c['canonical_epoch']['sha256']
actual={str(f.relative_to(C/'archive_source')):sha(f)for f in(C/'archive_source').rglob('*')if f.is_file()};assert actual==e['source_resources']
assert all(sha(C/'package'/r['path'])==r['sha256']for r in e['package_files'])
assert sha(pm['zip'])==pm['zip_sha256']==c['zip_sha256']
with zipfile.ZipFile(pm['zip'])as z:
 assert z.testzip()is None and len(z.infolist())==len(e['package_files'])and len(z.namelist())==len(set(z.namelist()))
 for r in e['package_files']:assert hashlib.sha256(z.read(r['path'].replace('\\','/'))).hexdigest().upper()==r['sha256']
impath=W/'prealpha/phone_studios_ph3/candidate_01/install_manifest_01.json';im=read(impath);game=Path(im['game_root']);oldrows={r['path'].replace('\\','/'):r for r in im['package_files']};core=[]
for r in e['package_files']:
 rel=r['path'].replace('\\','/');before=oldrows[rel]['after'];assert sha(game/rel)==before
 core.append({'path':rel,'before':before,'after':r['sha256'],'bytes':r['bytes'],'changing':before!=r['sha256']})
changing=[r['path']for r in core if r['changing']];assert set(changing)=={'archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl'}
old=read(P/'protection_before.json');save=Path(old['save_root']);files=sorted(set([Path(p)for p in old['files']]+[f for f in P.rglob('*')if f.is_file()]))
def pin(f):
 if not f.is_file()or f.is_symlink():return str(f),None
 s=f.stat();return str(f),{'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'sha256':sha(f)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:pins={p:v for p,v in pool.map(pin,files)if v}
drift=[{'path':p,'QR8_start':v,'QR9_start':pins.get(p)}for p,v in old['files'].items()if p not in pins or pins[p]['sha256']!=v['sha256']]
assert all(Path(x['path']).is_relative_to(game)or Path(x['path']).is_relative_to(save)for x in drift),'Immutable predecessor/workspace drift'
write(O/'external_drift_since_QR8.json',{'status':'CURRENT_EXTERNAL_STATE_PINNED_NEVER_REVERTED','changes':drift})
save_meta=tree_metadata(save);game_meta=tree_metadata(game)
write(O/'protection_before.json',{'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':pins,'game_metadata':game_meta,'save_root':str(save),'save_metadata':save_meta})
external_rel=['archive/pc/mod/LizziesBDs.archive','red4ext/plugins/ArchiveXL/ArchiveXL.dll','red4ext/plugins/Codeware/Codeware.dll','red4ext/plugins/TweakXL/TweakXL.dll','bin/x64/plugins/cyber_engine_tweaks.asi','r6/scripts/virtual-atelier-full/SetupNewTab.reds']
externals=[]
for rel in external_rel:
 f=game/rel;assert f.is_file(),f;externals.append({'path':rel,'sha256':sha(f),'bytes':f.stat().st_size})
assert next(r['sha256']for r in externals if r['path'].endswith('SetupNewTab.reds'))=='5743CDCD6F8CD46A58F9642002F75EBCA25D84BE340856C2E6D85B15DAD973F8'
inventory=[]
for folder in sorted(save.iterdir()):
 mp=folder/'metadata.9.json'
 if not folder.is_dir()or not mp.is_file():continue
 md=read(mp)['Data']['metadata'];finished=set(md.get('finishedQuests','').split())
 inventory.append({'directory':folder.name,'metadata':str(mp),'metadata_sha256':sha(mp),'timestamp':md.get('timestampString'),'game_version':md.get('gameVersion'),'build_patch':md.get('buildPatch'),'is_PONR':md.get('isPointOfNoReturn'),'is_end_game':md.get('isEndGameSave'),'tracked_entry':md.get('trackedQuestEntry'),'player_position':md.get('playerPosition'),'q307_in_finished_list':'q307'in finished,'relevant_finished_quests':sorted(finished&{'sts_pac_cvi_02','sts_ep1_01','sts_ep1_03','sts_ep1_08','sts_ep1_12','mq007','mq030','mq037','mq060'}),'scope':'Metadata only; q307/name/absence is not executing-owner, full history or genuine ending proof. No sav.dat parsing.'})
write(O/'save_metadata_inventory.json',{'status':'READ_ONLY_METADATA_INVENTORY','rows':inventory,'selected_master':'ManualSave-23','lineage_evidence':'User explicitly selected this known genuine Tower-completion save in QR9 reply. Metadata is corroboration only.','save_copies_or_writes':0})
master=save/'ManualSave-23';assert master.is_dir()
write(O/'selected_master.json',{'status':'USER_SELECTED_GENUINE_TOWER_MASTER_KEEP_UNTOUCHED','path':str(master),'files':{f.name:{'sha256':sha(f),'bytes':f.stat().st_size}for f in master.iterdir()if f.is_file()},'user_reply':'ManualSave-23 — 29 Oct, 7:23 PM','metadata_only_notes':'CVI02/Saints/Spy appear completed; fresh tests for those are NOT_TESTABLE on this fixture. Missing other names do not prove fresh eligibility.','disposable_copy':'NOT_CREATED_OR_MODIFIED_BY_CODEX; user-operated safe preparation required.','save_body_parsed':False})
git=['git','-c','safe.directory='+str(W).replace('\\','/')]
write(O/'workspace_before.json',{'cwd':str(W),'branch':subprocess.check_output(git+['branch','--show-current'],cwd=W,text=True).strip(),'head':subprocess.check_output(git+['rev-parse','HEAD'],cwd=W,text=True).strip(),'status':subprocess.check_output(git+['status','--short'],cwd=W,text=True),'tracked_diff_sha256':hashlib.sha256(subprocess.check_output(git+['diff','--binary'],cwd=W)).hexdigest().upper()})
baseline={'schema':1,'status':'PASS_EXACT_QR8_CORE_SOURCE_PACKAGE_AND_INSTALLED_PH3','workspace_root':str(W),'game_root':str(game),'save_root':str(save),'core_candidate':str(C),'package_root':str(C/'package'),'source_epoch':{'path':str(ep),'sha256':sha(ep),'key':'QR8:02'},'parent_completion':{'path':str(P/'completion.json'),'sha256':sha(P/'completion.json')},'package_manifest':{'path':str(C/'package_manifest.json'),'sha256':sha(C/'package_manifest.json')},'zip':pm['zip'],'zip_sha256':pm['zip_sha256'],'source_payloads':len(actual),'core_files':core,'changing_paths':changing,'external_dependencies':externals,'protected_state':{'path':str(O/'protection_before.json'),'sha256':sha(O/'protection_before.json'),'files':len(pins)},'selected_master':{'path':str(O/'selected_master.json'),'sha256':sha(O/'selected_master.json')},'external_drift_since_QR8':len(drift),'core_runtime_or_package_changes':0,'deployment_authorized':False,'CUA_or_game_interaction_authorized':False,'future_save_policy':'Future user-operated installer snapshots then-current saves read-only before/after its transaction; never restores them or requires old prep-date progress. Existing core/external dependency hash drift still refuses.'}
write(O/'baseline.json',baseline);write(O/'prepared.json',{'game':str(game),'save_root':str(save),'candidate':str(C),'scope':'QR9 offline installer/diagnostics/manual-test preparation. No CUA, GUI, auto gameplay, game launch, real install/rollback, saves/facts or release/Git publication.'})
shutil.copyfile(Path(r'C:\Users\Ayong\.codex\attachments\5930ee1d-f67c-42fb-adc7-ecb46528af71\Pasted text.txt'),O/'REQUEST.md')
write(O/'checkpoint.json',{'state':'QR9_OFFLINE_PREPARATION_THREE_WORKERS_ACTIVE','source':'QR8:02 unchanged','baseline_sha256':sha(O/'baseline.json'),'selected_master':'ManualSave-23 user-confirmed, untouched','next_action':'Fixture-test guarded deployment and read-only diagnostic addon; prove safe user copy/load procedure; crossreview and provide one initial card, then stop before real installation.','deployment_authorized':False,'game_launches':0,'save_writes':0,'CUA_calls':0})
print({'status':baseline['status'],'source_payloads':len(actual),'core_paths':len(core),'changing_paths':len(changing),'protected_hashes':len(pins),'preexisting_external_changes':len(drift),'master':'ManualSave-23'})
