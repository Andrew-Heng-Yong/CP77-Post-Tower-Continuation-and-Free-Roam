"""Freeze and assess the human S05 replay. Read-only originals, workspace outputs."""
from pathlib import Path
import collections,datetime,hashlib,json,re,stat,subprocess
H=Path(__file__).resolve().parent
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
SAVE=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
PS=r'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(data):return hashlib.sha256(data).hexdigest().upper()
def sha(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def safe(p):
    for q in(p,*p.parents):
        s=q.lstat();assert not stat.S_ISLNK(s.st_mode)and not(getattr(s,'st_file_attributes',0)&0x400),'Linked input refused'
def snapshot(p,limit):
    safe(p);before=p.stat();assert before.st_size<=limit,'Bounded input exceeded'
    raw=p.read_bytes();after=p.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'Input changed during collection'
    return raw
def main():
    running=subprocess.check_output([PS,'-NoProfile','-Command','Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -in @("Cyberpunk2077","REDlauncher","REDprelauncher") } | ForEach-Object { $_.ProcessName }'],text=True).splitlines()
    assert not running,'Game/launcher must already be closed; collector never closes them'
    out=H/'observations/jinguji_replay_01';assert not out.exists();out.mkdir(parents=True)
    inputs=[]
    def copy(p,name,limit=8388608):
        raw=snapshot(p,limit);dest=out/name;dest.write_bytes(raw);assert sha(dest)==digest(raw)
        inputs.append({'source':str(p),'copy':str(dest),'sha256':digest(raw),'bytes':len(raw)});return raw
    root=GAME/'bin/x64/plugins/cyber_engine_tweaks';diag=root/'mods/PTFR_QR9_Diagnostics'
    name='QR10_capture_20261103T182153Z_0001.jsonl'
    raw=copy(diag/name,name)
    rows=[json.loads(line)for line in raw.decode('utf-8-sig').splitlines()if line.strip()]
    assert rows and len(rows)<=2048
    for index,row in enumerate(rows,1):
        assert row['seq']==index and row['schema']==2 and row['module']=='PTFR_QR9_Diagnostics'and row['profile']=='S05'
        assert row['run_id']==name and row['user_label']=='QR12-Jinguji-Replay'
    def events(n):return [r for r in rows if r['event']==n]
    assert len(events('CAPTURE_START'))==len(events('ATTACHED_BASELINE'))==len(events('STOP'))==len(events('CAPTURE_CLEANUP'))==1
    assert rows[0]['event']=='CAPTURE_START'and rows[-1]['event']=='CAPTURE_CLEANUP'
    assert events('CAPTURE_START')[0]['data']['version']=='QR10D01'
    assert len(events('NATIVE_CALLBACK_UNAVAILABLE'))==1 and not events('FACT_DELIVERY')
    watch=read(diag/'watch.json');names=watch['profiles']['S05']['facts'];assert len(names)==32
    assert events('CAPTURE_START')[0]['data']['watch_facts']==names
    latest=dict(events('ATTACHED_BASELINE')[0]['data']['facts']);assert set(latest)==set(names)
    changes=events('FACT_SAMPLE_CHANGE')
    for row in changes:
        d=row['data'];assert d['fact']in names and latest[d['fact']]==d['previous_sample'] and d['current_sample']!=d['previous_sample']
        assert isinstance(d['current_sample'],int)and not isinstance(d['current_sample'],bool)and -2147483648<=d['current_sample']<=2147483647
        latest[d['fact']]=d['current_sample']
    stop=events('STOP')[0];metrics=stop['data'];assert metrics['sampled_changes']==len(changes)
    assert metrics['fact_getter_calls']==len(names)*(metrics['sample_rounds']+1)
    errors=[r for r in rows if r['event']in ['FACT_SAMPLE_ERROR','FACT_READ_FAILED','API_UNAVAILABLE']or r['data'].get('errors')]
    assert not errors
    start_utc=datetime.datetime.fromisoformat(rows[0]['utc']);stop_utc=datetime.datetime.fromisoformat(stop['utc'])
    broad=copy(root/'scripting.log','CET_scripting.log').decode('utf-8-sig',errors='replace')
    copy(root/'cyber_engine_tweaks.log','CET_framework.log')
    copy(root/'gamelog.log','CET_gamelog.log')
    timeline=[];writes=[]
    for num,line in enumerate(broad.splitlines(),1):
        timestamp=re.match(r'^\[([0-9-]+ [0-9:]+) UTC([+-][0-9:]+)\]',line)
        if not timestamp:continue
        t=datetime.datetime.fromisoformat(timestamp[1]+timestamp[2]);utc=t.astimezone(datetime.timezone.utc)
        if utc<start_utc-datetime.timedelta(seconds=30):continue
        fact=re.search(r': ([A-Za-z0-9_]+) : (-?\d+) -> (-?\d+)\s*$',line)
        relevant=(fact and(fact[1]in names or fact[1].startswith('mq030_')))or any(s in line for s in ['[PTFR QR10]','QR12_JINGUJI_DONE','Got the Factlist','post_ending_fallback snapshot verified'])
        if not relevant:continue
        item={'line':num,'utc':utc.isoformat(),'local_source_timestamp':timestamp[1]+' UTC'+timestamp[2],'text':line,'relative_to_capture':'WITHIN_CAPTURE'if start_utc<=utc<=stop_utc else'AFTER_CAPTURE'if utc>stop_utc else'BEFORE_CAPTURE'}
        if fact:item.update(fact=fact[1],previous=int(fact[2]),current=int(fact[3]));writes.append(item)
        timeline.append(item)
    within=[x for x in writes if x['relative_to_capture']=='WITHIN_CAPTURE'and x['fact']in names]
    after=[x for x in writes if x['relative_to_capture']=='AFTER_CAPTURE']
    correlations=[{'sample_seq':r['seq'],'fact':r['data']['fact'],'current_sample':r['data']['current_sample'],'matching_broad_lines':[x['line']for x in within if x['fact']==r['data']['fact']and x['current']==r['data']['current_sample']]}for r in changes]
    assert all(x['matching_broad_lines']for x in correlations),'Unexpected source disagreement; preserve and investigate'
    completion=[x for x in after if x.get('fact')=='mq030_done'and x['previous']==0 and x['current']==1]
    assert len(completion)==1
    assert any(x.get('fact')=='mq030_active'and x['previous']==1 and x['current']==0 for x in after)
    states=[{'seq':r['seq'],'utc':r['utc'],'journal':r['data']['journal']}for r in rows if 'journal'in r['data']]
    manifest=H.parent/'quest_restoration_qr11/d00e_01/diagnostics_manifest_01.json';m=read(manifest);prepared=read(H/'jinguji_replay_01/fixture_manifest.json')
    assert sha(manifest)==prepared['installed_manifest_sha256']
    pins=[]
    for r in m['files']+m['required_files']:
        p=GAME/r['path'];safe(p);actual=sha(p);expected=r.get('after',r.get('sha256'));pins.append({'path':str(p),'actual':actual,'expected':expected,'matches':actual==expected})
    assert all(r['matches']for r in pins),'Current installation drift; no repair performed'
    manual=[]
    for r in read(H/'jinguji_replay_01/manual_save_preservation.json')['files']:
        p=Path(r['path']);safe(p);actual=sha(p);assert actual==r['sha256'],'Manual save changed; do not overwrite';manual.append({'path':str(p),'sha256':actual})
    old=read(H/'completion.json');old_verified=[]
    for r in old['artifacts']:
        p=Path(r['path']);assert sha(p)==r['sha256'],'Sealed QR12 evidence changed';old_verified.append({'path':str(p),'sha256':r['sha256']})
    metadata=[]
    for folder in sorted(SAVE.iterdir()):
        p=folder/'metadata.9.json'
        if not p.is_file():continue
        b=snapshot(p,1048576);d=json.loads(b)['Data']['metadata'];metadata.append({'slot':folder.name,'source':str(p),'sha256':digest(b),'timestamp':d.get('timestampString'),'debug':d.get('debugString'),'mq030_in_finished_metadata':'mq030'in d.get('finishedQuests','').split()})
    result={'status':'SAMPLER_ACTIVATION_VERIFIED_COMPLETION_OUTSIDE_CAPTURE','capture':{'path':str(out/name),'sha256':digest(raw),'rows':len(rows),'start_utc':rows[0]['utc'],'stop_utc':stop['utc'],'elapsed_seconds':stop['wall_elapsed_s'],'stop_reason':metrics['reason'],'sample_rounds':metrics['sample_rounds'],'getter_calls':metrics['fact_getter_calls'],'sample_changes':len(changes),'errors':errors,'clean_cleanup':True,'states':states,'changes':changes},
        'user_observations':[{'text':'stopped, exited normally.','kind':'USER_REPORTED_CAPTURE_ATTEMPT_AND_NORMAL_EXIT'},{'text':'Yes, died and reloaded','kind':'USER_CONFIRMED_RELOAD_AFTER_DEATH','context':'Asked because logger stopped at player detach before broader-log completion.'}],
        'findings':{'sampler':'PASS_BOUNDED_ACTIVATION_GETTER_CAPTURE','broad_log_completion':'CORROBORATED_DONE1_ACTIVE0_AFTER_CAPTURE','current_replay_gameplay_feel':'NOT_SEPARATELY_REPORTED','full_encounter_sampling':'INCOMPLETE_AFTER_PLAYER_DETACH','death_reload_correlation':'HUMAN_CONFIRMED','lifecycle_stop':'EXPECTED_SESSION_GUARD_NO_DIAGNOSTIC_REPAIR_JUSTIFIED','owner_termination_or_lease_execution':'NOT_OBSERVED','save_identity':'NOT_INDEPENDENTLY_BOUND_TO_EXACT_SLOT','native_callbacks':'UNSUPPORTED_NOT_TESTED'},
        'independent_source_correlations':correlations,'broader_log_watched_changes_within_capture':within,'broader_log_changes_after_capture':after,'broader_log_completion_evidence':completion,'timeline':timeline,
        'current_installed_pins':pins,'manual_save_pins':manual,'sealed_QR12_artifacts_verified':len(old_verified),'current_save_metadata_only':metadata,'copied_inputs':inputs,
        'limits':['Two-second getter differences are not native callbacks or exact write ordering.','Death/reload ends capture; no sampling continuity or after-reload transitions are claimed.','Current post-run hashes are not retrospective executed-byte proof.','Earlier QR9 successful completion/vendor/reload evidence remains accepted.','Human game use may change autosaves/logs; no whole-save-root immutability claim.'],
        'next':'No full fight replay is needed. If a later capture crosses death/reload, restart it after loading as a new segment. A short reserved pending-stage test would be separate and requires its own instructions; do not request one merely to reproduce already accepted completion.',
        'assistant_operations':{'game_or_launcher_launches':0,'CUA_or_game_API_calls':0,'installations':0,'runtime_changes':0,'save_or_fact_writes':0,'rebuilds':0}}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    (out/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n',encoding='utf-8')
    print({'status':result['status'],'capture_seconds':stop['wall_elapsed_s'],'sample_changes':len(changes),'sample_rounds':metrics['sample_rounds'],'getter_calls':metrics['fact_getter_calls'],'stop_reason':metrics['reason'],'completion_utc':completion[0]['utc'],'installed_hashes_match':len(pins),'manual_save_pins_match':len(manual),'sealed_QR12_artifacts_match':len(old_verified),'output':str(out)})
if __name__=='__main__':main()
