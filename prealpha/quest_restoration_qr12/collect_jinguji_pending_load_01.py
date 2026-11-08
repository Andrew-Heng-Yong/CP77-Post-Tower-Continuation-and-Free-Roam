"""Bounded assessment of two user-operated pending-load captures, no game writes."""
from pathlib import Path
import collections,datetime,json,re,subprocess
from collect_jinguji_replay_01 import H,GAME,SAVE,PS,read,sha,snapshot,digest,safe
def main():
    running=subprocess.check_output([PS,'-NoProfile','-Command','Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -in @("Cyberpunk2077","REDlauncher","REDprelauncher") } | ForEach-Object { $_.ProcessName }'],text=True).splitlines()
    assert not running,'Game must already be closed; collector never closes it'
    out=H/'observations/jinguji_pending_load_01';assert not out.exists();out.mkdir(parents=True)
    root=GAME/'bin/x64/plugins/cyber_engine_tweaks';diag=root/'mods/PTFR_QR9_Diagnostics';inputs=[]
    def copy(p,name,limit=8388608):
        raw=snapshot(p,limit);d=out/name;d.write_bytes(raw);assert sha(d)==digest(raw)
        inputs.append({'source':str(p),'copy':str(d),'bytes':len(raw),'sha256':digest(raw)});return raw
    profile=read(diag/'watch.json')['profiles']['S05'];watch=profile['facts'];assert len(watch)==32
    runs=[]
    for name in ['QR10_capture_20261103T183826Z_0001.jsonl','QR10_capture_20261103T183943Z_0002.jsonl']:
        raw=copy(diag/name,name);rows=[json.loads(line)for line in raw.decode('utf-8-sig').splitlines()if line.strip()]
        assert len(rows)<=2048 and rows[0]['event']=='CAPTURE_START'and rows[-1]['event']=='CAPTURE_CLEANUP'
        for i,row in enumerate(rows,1):assert row['schema']==2 and row['seq']==i and row['module']=='PTFR_QR9_Diagnostics'and row['run_id']==name and row['profile']=='S05'and row['user_label']=='QR12-Jinguji-PendingLoad'
        def ev(n):return [x for x in rows if x['event']==n]
        for n in ['CAPTURE_START','ATTACHED_BASELINE','ATTACHED_STATE','STOP','CAPTURE_CLEANUP','NATIVE_CALLBACK_UNAVAILABLE','FACT_SAMPLING_STARTED']:assert len(ev(n))==1
        assert ev('CAPTURE_START')[0]['data']['version']=='QR10D01'and ev('CAPTURE_START')[0]['data']['watch_facts']==watch
        assert ev('SESSION_WAIT')and not ev('FACT_DELIVERY')
        base=ev('ATTACHED_BASELINE')[0];latest=dict(base['data']['facts']);assert set(latest)==set(watch)
        changes=ev('FACT_SAMPLE_CHANGE')
        for r in changes:
            d=r['data'];assert d['fact']in watch and latest[d['fact']]==d['previous_sample']and d['current_sample']!=d['previous_sample']
            assert isinstance(d['current_sample'],int)and not isinstance(d['current_sample'],bool)and -2147483648<=d['current_sample']<=2147483647
            latest[d['fact']]=d['current_sample']
        stop=ev('STOP')[0];metrics=stop['data'];assert metrics['sampled_changes']==len(changes)
        assert metrics['fact_getter_calls']==32*(metrics['sample_rounds']+1)
        errors=[r for r in rows if r['event']in ['FACT_SAMPLE_ERROR','FACT_READ_FAILED','API_UNAVAILABLE']or r['data'].get('errors')];assert not errors
        journal=ev('ATTACHED_STATE')[0]['data']['journal'];state=journal['quests/minor_quest/mq030_melisa']['state']
        # Specific observations are checked against the frozen input; no synthetic engine fixture.
        assert state=='gameJournalEntryState : Succeeded (3)'
        assert base['data']['facts']['mq030_done']==0 and base['data']['facts']['mq030_active']==1
        assert latest['mq030_done']==1 and latest['mq030_active']==0
        assert {r['data']['fact']for r in changes}=={'mq030_active','mq030_done'}
        runs.append({'file':name,'sha256':digest(raw),'start_utc':rows[0]['utc'],'attached_utc':base['utc'],'stop_utc':stop['utc'],'elapsed_seconds':stop['wall_elapsed_s'],
            'rows':len(rows),'event_counts':dict(collections.Counter(r['event']for r in rows)),'sample_rounds':metrics['sample_rounds'],'getter_calls':metrics['fact_getter_calls'],
            'initial_facts':base['data']['facts'],'final_sampled_facts':latest,'first_journal_state':state,'fact_changes':changes,'errors':errors,'stop_reason':metrics['reason'],
            'completion_detected_seconds_after_attachment':max(r['wall_elapsed_s']for r in changes)-base['wall_elapsed_s'],'cleanup_recorded':True,'session_wait':ev('SESSION_WAIT'),
            'scope':'Separate load segment. Initial journal Succeeded precedes later observed terminal fact differences. No exact native graph/owner/write-order proof.'})
    broad=copy(root/'scripting.log','CET_scripting.log').decode('utf-8-sig',errors='replace')
    copy(root/'cyber_engine_tweaks.log','CET_framework.log');copy(root/'gamelog.log','CET_gamelog.log')
    timeline=[]
    start=datetime.datetime.fromisoformat(runs[0]['start_utc']);end=datetime.datetime.fromisoformat(runs[-1]['stop_utc'])+datetime.timedelta(seconds=30)
    for number,line in enumerate(broad.splitlines(),1):
        m=re.match(r'^\[([0-9-]+ [0-9:]+) UTC([+-][0-9:]+)\]',line)
        if not m:continue
        t=datetime.datetime.fromisoformat(m[1]+m[2]).astimezone(datetime.timezone.utc)
        if not start<=t<=end:continue
        if any(x in line for x in ['mq030_','PTFRB0ZAN_','[PTFR QR10]','QR12_JINGUJI_PENDING','Got the Factlist','post_ending_fallback snapshot verified']):timeline.append({'line':number,'utc':t.isoformat(),'text':line})
    for r in runs:
        a=datetime.datetime.fromisoformat(r['attached_utc']);b=datetime.datetime.fromisoformat(r['stop_utc']);matches=[x for x in timeline if a<=datetime.datetime.fromisoformat(x['utc'])<=b and'mq030_done : 0 -> 1'in x['text']]
        assert len(matches)==1;r['broader_log_done1_corrobation']=matches
    manifest=H.parent/'quest_restoration_qr11/d00e_01/diagnostics_manifest_01.json';m=read(manifest);pins=[]
    for r in m['files']+m['required_files']:
        p=GAME/r['path'];safe(p);actual=sha(p);expected=r.get('after',r.get('sha256'));assert actual==expected;pins.append({'path':str(p),'sha256':actual})
    manuals=[]
    for r in read(H/'jinguji_replay_01/manual_save_preservation.json')['files']:
        assert sha(Path(r['path']))==r['sha256'];manuals.append(r)
    candidate=[]
    for r in read(H/'jinguji_pending_load_01/preflight.json')['checks'][:3]:
        p=Path(r['source']);assert sha(p)==r['sha256'];candidate.append(r)
    old=read(H/'completion.json');assert all(sha(Path(r['path']))==r['sha256']for r in old['artifacts'])
    result={'status':'PASS_BOUNDED_POST_LOAD_TERMINAL_FACT_OBSERVATION_TWICE','user_report':'did it 2 times. already complete after load in.',
        'runs':runs,'broader_log_timeline':timeline,'copied_inputs':inputs,
        'findings':{'journal_on_load':'Succeeded on first attached read both times; consistent with user observation.',
            'terminal_facts':'Both captures start active1/done0 and observe active0/done1 later,22/25seconds after attachment. Thus terminal fact updates were captured, not merely an already-final baseline.',
            'sampler':'Both armed in main menu, attached after load, produced coherent two-second differences with zero recorded getter/state errors.',
            'first_stop':'Player detach ended run1 after terminal samples; no death is inferred. Segment remains separate from run2.',
            'second_stop':'Explicit QR12_JINGUJI_PENDING_DONE, clean cleanup.',
            'precise_pending_scene_or_owner':'NOT_PROVEN','full_cleanup_or_reward_idempotence':'NOT_PROVEN','native_callbacks':'UNSUPPORTED_NOT_TESTED','save_identity':'Requested current pinned AutoSave3, but logger does not independently bind an exact saved slot/body.',
            'source_timing':'Broader logger done1 notice occurs later than sample detection. Preserve both timestamps; no exact native-write ordering or logging-latency cause is inferred.',
            'defect':'No stall/reset/diagnostic failure established by these bounded observations. Journal-vs-terminal-fact timing is preserved as an observation, not silently labelled a quest defect.'},
        'verification':{'installed_pins':pins,'manual_save_pins':manuals,'candidate_pins':candidate,'sealed_QR12_artifacts_matched':len(old['artifacts'])},
        'next':'Close this Jinguji load test; no repeat or further fight/shop/reload is requested. Carry internal owner/lease/reward proof and other genuine-fixture blockers forward.',
        'assistant_operations':{'game_or_launcher_launches':0,'CUA_or_game_API_calls':0,'runtime_or_diagnostic_changes':0,'save_or_fact_writes':0,'installations_or_rebuilds':0}}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');(out/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n',encoding='utf-8')
    print({'status':result['status'],'runs':[{'duration':r['elapsed_seconds'],'rounds':r['sample_rounds'],'changes':len(r['fact_changes']),'delay_after_attach':r['completion_detected_seconds_after_attachment'],'stop':r['stop_reason']}for r in runs],'installed_hashes':len(pins),'manual_pins':len(manuals),'output':str(out)})
if __name__=='__main__':main()
