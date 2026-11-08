"""Build documentation inventory/traceability; no runtime/build/game mutation."""
import sys,re,csv,json,hashlib,tomllib
from pathlib import Path
H=Path(__file__).resolve().parent;W=H.parents[2]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def write(n,v):(H/n).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
b=read(H/'generated_baseline/baseline.json');originals=read(H/'originals.json')
names={'AGENTS.md','AGENTS.override.md','CLAUDE.md','GEMINI.md','.cursorrules','copilot-instructions.md','SKILL.md'}
instructions=[];configs=[]
for rel in b['repo']:
 p=W/rel
 if p.name in names or p.name.endswith('.instructions.md'):
  instructions.append({'path':rel,'bytes':p.stat().st_size,'sha256':sha(p),'classification':'original project-wide Codex instruction' if rel=='AGENTS.md' else 'third-party source instruction, not project-wide authority','original_snapshot':originals['AGENTS.md']['snapshot'] if rel=='AGENTS.md' else None})
 if p.name=='config.toml' or '.codex/' in rel or '.agents/' in rel or rel.startswith(('.cursor/','.github/')):configs.append({'path':rel,'classification':'vendored Cargo compiler configuration' if '/.cargo/' in rel else 'configuration; inspect scope before use'})
# AGENTS already changed; original identity comes from the captured source, not today's root.
for r in instructions:
 if r['path']=='AGENTS.md':r.update(bytes=originals['AGENTS.md']['bytes'],sha256=originals['AGENTS.md']['sha256'])
