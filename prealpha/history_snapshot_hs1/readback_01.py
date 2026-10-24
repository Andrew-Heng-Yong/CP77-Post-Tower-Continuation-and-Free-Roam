from pathlib import Path
import importlib.util,json,re,hashlib
H=Path(__file__).resolve().parent;O=H/'candidate_01';P=O/'package'
sp=importlib.util.spec_from_file_location('cat',H/'build_catalogue_01.py');cat=importlib.util.module_from_spec(sp);sp.loader.exec_module(cat)
text=(O/'compile_04/compiled.script').read_text(encoding='utf-8-sig')
source=(H/'SnapshotStateHS1.reds').read_text()
def norm(s):
 s=re.sub(r'PTFR\.\w+\.', '',s);s=re.sub(r'\$local\$\d+','',s);s=s.replace("\\'", "'")
 return re.sub(r'\s+','',s)
checks=[]
for cls,methods in [('SnapshotStateHS1',['Ready','CanExport','Allows','FreshU9','FamilyPrerequisite']),('SnapshotRecoveryHS1',['BaseReady','ExactFailedPreparation'])]:
 original=cat.block(source,r'public class '+cls+r' extends ScriptableSystem\s*\{')
 compiled=cat.block(text,r'public class PTFR.HistorySnapshotHS1.'+cls+r' extends ScriptableSystem\s*\{')
 for method in methods:
  a=re.findall(r'\breturn\s+([^;]+);',cat.body(original,method));b=re.findall(r'\breturn\s+([^;]+);',cat.body(compiled,method))
  assert [norm(x) for x in a]==[norm(x) for x in b],(cls,method,a,b)
  checks.append(cls+'.'+method)
 fields=lambda s:re.findall(r'\bpersistent let (\w+):',s)
 assert fields(original)==fields(compiled),cls
 checks.append(cls+'.persistent-fields')
row=cat.block(text,r'public struct PTFR.HistorySnapshotHS1.SnapshotRowHS1\s*\{')
for field in ['states','facts','counters','optional','tracked','stable','legacyCertified']:assert re.search(r'persistent let '+field+r':',row),field
data=cat.block(text,r'public abstract class PTFR.HistorySnapshotHS1.SnapshotDataHS1 extends IScriptable\s*\{')
rows=json.loads((O/'catalogue.json').read_text())['rows'];arrays=0;strings=0
for i,row in enumerate(rows):
 for method,expected in [('Paths',[p[0] for p in row['journals']]),('Classes',[p[1] for p in row['journals']]),('Facts',row['facts'])]:
  b=cat.body(data,method+str(i));resize=re.search(r'ArrayResize\((synthetic\$\d+),\s*(\d+)u\)',b)
  if not expected:
   assert not re.search(r'\[\d+u\]\s*=',b)
   if resize:assert int(resize.group(2))==0
  else:
   assert resize and int(resize.group(2))==len(expected),(method,i)
   assignments=re.findall(re.escape(resize.group(1))+r'\[(\d+)u\]\s*=\s*("(?:[^"\\]|\\.)*");',b)
   actual=[(int(k),json.loads(v.replace("\\'","'"))) for k,v in assignments]
   assert actual==list(enumerate(expected)),(method,i)
  arrays+=1
 for method,expected in [('ID',row['id']),('MetadataJSON',json.dumps({'id':row['id'],'title':row['title'],'journals':row['journals'],'fact_names':row['facts'],'coverage':'installed_catalogue' if row['sources'] else 'selected_root_only'},ensure_ascii=True,separators=(',',':')))]:
  b=cat.body(data,method+str(i));m=re.search(r'return\s+("(?:[^"\\]|\\.)*");',b);assert m
  assert json.loads(m.group(1).replace("\\'","'"))==expected,(method,i);strings+=1
recovery=cat.block(text,r'public class PTFR.HistorySnapshotHS1.SnapshotRecoveryHS1 extends ScriptableSystem\s*\{')
assert re.findall(r'SetOwned\(n"([^"]+)",\s*(\d+)\)',recovery)==[('PTFRPA2_Fault','0'),('PTFRPA2_Finished','1')]
pol=norm(cat.body(recovery,'Poll'))
assert pol.index('this.originalFault=2')<pol.index('this.SetOwned(n"PTFRPA2_Fault",0)')
assert 'this.Fact(n"PTFRPA2_Prepared")!=1' in pol and 'this.Fact(n"PTFRPA2_Reveal")!=1' in pol
assert '!arrival.Completed()' in pol and '!housing.HousingReadyForReveal()' in pol and '!profile.PTFRPAComplete()' in pol
assert 'if(this.SetOwned(n"PTFRPA2_Finished",1))' in pol or 'ifthis.SetOwned(n"PTFRPA2_Finished",1)' in pol
checks.append('recovery receipt precedes clear; completion barrier remains compiled')
sources={str(p):cat.sha(p) for p in P.rglob('*') if p.is_file()}
out={'status':'PASS_COMPILED_READBACK_NOT_LIVE','methods_and_schemas':checks,'catalogue_arrays':arrays,'catalogue_strings':strings,'sources':sources,'compiled_sha256':cat.sha(O/'compile_04/cache/compiled.redscripts')}
path=O/'readback_01.json';assert not path.exists();path.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='sources'}))
