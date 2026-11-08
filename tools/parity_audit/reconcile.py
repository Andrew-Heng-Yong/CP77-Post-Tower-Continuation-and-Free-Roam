"""Independent root/manifest catalogue cross-check and inherited-reference triage."""
from common import *
from engine import Models
import collections,sys
def reconcile(base,o,identity_path=None):
 cat=read(o/'catalogues.json');q=read(o/'queries.json');regs=read(o/'registration_inventory.json')['bindings'];idx=read(o/'resource_inventory.json');pairs=read(o/'resource_parity.json');pairmap={r['private']:r for r in pairs};declared=collections.defaultdict(list);sources=[]
 for rec in q['metadata_sources']:
  p=Path(rec['path']);j=read(p);sources.append({'path':str(p),'sha256':sha(p),'matches_discovery_pin':sha(p)==rec['sha256']})
  for row in j.get('recipes',[])+j.get('jobs',[]):
   if isinstance(row,dict) and row.get('id'):declared[row['id']].append({'source':str(p),'native':row.get('native'),'scope':'Historical source declaration; not executing-owner proof'})
  for k,v in j.get('quests',{}).items():declared[k].append({'source':str(p),'native':v,'scope':'Historical source declaration'})
 results=[];unmatched=[]
 for quest in cat['quests']:
  qid=quest['id'];short=re.match(r'^(mq\d+|sq\d+)',qid);short=short[0] if short else qid
  def match(d):return qid in d or (short!=qid and bool(re.search(r'(?<![a-z0-9])'+short+r'(?!\d)',d)))
  roots=[r for r in regs if match(r['path'])];entry=[r for r in roots if re.search(r'entr(?:y|ies)|resume|fresh',r['path'],re.I)];results.append({'id':qid,'selection':quest['decision'],'held':quest['held'],'has_requirements':bool(quest.get('requirements')),'source_declarations':declared[qid],'installed_root_candidates':roots,'installed_entry_candidates':entry,'status':'CONDITIONAL' if declared[qid] or entry else 'UNKNOWN','limit':'Manifest/root/ID candidates independently corroborate catalogue identity; source presence never establishes native gate feasibility or executing-owner liveness'})
 for r in regs:
  if re.search(r'entr(?:y|ies)|resume|fresh',r['path'],re.I) and not any(r in x['installed_entry_candidates'] for x in results):unmatched.append(r)
 write(o/'catalogue_reconciliation.json',{'derived_selection':dict(collections.Counter(x['selection'] for x in results)),'source_pins':sources,'per_quest':results,'registry_ids_missing_declaration_and_entry':[r['id'] for r in results if r['selection']=='INCLUDE' and r['status']=='UNKNOWN'],'entry_like_bindings_not_mapped':unmatched,'declared_ids_outside_registry':sorted(set(declared)-{r['id'] for r in cat['quests']}),'limit':'Historical declarations are discovery candidates, not current admissions. Unmapped bindings remain unresolved; shared/support owners can resemble quest entries.'});csvwrite(o/'catalogue_reconciliation.csv',[{'id':r['id'],'selection':r['selection'],'held':r['held'],'status':r['status'],'declarations':len(r['source_declarations']),'root_candidates':len(r['installed_root_candidates']),'entry_candidates':len(r['installed_entry_candidates'])} for r in results])
 if identity_path:
  from identity_registry import bind_registry
  identity=bind_registry(read(identity_path),{r['depot']:r['sha256'] for r in q['private']},{r['id'] for r in results if r['selection']=='INCLUDE'})
  write(o/'identity_registry_corroboration.json',{'registry':str(identity_path),'registry_sha256':sha(identity_path),'corroborated_ids':sorted(identity),'remaining_selected_ids':sorted({r['id'] for r in results if r['selection']=='INCLUDE'}-set(identity)),'mappings':identity,'scope':'Identity/source correlation only, not quest correctness, lifecycle verification or permission to activate excluded content'})
 deps=read(o/'dependency_inventory.json');triage=[]
 for r in deps:
  if r['status']=='RESOLVED_PRESENCE':continue
  d=r['resource'];target=r['target'];p=pairmap.get(d,{});n=p.get('native');native_refs=set(idx.get(n,{}).get('refs',[]));private=idx[d].get('private',False)
  kind='EMBEDDED_OWNER_CONDITIONAL' if r['status']=='CONDITIONAL_EMBEDDED' else ('INHERITED_NATIVE_REFERENCE' if private and target in native_refs else 'PRIVATE_UNRESOLVED_WITHOUT_PROVED_ORIGIN' if private else 'NATIVE_BASELINE_REFERENCE_UNRESOLVED')
  triage.append({**r,'origin':kind,'native_identity_candidate':n,'limit':'Archive-only presence/lifetime evidence; localization, loose files, cuts and shared ownership require further review'})
 write(o/'dependency_discrepancy_triage.json',triage);write(o/'dependency_triage_summary.json',dict(collections.Counter(r['origin'] for r in triage)));print(json.dumps({'catalogue_rows':len(results),'unmapped_entry_like':len(unmatched),'dependency_origins':dict(collections.Counter(r['origin'] for r in triage))}))
if __name__=='__main__':reconcile(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]) if len(sys.argv)>3 else None)
