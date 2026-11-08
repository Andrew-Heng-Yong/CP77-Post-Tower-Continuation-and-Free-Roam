"""Collect/analyze a completed human D00E capture. Read-only game/save access.
Writes a new QR11/evidence directory; no launcher, gameplay or save APIs.
"""
from pathlib import Path
import datetime, hashlib, json, os, stat, subprocess, uuid
H=Path(__file__).resolve().parent
PS=r'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
FACT='phonecall_player_with_muamar_el_capitan_reyes'
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def no_links(p):
    for q in (p,*p.parents):
        try:s=q.lstat()
        except FileNotFoundError:continue
        assert not stat.S_ISLNK(s.st_mode)and not(getattr(s,'st_file_attributes',0)&0x400),'Linked input/output refused: '+str(q)
def bounded(p,limit):
    no_links(p);before=p.stat();assert before.st_size<=limit,'Oversized capture refused'
    data=p.read_bytes();after=p.stat();assert(before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'File changed while reading'
    return data
def analyze(data):
    issues=[];rows=[]
    try:rows=[json.loads(x)for x in data.decode('utf-8-sig').splitlines()if x.strip()]
    except (ValueError,UnicodeError)as e:return {'status':'FAIL_CAPTURE_INTEGRITY','issues':[str(e)],'native_callbacks':'UNSUPPORTED_NOT_TESTED'}
    if not rows:return {'status':'FAIL_CAPTURE_INTEGRITY','issues':['empty log'],'native_callbacks':'UNSUPPORTED_NOT_TESTED'}
    if any(not isinstance(r,dict)or not isinstance(r.get('data'),dict)or not isinstance(r.get('event'),str)for r in rows):
        return {'status':'FAIL_CAPTURE_INTEGRITY','issues':['row/data/event shape invalid'],'native_callbacks':'UNSUPPORTED_NOT_TESTED'}
    if rows[0]['event']!='CAPTURE_START':issues.append('capture start is not first')
    if len(rows)>2048:issues.append('row limit exceeded')
    for i,r in enumerate(rows):
        if r.get('schema')!=2 or r.get('module')!='PTFR_QR9_Diagnostics' or r.get('profile')!='D00E' or r.get('seq')!=i+1:issues.append('schema/module/profile/sequence mismatch at row'+str(i+1))
        if r.get('run_id')!=rows[0].get('run_id'):issues.append('mixed capture IDs')
    def event(name):return[r for r in rows if r.get('event')==name]
    starts=event('CAPTURE_START');base=event('ATTACHED_BASELINE');changes=event('FACT_SAMPLE_CHANGE')
    if len(starts)!=1 or starts[0].get('data',{}).get('version')!='QR10D01':issues.append('wrong/missing version start')
    if starts and starts[0].get('data',{}).get('watch_facts')!=[FACT]:issues.append('unexpected fact profile')
    if len(base)!=1 or FACT not in base[0].get('data',{}).get('facts',{}):issues.append('missing attached baseline')
    if len(event('NATIVE_CALLBACK_UNAVAILABLE'))!=1:issues.append('missing explicit callback-unavailable declaration')
    if event('FACT_DELIVERY'):issues.append('native-delivery label incompatible with sampling-only source')
    previous=base[0]['data']['facts'][FACT]if len(base)==1 and FACT in base[0].get('data',{}).get('facts',{})else None
    for r in changes:
        d=r.get('data',{});value=d.get('current_sample')
        valid=isinstance(value,(int,float))and not isinstance(value,bool)and -2147483648<=value<=2147483647 and value%1==0
        if d.get('fact')!=FACT or not valid or d.get('previous_sample')!=previous or value==previous:issues.append('invalid/inconsistent sampled difference')
        previous=value
    errors=[r for r in rows if r.get('event')in('FACT_SAMPLE_ERROR','FACT_READ_FAILED','API_UNAVAILABLE')]
    clean=len(event('STOP'))==1 and len(event('CAPTURE_CLEANUP'))==1 and rows[-1]['event']=='CAPTURE_CLEANUP'
    if issues:status='FAIL_CAPTURE_INTEGRITY'
    elif errors:status='FAIL_DIAGNOSTIC_GETTER'
    elif not clean:status='INCONCLUSIVE_INCOMPLETE_CAPTURE'
    elif changes:status='SAMPLED_CHANGE_RECORDED_AWAITING_HUMAN_CORRELATION'
    else:status='INCONCLUSIVE_NO_SAMPLED_CHANGE'
    return {'status':status,'issues':issues,'rows':len(rows),'run_id':rows[0].get('run_id'),
        'start_utc':rows[0].get('utc'),'end_utc':rows[-1].get('utc'),'event_counts':{n:len(event(n))for n in sorted({r.get('event')for r in rows})},
        'sampled_changes':changes,'errors':errors,'stop':event('STOP'),'native_callbacks':'UNSUPPORTED_NOT_TESTED',
        'gameplay_result':'AWAITING_HUMAN_CALL_OBSERVATION','ordering':'Two-second sampled values only; native writes/ordering/intermediate states unobserved.'}

def main():
    manifest_path=H/'diagnostics_manifest_01.json'
    assert sha(manifest_path.read_bytes())=='C4BC8A6AB6FDF2948DAF7C2F04EDDB34B8287FA9794040701D09E48E9160B5F5','Manifest changed'
    manifest=read(manifest_path);game=Path(manifest['game_root']);save=Path(manifest['save_root'])
    running=subprocess.check_output([PS,'-NoProfile','-Command','Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -in @("Cyberpunk2077","REDlauncher","REDprelauncher") } | ForEach-Object { $_.ProcessName }'],text=True).splitlines()
    assert not running,'Close game and RED launcher normally before collecting; tool will not close them'
    folder=game/Path(manifest['files'][0]['path']).parent
    no_links(folder)
    candidates=sorted(folder.glob('QR10_capture_*.jsonl'),key=lambda p:p.stat().st_mtime_ns,reverse=True)
    selected=None
    for p in candidates:
        data=bounded(p,8388608)
        try:first=json.loads(data.splitlines()[0])
        except (ValueError,IndexError):continue
        if first.get('profile')=='D00E'and first.get('data',{}).get('version')=='QR10D01':selected=(p,data);break
    assert selected,'No QR10D01 D00E capture found. If El Capitan had no Call option, report D00 NOT_TESTABLE; no forced test is needed.'
    p,data=selected;summary=analyze(data);current=[]
    for row in manifest['files']+manifest['required_files']:
        source=game/row['path'];no_links(source);actual=sha(source.read_bytes());expected=row.get('after',row.get('sha256'))
        current.append({'path':row['path'],'sha256':actual,'expected':expected,'matches':actual==expected})
    for row in manifest['protected_saves']:
        source=save/row['path'];no_links(source);assert sha(source.read_bytes())==row['sha256'],'Protected master changed; preserve and investigate'
    output_root=H/'evidence';no_links(output_root);output_root.mkdir(exist_ok=True)
    out=output_root/('D00_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:6]);out.mkdir()
    (out/p.name).write_bytes(data)
    summary['capture_source']={'path':str(p),'sha256':sha(data),'bytes':len(data),'selection':'newest matching D00 by filesystem mtime; report actual run filename if a different capture was intended'}
    summary['installed_current_hashes']=current
    summary['current_installation_matches']=all(r['matches']for r in current)
    if not summary['current_installation_matches']:summary['status']='INCONCLUSIVE_INSTALLATION_DRIFT'
    summary['installation_binding']='Current bytes measured after run, not retrospective executed-byte proof. Correlate with install receipt and capture declaration.'
    tails=[]
    for source in [game/'bin/x64/plugins/cyber_engine_tweaks/scripting.log',game/'bin/x64/plugins/cyber_engine_tweaks/cyber_engine_tweaks.log',folder/'PTFR_QR9_Diagnostics.log']:
        if not source.is_file():tails.append({'path':str(source),'status':'MISSING'});continue
        no_links(source);s=source.stat()
        with source.open('rb')as f:f.seek(max(0,s.st_size-4194304));tail=f.read(4194304)
        assert(s.st_size,s.st_mtime_ns)==(source.stat().st_size,source.stat().st_mtime_ns),'Log changed during collection'
        name='tail_'+source.name; (out/name).write_bytes(tail)
        tails.append({'path':str(source),'source_bytes':s.st_size,'copied_tail_bytes':len(tail),'sha256':sha(tail),'output':name,'limit':'bounded tail; beginning may contain a partial line; older log coverage not guaranteed'})
    summary['log_tails']=tails
    for slot in ('ManualSave-23','ManualSave-24'):
        source=save/slot/'metadata.9.json';raw=bounded(source,1048576);(out/(slot+'_metadata.json')).write_bytes(raw)
    receipt=H/'recovery/diagnostics_d00e_01/journal.json'
    summary['installation_receipt']={'path':str(receipt),'sha256':sha(bounded(receipt,16777216))if receipt.exists()else'NOT_FOUND'}
    summary['user_reply_template']='D00 | ManualSave-24, 2 Nov 16:37 | El Capitan Call available yes/no | rang/answered/no answer/stalled | recording started/stopped | unexpected behavior none/details'
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':summary['status'],'sampled_changes':len(summary.get('sampled_changes',[])),'evidence_folder':str(out),'native_callbacks':'UNSUPPORTED_NOT_TESTED','report_back':summary['user_reply_template']},indent=2))

if __name__=='__main__':main()
