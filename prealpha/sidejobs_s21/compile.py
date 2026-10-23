"""Compile a new S2 layer in workspace copies, never in game caches."""
import json, re, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import sha
GAME=Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')

def block(text,pattern,label):
 match=re.search(pattern,text);assert match,label
 start=match.end();depth=1;quoted=False;escape=False
 for pos in range(start,len(text)):
  char=text[pos]
  if quoted:
   if escape:escape=False
   elif char=='\\':escape=True
   elif char=='"':quoted=False
  elif char=='"':quoted=True
  elif char=='{':depth+=1
  elif char=='}':
   depth-=1
   if depth==0:return text[start:pos]
 raise AssertionError('Unbalanced '+label)

def body(text,name):
 return block(text,r'\b(?:public|private)\s+(?:static\s+)?func\s+'+re.escape(name)+r'\([^)]*\)[^{]*\{',name)

def compact(text):
 text=re.sub(r'\$local\$\d+','',text)
 text=re.sub(r'PTFR\.(?:SideJobsS2|ActivityStateR3|RestrictionsR2|RestrictionsR3)\.','',text)
 text=re.sub(r'(\d+)\.0+\b',r'\1.0',text)
 return re.sub(r'\s+','',text)

def verify_bodies(text,source):
 owner=block(text,r'\bpublic class PTFR\.SideJobsS2\.SideJobsS2 extends ScriptableSystem\s*\{','compiled S2 owner')
 data=block(text,r'\bpublic abstract class PTFR\.SideJobsS2\.SideJobDataS2 extends IScriptable\s*\{','compiled S2 data')
 src_owner=block(source,r'\bpublic class SideJobsS2 extends ScriptableSystem\s*\{','source S2 owner')
 src_data=block(source,r'\bpublic abstract class SideJobDataS2\s*\{','source S2 data')
 failure=block(text,r'\bpublic abstract class PTFR\.SideJobsS2\.SideJobFailureDataS21 extends IScriptable\s*\{','compiled failed inventory data')
 src_failure=block(source,r'\bpublic abstract class SideJobFailureDataS21\s*\{','source failed inventory data')
 checked=[]
 def need(name,*tokens):
  actual=compact(body(owner,name))
  for token in tokens:assert compact(token) in actual,(name,token)
  checked.append(name)
 def same_return(name):
  a=re.findall(r'\breturn\s+([^;]+);',body(owner,name))
  b=re.findall(r'\breturn\s+([^;]+);',body(src_owner,name))
  assert [compact(x) for x in a]==[compact(x) for x in b],('return mismatch',name)
  checked.append(name)
 for name in ['Catalogue','BoundaryNow','TeardownNow','Common','Certified']:same_return(name)
 # Decompiler removes redundant parentheses around && under ||.
 need('DevelopmentArmed','if this.faulted','return false','return this.explicitDevelopment || IsDefined(prior) && prior.DevelopmentArmed()')
 need('EnableFreshFixture','NotEquals(confirmation,"DISPOSABLE_SAVE")','this.faulted || !this.Common()','this.explicitDevelopment = true')
 need('FailedReport','!IsDefined(jm)||jm.HasAnyDelayedStateChanges()',
      'GetEntryByString(paths[i],"gameJournalQuest")','IsDefined(entry)?EnumInt(jm.GetEntryState(entry)):-1',
      'state==1','state==2','state==3','state==4','inactive+=1','active+=1','succeeded+=1','failed+=1','unknown+=1')
 need('FailedDetails','!IsDefined(jm)||!IsDefined(qs)||jm.HasAnyDelayedStateChanges()',
      'GetEntryByString(roots[i],"gameJournalQuest")','IsDefined(root)?EnumInt(jm.GetEntryState(root)):-1',
      'if state==4','SideJobFailureDataS21.DetailPaths(i)','SideJobFailureDataS21.DetailClasses(i)',
      'SideJobFailureDataS21.FactNames(i)','GetEntryByString(paths[k],classes[k])','qs.GetFactStr(facts[k])',
      'if EnumInt(jm.GetEntryState(root))!=4','if state<1||state>4')
 for name in ['FailedReport','FailedDetails']:
  diagnostic=body(owner,name)
  assert diagnostic.count('jm.HasAnyDelayedStateChanges()')==2,(name,'settled before and after')
  assert not re.search(r'this\.\w+\s*=',diagnostic),(name,'owner mutation')
  for forbidden in ['SetFact','SetPermit','SetRoute','ChangeEntry','EnableFreshFixture','CaptureBeforeEnding','Schedule(','ModLog(','QueueRequest','GiveItem']:
   assert forbidden not in diagnostic,(name,forbidden)
 need('Restored','this.epoch+=1','this.warmup=3','if this.Own(i,"Issued")==0','this.SetPermit(i,false);this.SetRoute(i,0)',
      'this.schema != 0 && (this.schema != 1 || NotEquals(this.catalogue, SideJobsS2.Catalogue()))',
      'if !this.faulted && this.BoundaryNow() && !this.frozen','this.frozen=true;this.certified=false;ArrayClear(this.eligible)')
 need('Read','!IsDefined(jm)||jm.HasAnyDelayedStateChanges()||ArraySize(paths)==0||ArraySize(paths)!=ArraySize(classes)',
      'GetEntryByString(paths[k],classes[k])','IsDefined(entry)?EnumInt(jm.GetEntryState(entry)):-1',
      'ArrayPush(sample.facts,this.Fact(names[k]))','ArrayPush(sample.setup,this.Fact(setup[k]))','sample.fresh=this.SampleFresh(i,sample)')
 need('SampleFresh','ArraySize(sample.states)!=ArraySize(paths)','ArraySize(sample.facts)!=ArraySize(names)','ArraySize(sample.setup)!=ArraySize(setup)',
      'required=SideJobDataS2.FreshIndices(i)','ArraySize(required)==0','required[k]<0||required[k]>=ArraySize(sample.states)||sample.states[required[k]]!=1',
      'sample.facts[k]!=0','sample.setup[k]<0||sample.setup[k]>1')
 need('CaptureBeforeEnding','this.faulted||this.frozen||this.BoundaryNow()','!this.Same(sample[i],this.Read(i))',
      'this.BoundaryNow()||jm.HasAnyDelayedStateChanges()||this.captures>=2147483647','this.baseline=sample','this.ready=this.ShapeValid()','this.lastCapture=this.Now()')
 cap=compact(body(owner,'CaptureBeforeEnding'))
 assert cap.index('this.BoundaryNow()||jm.HasAnyDelayedStateChanges()||this.captures>=2147483647')<cap.index('this.baseline=sample')
 need('Freeze','this.certified=nativeBoundary&&!this.TeardownNow()&&this.ready&&this.ShapeValid()&&age>=0.0&&age<=6.0&&IsDefined(jm)&&!jm.HasAnyDelayedStateChanges()',
      'fresh=this.certified&&this.baseline[i].fresh&&this.Same(this.baseline[i],this.Read(i))','ArrayPush(this.eligible,fresh)','this.frozen=true')
 need('CanPermit','!this.running||this.warmup>0||this.faulted||!this.Common()||this.Own(i,"Ready")!=1||this.Own(i,"Issued")!=0||this.Own(i,"Finished")!=0||this.Own(i,"Fault")!=0',
      '!this.Certified(SideJobDataS2.ID(i))&&!this.DevelopmentArmed()','!IsDefined(player)||!BodyPolicy.Safe(player)',
      'before=this.Read(i);after=this.Read(i)','return before.fresh&&after.fresh&&this.Same(before,after)')
 need('Poll','!this.running||epoch!=this.epoch','this.Freeze(false)','if this.Own(i,"Issued")==0','allowed=this.CanPermit(i)',
      'this.SetRoute(i,this.Certified(SideJobDataS2.ID(i))?1:2)',
      'this.SetPermit(i,this.Own(i,"AuthorizedRoute")==1||this.Own(i,"AuthorizedRoute")==2)','this.SetPermit(i,false);this.SetRoute(i,0)')
 poll=compact(body(owner,'Poll'))
 assert poll.index('this.SetRoute(i,this.Certified(')<poll.index('this.SetPermit(i,this.Own(i,"AuthorizedRoute")')
 for name,suffix,arg in [('SetPermit','Permit','value'),('SetRoute','AuthorizedRoute','route')]:
  need(name,f'SetFactStr("PTFRS2_"+SideJobDataS2.Tag(i)+"_{suffix}",{arg})')
 assert owner.count('.SetFactStr(')==2 and '.SetFact(' not in owner and 'ChangeEntryState' not in owner and 'ModLog(' not in owner
 for name in ['Paths','Classes','ZeroFacts','SetupFacts']:
  assert re.findall(r'"([^"\n]*)"',body(data,name))==re.findall(r'"([^"\n]*)"',body(src_data,name)),('data order/value drift',name)
  checked.append('Data.'+name)
 for name in ['Count','ID','Tag','Index']:
  a=re.findall(r'\breturn\s+([^;]+);',body(data,name));b=re.findall(r'\breturn\s+([^;]+);',body(src_data,name))
  assert [compact(x).replace('(','').replace(')','') for x in a]==[compact(x).replace('(','').replace(')','') for x in b],('data return mismatch',name)
  checked.append('Data.'+name)
 for name in ['Paths','Classes','ZeroFacts','SetupFacts','FreshIndices']:
  for index in [0,1]:
   expected=re.search(r'if i == '+str(index)+r'\s*\{\s*return\s*(\[[^]]*\]);',body(src_data,name),re.S)
   if not expected:
    assert not re.search(r'if i == '+str(index)+r'\s*\{',body(data,name)),(name,index)
    continue
   wanted=json.loads(expected.group(1))
   branch=block(body(data,name),r'if i == '+str(index)+r'\s*\{',name+str(index))
   resize=re.search(r'ArrayResize\((synthetic\$\d+),\s*(\d+)u\)',branch)
   assert resize and int(resize.group(2))==len(wanted),(name,index,'size')
   assignments=re.findall(re.escape(resize.group(1))+r'\[(\d+)u\]\s*=\s*("[^"]*"|-?\d+);',branch)
   assert [(int(k),json.loads(v)) for k,v in assignments]==list(enumerate(wanted)),(name,index,'values')
   assert 'return '+resize.group(1)+';' in branch,(name,index,'returned array')
  checked.append('DataArrays.'+name)
 def same_array(compiled_body,wanted,label):
  resize=re.search(r'ArrayResize\((synthetic\$\d+),\s*(\d+)u\)',compiled_body)
  assert resize and int(resize.group(2))==len(wanted),(label,'size')
  assignments=re.findall(re.escape(resize.group(1))+r'\[(\d+)u\]\s*=\s*("[^"\n]*"|-?\d+);',compiled_body)
  # REDscript's decompiler escapes apostrophes inside double-quoted strings.
  assert [(int(k),json.loads(v.replace("\\'", "'"))) for k,v in assignments]==list(enumerate(wanted)),(label,'values')
  assert 'return '+resize.group(1)+';' in compiled_body,(label,'returned array')
 for name in ['IDs','Titles','Paths']:
  expected=re.search(r'\breturn\s*(\[[^]]*\]);',body(src_failure,name),re.S)
  assert expected,(name,'source array')
  wanted=json.loads(expected.group(1));assert len(wanted)==58,(name,'roster count')
  same_array(body(failure,name),wanted,'FailedData.'+name)
  checked.append('FailedData.'+name)
 assert compact(body(failure,'Count'))=='return58;','failed inventory count'
 checked.append('FailedData.Count')
 arrays=0
 for name in ['DetailPaths','DetailClasses']:
  for index in range(58):
   expected=re.search(r'if i == '+str(index)+r'\s*\{\s*return\s*(\[[^]]*\]);',body(src_failure,name),re.S)
   if not expected:
    assert not re.search(r'if i == '+str(index)+r'\s*\{',body(failure,name)),(name,index,'unexpected branch')
    continue
   wanted=json.loads(expected.group(1))
   branch=block(body(failure,name),r'if i == '+str(index)+r'\s*\{',name+str(index))
   same_array(branch,wanted,'FailedData.'+name+str(index));arrays+=1
  checked.append('FailedDataArrays.'+name)
 # Keep the large fact catalogue in small per-job methods. Verify both the
 # dispatcher and every compiled array, rather than accepting compile success.
 for index in range(58):
  helper='FactNames'+str(index)
  expected=re.search(r'if i == '+str(index)+r'\s*\{\s*return\s*SideJobFailureDataS21\.'+helper+r'\(\);',body(src_failure,'FactNames'))
  if not expected:
   assert not re.search(r'if i == '+str(index)+r'\s*\{',body(failure,'FactNames')),('FactNames',index,'unexpected dispatch')
   continue
  branch=block(body(failure,'FactNames'),r'if i == '+str(index)+r'\s*\{',helper+'dispatch')
  assert compact(branch)=='returnSideJobFailureDataS21.'+helper+'();',(helper,'dispatch target')
  source_array=re.search(r'\breturn\s*(\[[^]]*\]);',body(src_failure,helper),re.S)
  if source_array:
   same_array(body(failure,helper),json.loads(source_array.group(1)),'FailedData.'+helper)
  else:
   assert compact(body(src_failure,helper))=='letempty:array<String>;returnempty;',(helper,'source empty array')
   assert compact(body(failure,helper))=='letempty:array<String>;ArrayClear(empty);returnempty;',(helper,'compiled empty array')
  arrays+=1
 checked.append('FailedDataArrays.FactNames')
 return {'scoped_class':'PTFR.SideJobsS2.SideJobsS2','scoped_data':'PTFR.SideJobsS2.SideJobDataS2','scoped_failure_data':'PTFR.SideJobsS2.SideJobFailureDataS21','methods_verified':checked,'failed_detail_arrays_verified':arrays,'only_owned_admission_setters':True,'diagnostics_read_only':True}

