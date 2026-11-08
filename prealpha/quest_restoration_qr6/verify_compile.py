"""Verify exact current compile inputs; fresh offline SCC only for changed pins."""
from pathlib import Path
import sys,shutil,subprocess,argparse
W=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,snapshot
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();O=Path(a.output).resolve();assert not O.exists()
e=read(H/'source_epoch_00.json');C=Path(e['candidate']);G=Path(read(H/'prepared.json')['game']); priorpath=W/'prealpha/quest_restoration_qr1/candidate_01/compile_01/result.json';prior=read(priorpath)
assert prior['status']=='PASS';roots=[('game',G/'r6/scripts'),('Codeware',G/'red4ext/plugins/Codeware/Scripts'),('ArchiveXL',G/'red4ext/plugins/ArchiveXL/Scripts'),('TweakXL',G/'red4ext/plugins/TweakXL/Scripts'),('mod_settings',G/'red4ext/plugins/mod_settings')]
S=O/'scripts';K=O/'cache'; K.mkdir(parents=True);pins={};sources=[]
for name,root in roots:
 assert root.is_dir(),str(root)
 for p in sorted(root.rglob('*.reds')):
  pins[str(p)]=sha(p);t=S/name/p.relative_to(root);t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,t);sources.append({'source':str(p),'staged':str(t),'sha256':sha(t)})
managed=[]
for r in e['package_files']:
 if r['path'].endswith('.reds'):
  f=C/'package'/r['path'];assert sha(f)==r['sha256'];t=S/'game'/Path(r['path']).relative_to('r6/scripts');assert t.exists();shutil.copyfile(f,t);managed.append({'path':r['path'],'sha256':sha(t)})
for name in ['final.redscripts','final.redscripts.ts']:
 p=G/'r6/cache'/name;pins[str(p)]=sha(p);shutil.copyfile(p,K/name)
exe=G/'engine/tools/scc.exe';pins[str(exe)]=sha(exe)
oldset=set(prior['input_pins']);deltas=[{'path':p,'old':prior['input_pins'].get(p),'current':h}for p,h in pins.items()if prior['input_pins'].get(p)!=h]+[{'path':p,'old':prior['input_pins'][p],'current':None}for p in oldset-set(pins)]
source_equality=[]
oldroot=priorpath.parent/'scripts'
for p in sorted(S.rglob('*.reds')):
 old=oldroot/p.relative_to(S);source_equality.append({'relative':str(p.relative_to(S)),'old':sha(old)if old.exists()else None,'current':sha(p)})
same=all(r['old']==r['current'] for r in source_equality)and len(source_equality)==len(prior['staged_sources'])
run=bool(deltas)or not same
if run:
 paths=O/'compile_paths.txt';paths.write_text('',encoding='utf-8');cmd=list(map(str,[exe,'-compile',S,'-compilePathsFile',paths,'-customCacheDir',K,'-outputCacheFile',K/'compiled.redscripts',K/'final.redscripts']))
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=300);log=r.stdout+r.stderr;(O/'scc.log').write_text(log,encoding='utf-8');assert r.returncode==0 and 'Compilation complete'in log and (K/'compiled.redscripts').exists(),log[-2000:]
else:cmd=prior['command'];log='Exact unchanged current inputs: reuse pinned successful SCC result.'
assert all(sha(p)==h for p,h in pins.items()),'Installed inputs changed during offline validation'
write(O/'source_comparison.json',source_equality)
out={'status':'PASS_CURRENT_INPUTS_OFFLINE_COMPILED'if run else'PASS_EXACT_UNCHANGED_INPUT_REUSE','source_count':len(source_equality),'managed_sources':len(managed),'input_pin_count':len(pins),'input_pins':pins,'staged_sources':snapshot(S.rglob('*.reds')),'managed':managed,'prior_result':str(priorpath),'prior_result_sha256':sha(priorpath),'prior_source_bytes_equal':same,'changed_input_pins':deltas,'fresh_SCC_invocation':run,'compiled_sha256':sha(K/'compiled.redscripts')if run else prior['compiled_sha256'],'command':cmd,'game_writes':0,'save_writes':0,'installed_inputs_unchanged':True,'reason':'Preexisting compiler timestamp changed since QR5; all actual source/cache/executable input pins compared before deciding reuse versus fresh offline SCC.'}
write(O/'result.json',out);print({k:out[k]for k in ['status','source_count','managed_sources','input_pin_count','prior_source_bytes_equal','fresh_SCC_invocation','compiled_sha256']})
