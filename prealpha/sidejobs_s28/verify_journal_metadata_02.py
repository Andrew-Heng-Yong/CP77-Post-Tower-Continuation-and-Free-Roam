"""Current2.5 path/class metadata proof; explicit unused mappin enum omissions only.

These resources are NOT shipped or overridden. Only the used journal path/class
metadata is compared; this does not claim the two whole journals are equivalent.
"""
import argparse,hashlib,json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'prealpha/sidejobs_s23'))
from audit import walk
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def catalog(path):
 d=read(path);h={x['HandleId']:x['Data'] for x in walk(d) if 'HandleId' in x and 'Data' in x};out={}
 def visit(w,p):
  n=w.get('Data',h.get(w.get('HandleRefId'),w));k=n.get('id','');p=p+([k] if k else [])
  if n.get('$type','').startswith('gameJournal'):out['/'.join(p)]=n['$type']
  for child in n.get('entries',[]):visit(child,p)
 visit(d['Data']['RootChunk']['entry'],[]);return out
def main():
 a=argparse.ArgumentParser();a.add_argument('--contracts',nargs='+',required=True);a.add_argument('--output',required=True);args=a.parse_args()
 extraction='research/sidejobs_s28/journal_variants_05/extraction.json';e=read(ROOT/extraction)
 pins={extraction:sha(ROOT/extraction),e['source']:sha(ROOT/e['source'])};wanted={}
 assert pins[e['source']]==e['source_sha256']
 assert e['status']=='EXTRACTED_CURRENT_JOURNAL_PATH_CLASS_METADATA_ONLY' and e['script_sha256']==sha(ROOT/e['script'])
 assert len(e['variants'])==2 and len(e['ep1_variants'])==1
 for v in e['variants']+e['ep1_variants']:
  assert v['metadata_only'] is True
  for ignored in v['ignored_enums']:
   assert ignored['enum_type']=='WolvenKit.RED4.Types.Enums+gamedataMappinVariant' and ignored['original'] in ('Zzz22_CityTourLandmark','Zzz21_ServicePointGlamdocVariant') and ignored['metadata_placeholder']==0
 for rel in ('prealpha/sidejobs_s28/verify_journal_metadata_02.py','prealpha/sidejobs_s23/audit.py','tools/catalog_gig_rollout_r2.py','prealpha/sidejobs_s28/extract_journals_05.ps1','tools/build_phase2a.ps1'):
  pins[rel]=sha(ROOT/rel)
 for rel in args.contracts:
  c=read(ROOT/rel);pins[rel]=sha(ROOT/rel)
  for o in c.get('owners',[c]):
   for j in o['journals']:
    assert j['path'] not in wanted or wanted[j['path']]==j['class'];wanted[j['path']]=j['class']
   contact=o.get('contact') or o.get('contact_target') or (o.get('contact_copy') or {}).get('path')
   if contact:wanted[contact]='gameJournalContact'
 variants=[]
 for v in e['variants']:
  assert sha(ROOT/v['raw'])==v['sha256'];assert sha(ROOT/v['json'])==v['json_sha256']
  pins[v['raw']]=v['sha256'];pins[v['json']]=v['json_sha256'];cat=catalog(ROOT/v['json'])
  checks=[]
  for path,cls in wanted.items():
   if path.startswith('ep1/'):continue
   assert cat.get(path)==cls,(v['archive'],path,cls,cat.get(path));checks.append({'path':path,'class':cls})
  variants.append(v|{'metadata_checks':len(checks),'metadata_sha256':hashlib.sha256(json.dumps(checks,sort_keys=True).encode()).hexdigest().upper()})
 assert len({x['metadata_sha256'] for x in variants})==1
 ep1variants=[];ep1checks=[]
 for v in e['ep1_variants']:
  assert sha(ROOT/v['raw'])==v['sha256'] and sha(ROOT/v['json'])==v['json_sha256']
  pins[v['raw']]=v['sha256'];pins[v['json']]=v['json_sha256'];cat=catalog(ROOT/v['json']);checks=[]
  for path,cls in wanted.items():
   if not path.startswith('ep1/'):continue
   assert cat.get(path)==cls,(path,cls,cat.get(path));checks.append({'path':path,'class':cls})
  ep1checks=checks;ep1variants.append(v|{'metadata_checks':len(checks),'metadata_sha256':hashlib.sha256(json.dumps(checks,sort_keys=True).encode()).hexdigest().upper()})
 result={'status':'PASS_USED_JOURNAL_METADATA_ALL_VARIANTS','contracts':args.contracts,'source_pins':pins,'metadata_only_depot':e['depot'],'source':e['source'],'source_sha256':e['source_sha256'],'variants':variants,'ep1_variants':ep1variants,'extraction':extraction,'current_archives':e['archives'],'metadata_decode_omissions':{'enum_type':'gamedataMappinVariant','allowed_names':['Zzz22_CityTourLandmark','Zzz21_ServicePointGlamdocVariant'],'reason':'Unused mappin appearance enum fields only; needed path/class/tree fields remain native and unchanged. No journal payload is shipped.'},'base_paths':[{'path':p,'class':c} for p,c in wanted.items() if not p.startswith('ep1/')],'ep1_paths':ep1checks,'ep1_metadata_checks':len(ep1checks),'total_used_paths':len(wanted),'verifier_sha256':sha(Path(__file__)),'scope':'Current2.5 exact official-archive raw variants separately extracted and pinned. Metadata-only parsing substitutes numeric0 for two exact new unused mappin appearance enums and rejects other parse events; every occurrence is recorded. Every guarded/contact path and class exists identically in BOTH base journal variants. EP1 journal paths checked separately. These journals are metadata-only build evidence, never shipped or overridden; whole-journal byte equivalence is NOT claimed. All gameplay resource byte identity still mandatory.'}
 dest=ROOT/args.output;assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('status','total_used_paths','ep1_metadata_checks')}))
if __name__=='__main__':main()
