"""Pinned REDscript identity/dependency inventory, lexical and explicitly bounded."""
from common import *
import collections
def inventory(w,o):
 prep=read(o/'prepared.json');manifest=read(prep['manifest']);candidate=Path(prep['candidate']);files=[];fields=[];classes=[];symbols=[];refs=[]
 for r in manifest['package_files']:
  if not r['path'].endswith('.reds'):continue
  p=candidate/'package'/r['path'];assert sha(p)==r['after'];text=p.read_text(encoding='utf-8-sig');cl=None
  files.append({'path':str(p),'installed_path':str(Path(prep['game'])/r['path']),'sha256':sha(p),'lines':len(text.splitlines())})
  for line_no,line in enumerate(text.splitlines(),1):
   c=re.search(r'\bclass\s+(\w+)\s*(?:extends\s+(\w+))?',line)
   if c:cl=c[1];classes.append({'class':cl,'extends':c[2],'path':str(p),'line':line_no})
   f=re.search(r'\b(persistent\s+)?let\s+(\w+)\s*:\s*([^;=]+)',line)
   if f and f[1]:fields.append({'class_context':cl,'name':f[2],'type':f[3].strip(),'path':str(p),'line':line_no,'declaration':line.strip(),'status':'LIVE_ONLY','limit':'Lexical class context; save serialization/migration not decoded'})
   for match in re.finditer(r'"((?:PTFR|holo_|audio_|q\d|sq\d|mq\d|sts_)[^"\r\n]*)"',line):symbols.append({'symbol':match[1],'path':str(p),'line':line_no})
   for match in re.finditer(r'"([^"\r\n]+\.(?:questphase|scene|ent|streamingblock))"',line):refs.append({'depot_literal':match[1].replace('\\\\','\\'),'path':str(p),'line':line_no})
 baseline_path=w/'release/persistence-v0.2.0-beta.json';baseline=read(baseline_path);current={r['path']:r['after'] for r in manifest['package_files']};resources={r['depot']:r['sha256'] for r in read(o/'queries.json')['private']};script_pins=[{'path':r['path'],'old_sha256':r['sha256'],'current_sha256':current.get(r['path']),'status':'PASS' if current.get(r['path'])==r['sha256'] else 'UNKNOWN'} for r in baseline['scripts']];resource_changes=[{'depot':r['depot'],'old_sha256':r['sha256'],'current_sha256':resources.get(r['depot']),'status':'UNKNOWN' if resources.get(r['depot']) else 'FAIL'} for r in baseline['native_resources'] if resources.get(r['depot'])!=r['sha256']]
 result={'scope':'Exact PH3 packaged REDscript lexical inventory; not a compiler, fact-flow solver or save parser','files':files,'classes':classes,'persistent_fields':fields,'fact_or_resource_symbols':symbols,'dynamic_resource_literals':refs,'persistence_baseline':{'path':str(baseline_path),'sha256':sha(baseline_path),'scripts':script_pins,'resource_changes_requiring_identity_review':resource_changes,'resources_checked':len(baseline['native_resources']),'limit':'Unchanged bytes preserve declarations/IDs; this does not establish serialized instance or owner liveness'},'unresolved':['Runtime-generated strings and macro expansion are not resolved','Saved-owner instances, serialized state and migration compatibility require separate evidence','No compile or game execution performed']}
 write(o/'source_identity_inventory.json',result);csvwrite(o/'persistent_fields.csv',fields);print(json.dumps({'reds_files':len(files),'persistent_fields':len(fields),'classes':len(classes),'symbols':len(symbols),'resource_literals':len(refs)}))
if __name__=='__main__':
 import sys
 inventory(Path.cwd(),Path(sys.argv[1]))