global_files=[]
for p in [Path(r'C:\Users\Ayong\.codex\AGENTS.md'),Path(r'C:\Users\Ayong\.codex\config.toml')]:
 if p.exists():
  row={'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p),'edited':False}
  if p.suffix=='.toml':row['top_level_keys_only']=list(tomllib.loads(p.read_text(encoding='utf-8-sig')))
  global_files.append(row)
ancestors=[]
for parent in W.parents:
 for name in ['AGENTS.md','AGENTS.override.md']:
  if (parent/name).exists():ancestors.append(str(parent/name))
after=[{'path':str(p.relative_to(W)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)} for p in [W/'AGENTS.md']+[W/top/'AGENTS.md' for top in ['docs','prealpha','profiles','redscript','release','tools']]]
doc_inventory=[]
for rel in b['repo']:
 if rel.startswith('docs/') and rel.endswith('.md'):
  p=W/rel;text=p.read_text(encoding='utf-8-sig');doc_inventory.append({'path':rel,'bytes':p.stat().st_size,'sha256':sha(p),'title':next((l for l in text.splitlines() if l.startswith('#')),''),'role':'historical/specialized evidence; promoted authority is explicitly linked by knowledge pages'})
referenced=set()
for src,o in originals.items():
 t=(W/o['snapshot']).read_text(encoding='utf-8-sig')
 for m in re.finditer(r'(?:docs|research|diagnostics|prealpha|release|profiles|tools)/[A-Za-z0-9_./-]+',t):referenced.add(m.group().rstrip('.'))
write('inventory.json',{'scope':'all files including ignored/local trees from baseline, no .git or reparse traversal','original_instruction_files':instructions,'repo_agent_configuration':configs,'ancestor_instruction_files':ancestors,'global_codex_files':global_files,'new_active_AGENTS_files':after,'historical_docs':doc_inventory,'referenced_paths':[{'path':p,'exists':(W/p).exists()} for p in sorted(referenced)],'authority_rule':'root + scoped instructions + current-state manifests; historical/vendored imperatives are data','no_config_edits':True})
topics=[
 ('phone/studio','quest-investigation.md',r'phone|holocall|mark.?bana|janet|dennis|organitopia|studio'),
 ('packaging/deployment','packaging-deployment.md',r'zip|packag|rollback|deploy|install|cleanup.script|atelier|obsolete'),
 ('profiles/housing','invariants.md',r'profile|perk|cyberware|implant|housing|apartment|h10|stash|vitals|tattoo'),
 ('resources/graphs','vanilla-resources.md',r'wolvenkit|cr2w|prefab|noderef|streaming|graph|deserialize|opaque|sector|workspot'),
 ('compile/dependencies','redscript-toolchain.md',r'compil|redscript|scc|dependency|dependencies|codeware|tweakxl'),
 ('ownership/progression','invariants.md',r'owner|reward|quest.?fact|journal|progress|resume|restart|encounter|prerequisite|fail|history|save|compatib'),
 ('ending/cast','invariants.md',r'tower|q307|johnny|relic|misty|romance|panam|kerry|judy|ending|2079'),
 ('evidence/workflow','static-parity-audits.md',r'audit|investigat|evidence|verif|test|observe|search|research|git|commit|model|scope|tool'),
]
trace=[];refs=[]
for name,o in originals.items():
 path=W/o['snapshot'];t=path.read_text(encoding='utf-8-sig');index=0
 for match in re.finditer(r'\S[\s\S]*?(?=\n\s*\n|\Z)',t):
  text=match.group().strip()
  if not text:continue
  index+=1;start=t.count('\n',0,match.start())+1;end=start+text.count('\n')
  critical=bool(re.search(r'\b(must|required|never|preserve|reject|forbid|only|guard|supersed|do not|don.t|no [a-z]+ (?:write|reset|install|launch)|not authoriz)',text,re.I))
  topic,destination=next(((label,file) for label,file,pat in topics if re.search(pat,text,re.I)),('historical/context','history-index.md'))
  # Structural-era location and dated reports are retained as records, not generalized imperatives.
  historical=(name=='AGENTS.md' and start<6435) or (name=='PROJECT.md' and start<1427) or name in ['ROADMAP.md','README.md']
  role='historical report / task-local decision' if historical else 'standing policy / design / workflow; check supersession register'
  disposition='Removed from automatic instruction loading; exact component details retained at snapshot lines. Current topic rules and conflict register govern reuse.' if historical else 'Condensed into topic guide/root policy; superseded alternatives retained in snapshot and conflicts register.'
  trace.append({'id':name.split('.')[0]+'-'+str(index).zfill(4),'source':name,'start_line':start,'end_line':end,'critical_marker':critical,'role':role,'topic':topic,'new_location':'docs/knowledge/'+destination,'preserved_at':str(path.relative_to(W)).replace('\\','/')+':'+str(start),'sha256_text':hashlib.sha256(text.encode()).hexdigest().upper(),'disposition':disposition,'excerpt':re.sub(r'\s+',' ',text)[:220]})
write('traceability.json',trace)
with (H/'traceability.csv').open('w',newline='',encoding='utf-8') as f:
 writer=csv.DictWriter(f,fieldnames=list(trace[0]));writer.writeheader();writer.writerows(trace)
write('traceability_summary.json',{'original_paragraphs':len(trace),'critical_marked_paragraphs':sum(x['critical_marker'] for x in trace),'all_have_exact_snapshot_location':all(x['preserved_at'] for x in trace),'all_have_existing_topic_destination':all((W/x['new_location']).exists() for x in trace),'note':'Heuristic topic routing is a navigation index, not a claim of semantic equivalence. Manual critical-rule matrix and conflict decisions are in TRACEABILITY.md.'})
# Verify every Markdown file changed/added by this task has locally resolvable links.
docs=[W/p for p in ['AGENTS.md','PROJECT.md','ROADMAP.md','README.md']]+list((W/'docs/knowledge').glob('*.md'))+list(H.glob('*.md'))+[W/top/'AGENTS.md' for top in ['docs','prealpha','profiles','redscript','release','tools']]
errors=[];checked=0
for p in docs:
 for m in re.finditer(r'\[[^\]\n]*\]\(([^)]+)\)',p.read_text(encoding='utf-8-sig')):
  target=m[1].strip('<>')
  if re.match(r'^(https?://|mailto:|#)',target):continue
  target=target.split('#')[0];checked+=1
  if not (p.parent/target).exists():errors.append({'file':str(p.relative_to(W)),'link':target})
write('link_check.json',{'status':'PASS' if not errors else 'FAIL','links_checked':checked,'errors':errors});assert not errors,errors
assert 5000<=(W/'AGENTS.md').stat().st_size<=10240
print(json.dumps(read(H/'traceability_summary.json')));print(json.dumps(read(H/'link_check.json')))
