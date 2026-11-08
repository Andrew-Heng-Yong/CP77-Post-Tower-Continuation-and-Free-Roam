"""Bind exact offline gates. Writes new QR11 readiness; no installation."""
from pathlib import Path
import ctypes, datetime, hashlib, json
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def main():
    target=H/'readiness.json';assert not target.exists(),'Never overwrite readiness'
    suite=read(H/'run_02_results.json');review=read(H/'review/result.json')
    installer=sha(H/'deploy_diagnostics.ps1');manifest=sha(H/'diagnostics_manifest_01.json')
    assert suite['status']=='PASS_DEPLOYMENT_FIXTURES'and suite['installer_sha256']==installer and suite['manifest_sha256']==manifest
    assert review['installer_sha256']==installer and review['manifest_sha256']==manifest
    assert read(H/'collector_controls_02.json')['status']=='PASS_OFFLINE_COLLECTOR'
    b=read(H/'baseline.json');game=Path(b['game_root'])
    binding=game/'bin/x64/plugins/cyber_engine_tweaks/bindings.json';settings=Path(r'C:\Users\Ayong\AppData\Local\CD Projekt Red\Cyberpunk 2077\UserSettings.json')
    code=read(binding)['cet']['overlay_key'];decoded=[(code>>n)&0xffff for n in (48,32,16,0)]
    assert decoded==[0xdc,0,0,0]
    mapping=ctypes.WinDLL('user32',use_last_error=True).MapVirtualKeyW(0xdc,2);assert mapping==0x5c
    values=[]
    def walk(x):
        if isinstance(x,dict):
            if x.get('name')=='openPhone':values.append(x.get('value'))
            for v in x.values():walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    walk(read(settings));assert values==['IK_T']
    ui={'source_binding':str(binding),'binding_sha256':sha(binding),'encoded':code,'hex':hex(code),'decoded_virtual_keys':decoded,
        'CET_key':'backslash \\ (VK_OEM_5 0xDC; current Windows MapVirtualKeyW yields0x5C)',
        'phone_key':'T','UserSettings_path':str(settings),'UserSettings_sha256':sha(settings),
        'source':'https://github.com/maximegmd/CyberEngineTweaks/blob/b160d68cf923f2535cb3a6ebe006de86ef21e359/src/VKBindings.cpp#L404',
        'limits':'Configuration read and official decoder corroboration + read-only Windows key-name mapping; no keyboard/game control or CET launch. Key meaning assumes unchanged bindings/current layout.'}
    (H/'controls_evidence.json').write_text(json.dumps(ui,indent=2)+'\n',encoding='utf-8')
    result={'status':'READY_NOT_INSTALLED','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'installer_sha256':installer,'manifest_sha256':manifest,'fixture_result':'run_02_results.json','fixture_result_sha256':sha(H/'run_02_results.json'),
        'primary_checks':len(suite['checks']),'primary_PS_actions':suite['command_count'],
        'independent_review':{'path':'review/result.json','sha256':sha(H/'review/result.json')},
        'collector_controls':{'path':'collector_controls_02.json','sha256':sha(H/'collector_controls_02.json')},
        'payload':'Exact QR10D01 candidate02; no diagnostic code changes in QR11.',
        'authorization':'No real Install/Rollback/Recover authorized or executed by this task. Preflight is read-only; user decides deployment separately.',
        'limits':'Fixtures cannot prove real Program Files write permissions or hardware power-loss atomicity. Each leaf uses File.Replace; the pair requires the journal/recovery protocol.'}
    target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result)
if __name__=='__main__':main()
