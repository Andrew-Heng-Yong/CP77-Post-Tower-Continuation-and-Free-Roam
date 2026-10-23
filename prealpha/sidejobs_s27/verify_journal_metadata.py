"""Narrow metadata proof for two official cooked-base-journal byte variants.

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
 extraction='research/sidejobs_s24/ep1/journal_variants_01/extraction.json';e=read(ROOT/extraction)
 pins={extraction:sha(ROOT/extraction),e['source']:sha(ROOT/e['source'])};wanted={}
 assert pins[e['source']]==e['source_sha256']
 for rel in ('prealpha/sidejobs_s27/verify_journal_metadata.py','prealpha/sidejobs_s23/audit.py','tools/catalog_gig_rollout_r2.py','prealpha/ncpd_scanner_n1/native_inspect.py','tools/audit_activity_batches_b1.py','prealpha/sidejobs_s24/ep1/verify_journal_variants.ps1','prealpha/sidejobs_s24/ep1/extract.ps1','prealpha/sidejobs_s24/ep1/extract_journals.ps1','tools/extract_resources.ps1'):
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
 ep1rel='research/sidejobs_s24/ep1/native_02/json/ep1/journal/cooked_journal.journal.json';cat=catalog(ROOT/ep1rel);pins[ep1rel]=sha(ROOT/ep1rel)
 ep1checks=[]
 for path,cls in wanted.items():
  if not path.startswith('ep1/'):continue
  assert cat.get(path)==cls,(path,cls,cat.get(path));ep1checks.append({'path':path,'class':cls})
 result={'status':'PASS_USED_JOURNAL_METADATA_ALL_VARIANTS','contracts':args.contracts,'source_pins':pins,'metadata_only_depot':e['depot'],'source':e['source'],'source_sha256':e['source_sha256'],'variants':variants,'base_paths':[{'path':p,'class':c} for p,c in wanted.items() if not p.startswith('ep1/')],'ep1_paths':ep1checks,'ep1_metadata_checks':len(ep1checks),'total_used_paths':len(wanted),'verifier_sha256':sha(Path(__file__)),'scope':'Exact official-archive variants separately extracted and pinned. Every guarded/contact path and class exists identically in BOTH base journal variants. EP1 journal paths checked separately. These journals are metadata-only build evidence, never shipped or overridden; whole-journal byte equivalence is NOT claimed. All gameplay resource byte identity still mandatory.'}
 dest=ROOT/args.output;assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('status','total_used_paths','ep1_metadata_checks')}))
if __name__=='__main__':main()
