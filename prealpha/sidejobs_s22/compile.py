"""Compile S22 in workspace copies and inspect the resulting bytecode bodies."""
import importlib.util, inspect, json, re, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('s21_compile',ROOT/'prealpha/sidejobs_s21/compile.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
sha,body,block=prior.sha,prior.body,prior.block
GAME=prior.GAME

def compact(s):
 s=re.sub(r'PTFR\.(?:SideJobsS22|SideJobsS2|RestrictionsR2|RestrictionsR3)\.','',s)
 return prior.compact(s)

def verify(text,s2,s22):
 # Reuse the pinned prior verifier, changing ONLY its expected authorization
 # predicate. This changes test expectations, never the compiled artifact.
 old="need('DevelopmentArmed','if this.faulted','return false','return this.explicitDevelopment || IsDefined(prior) && prior.DevelopmentArmed()')"
 new="same_return('DevelopmentArmed'); need('DevelopmentArmed','return !this.faulted && this.Common()')"
 verifier=inspect.getsource(prior.verify_bodies);assert verifier.count(old)==1
 scope=dict(prior.__dict__);exec(verifier.replace(old,new),scope)
 s2proof=scope['verify_bodies'](text,s2)
 owner=block(text,r'\bpublic class PTFR\.SideJobsS22\.SideJobsS22 extends ScriptableSystem\s*\{','compiled S22')
 data=block(text,r'\bpublic abstract class PTFR\.SideJobsS22\.SideJobDataS22 extends IScriptable\s*\{','compiled data')
 source=block(s22,r'\bpublic class SideJobsS22 extends ScriptableSystem\s*\{','source S22')
 srcdata=block(s22,r'\bpublic abstract class SideJobDataS22\s*\{','source data')
 checked=[]
 def need(name,*tokens):
  actual=compact(body(owner,name))
  for token in tokens:assert compact(token) in actual,(name,token)
  checked.append(name)
 for name in ['Common','Safe','Ready','Fact','Own']:
  a=re.findall(r'\breturn\s+([^;]+);',body(owner,name));b=re.findall(r'\breturn\s+([^;]+);',body(source,name))
  assert [compact(x) for x in a]==[compact(x) for x in b],name;checked.append(name)
 need('Permit','!IsDefined(qs)||this.Own(i,"Issued")!=0','SideJobDataS22.Tag(i)+"_Permit"','qs.SetFactStr(name,value)')
 need('Restored','this.epoch+=1','ArrayClear(this.previous)','this.warmup=3','if this.Own(i,"Issued")==0','this.Permit(i,false)')
 need('Read','!IsDefined(jm)||!IsDefined(qs)||jm.HasAnyDelayedStateChanges()',
      'GetEntryByString(paths[k],classes[k])','IsDefined(entry)?EnumInt(jm.GetEntryState(entry)):-1',
      'state!=first[k]&&state!=second[k]','actual!=wanted[k]','sample.valid=false')
 assert body(owner,'Read').count('jm.HasAnyDelayedStateChanges()')==2
 need('Same','!a.valid||!b.valid','ArraySize(a.states)!=ArraySize(b.states)','ArraySize(a.facts)!=ArraySize(b.facts)','a.states[i]!=b.states[i]','a.facts[i]!=b.facts[i]')
 need('Poll','!this.running||epoch!=this.epoch','this.Own(i,"Issued")==0','this.Same(this.previous[i],current)&&this.Ready(i)','this.previous[i]=current','this.Permit(i,false);this.previous[i]=empty')
 assert owner.count('.SetFactStr(')==1
 for forbidden in ['ChangeEntryState','GiveReward','GiveItem','ModLog(','SetFact(']:assert forbidden not in owner,forbidden
 arrays=0
 for stem in ['Paths','Classes','StatesA','StatesB','FactNames','FactValues']:
  for i in range(4):
   name=stem+str(i);original=body(srcdata,name);actual=body(data,name)
   wanted=re.search(r'return\s*(\[[^]]*\]);',original);assert wanted,name
   expected=json.loads(re.sub(r'\bn"','"',wanted.group(1)))
   resize=re.search(r'ArrayResize\((synthetic\$\d+),\s*(\d+)u\)',actual)
   assert resize and int(resize.group(2))==len(expected),(name,'size')
   assignments=re.findall(re.escape(resize.group(1))+r'\[(\d+)u\]\s*=\s*(n?"[^"\n]*"|-?\d+);',actual)
   parsed=[(int(k),json.loads(v.removeprefix('n').replace("\\'","'"))) for k,v in assignments]
   assert parsed==list(enumerate(expected)),(name,'data');arrays+=1
   branch=block(body(data,stem),r'if i == '+str(i)+r'\s*\{',name+' dispatch')
   assert compact(branch)=='returnSideJobDataS22.'+name+'();'
 for name in ['Count','ID','Title','Tag','Index']:
  a=re.findall(r'\breturn\s+([^;]+);',body(data,name));b=re.findall(r'\breturn\s+([^;]+);',body(srcdata,name))
  assert [compact(x) for x in a]==[compact(x) for x in b],name
 return {'s2':s2proof,'s22_methods':checked,'s22_arrays':arrays,'owned_permit_only':True}

def main(revision):
 build=Path(__file__).resolve().parent/'build'/revision;dest=build/'compile_result.json'
 assert not dest.exists(),'Immutable evidence exists'
 stage=Path(tempfile.mkdtemp(prefix='compile_',dir=build));cache=stage/'cache';cache.mkdir()
 protected={str(p):sha(p) for p in (GAME/'r6/cache').iterdir() if p.is_file()}
 for name in ('final.redscripts','final.redscripts.ts'):shutil.copy2(GAME/'r6/cache'/name,cache/name)
 deps={}
 for p in (GAME/'r6/scripts').rglob('*.reds'):
  deps[str(p)]=sha(p);target=stage/'scripts'/p.relative_to(GAME/'r6/scripts');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
 sources=[]
 for version in ['S2','S22']:
  source=stage/('scripts/TowerContinued_SideJobs_'+version);source.mkdir(exist_ok=True)
  shutil.copy2(build/('SideJobs'+version+'.reds'),source/('SideJobs'+version+'.reds'));sources.append(source)
 plugins=(ROOT/'research/restriction_profiles/implementation_r1/compile_paths.txt').read_text(encoding='utf-8-sig').splitlines()[2:]
 for folder in plugins:
  for p in Path(folder).rglob('*.reds'):deps[str(p)]=sha(p)
 cli=ROOT/'research/finalboards_dismissal/tooling/redscript-cli.exe'
 def run(args,name):
  result=subprocess.run(args,capture_output=True,text=True,timeout=180);log=result.stdout+result.stderr;(stage/name).write_text(log,encoding='utf-8')
  assert result.returncode==0 and 'Output successfully saved' in log and not re.search(r'(?m)^\[?ERROR\b',log),log[-12000:]
  return log
 args=[str(cli),'compile']
 for p in sources+[stage/'scripts/PTFR_PreAlpha',GAME/'red4ext/plugins/Codeware/Scripts']:args+=['-s',str(p)]
 args+=['-b',str(cache/'final.redscripts'),'-o',str(stage/'headless.redscripts')];run(args,'headless.log')
 paths=stage/'compile_paths.txt';paths.write_text('\n'.join(plugins)+'\n')
 compiled=cache/'compiled.redscripts'
 log=run([str(GAME/'engine/tools/scc.exe'),'-compile',str(stage/'scripts'),'-compilePathsFile',str(paths),'-customCacheDir',str(cache),'-outputCacheFile',str(compiled),str(cache/'final.redscripts')],'scc.log')
 assert 'Compilation complete' in log and 'EquipmentEx.reds' in log
 flat=stage/'compiled.script';run([str(cli),'decompile','-i',str(compiled),'-o',str(flat)],'decompile.log')
 text=re.sub(r'\$local\$\d+','',flat.read_text(encoding='utf-8-sig'));assert 'EquipmentEx.OutfitSystem.GetInstance' in text
 proof=verify(text,(build/'SideJobsS2.reds').read_text(encoding='utf-8-sig'),(build/'SideJobsS22.reds').read_text(encoding='utf-8-sig'))
 for p,h in {**protected,**deps}.items():assert sha(p)==h,p
 report={'status':'PASS_NOT_LIVE','build_sha256':sha(build/'build.json'),'compiler_sha256':sha(Path(__file__)),'script_sha256':{n:sha(build/n) for n in ['SideJobsS2.reds','SideJobsS22.reds']},'compiled_sha256':sha(compiled),'stage':str(stage),'combined_cli':True,'full_scc':True,'equipmentex':True,'body_readback':True,'body_checks':proof,'protected':protected,'dependencies':deps,'live_files_unchanged':True}
 dest.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['protected','dependencies']},indent=2))
if __name__=='__main__':main(sys.argv[1])