def main(revision):
 build=Path(__file__).resolve().parent/'build'/revision;dest=build/'compile_result.json'
 assert not dest.exists(),'Evidence already exists'
 stage=Path(tempfile.mkdtemp(prefix='compile_',dir=build));cache=stage/'cache';cache.mkdir()
 protected={str(p):sha(p) for p in (GAME/'r6/cache').iterdir() if p.is_file()}
 for name in ('final.redscripts','final.redscripts.ts'):shutil.copy2(GAME/'r6/cache'/name,cache/name)
 deps={}
 for p in (GAME/'r6/scripts').rglob('*.reds'):
  deps[str(p)]=sha(p);target=stage/'scripts'/p.relative_to(GAME/'r6/scripts');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
 source=stage/'scripts/TowerContinued_SideJobs_S2';source.mkdir(exist_ok=True)
 shutil.copy2(build/'SideJobsS2.reds',source/'SideJobsS2.reds')
 plugins=(ROOT/'research/restriction_profiles/implementation_r1/compile_paths.txt').read_text(encoding='utf-8-sig').splitlines()[2:]
 for folder in plugins:
  for p in Path(folder).rglob('*.reds'):deps[str(p)]=sha(p)
 cli=ROOT/'research/finalboards_dismissal/tooling/redscript-cli.exe'
 def run(args,name):
  r=subprocess.run(args,capture_output=True,text=True,timeout=180);log=r.stdout+r.stderr;(stage/name).write_text(log,encoding='utf-8')
  assert r.returncode==0 and 'Output successfully saved' in log and not re.search(r'(?m)^\[?ERROR\b',log),log[-12000:]
  return log
 args=[str(cli),'compile']
 for p in [source,stage/'scripts/PTFR_PreAlpha',GAME/'red4ext/plugins/Codeware/Scripts']:args+=['-s',str(p)]
 args+=['-b',str(cache/'final.redscripts'),'-o',str(stage/'headless.redscripts')]
 run(args,'headless.log')
 paths=stage/'compile_paths.txt';paths.write_text('\n'.join(plugins)+'\n')
 compiled=cache/'compiled.redscripts'
 log=run([str(GAME/'engine/tools/scc.exe'),'-compile',str(stage/'scripts'),'-compilePathsFile',str(paths),'-customCacheDir',str(cache),'-outputCacheFile',str(compiled),str(cache/'final.redscripts')],'scc.log')
 assert 'Compilation complete' in log and 'EquipmentEx.reds' in log
 flat=stage/'compiled.script';run([str(cli),'decompile','-i',str(compiled),'-o',str(flat)],'decompile.log')
 text=re.sub(r'\$local\$\d+','',flat.read_text(encoding='utf-8-sig'))
 assert 'EquipmentEx.OutfitSystem.GetInstance' in text
 bodies=verify_bodies(text,(build/'SideJobsS2.reds').read_text(encoding='utf-8'))
 for p,h in {**protected,**deps}.items():assert sha(p)==h,p
 report={'status':'PASS_NOT_LIVE','build_sha256':sha(build/'build.json'),'compiler_sha256':sha(Path(__file__)),'script_sha256':sha(build/'SideJobsS2.reds'),'compiled_sha256':sha(compiled),'stage':str(stage),'combined_cli':True,'full_scc':True,'equipmentex':True,'body_readback':True,'body_checks':bodies,'protected':protected,'dependencies':deps,'live_files_unchanged':True}
 dest.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('protected','dependencies')},indent=2))

if __name__=='__main__':main(sys.argv[1])
