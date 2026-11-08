"""Pure QR5 G01 input loader. Explicit current epoch/raw/native provenance."""
from pathlib import Path
import sys,json,gzip
W=Path(__file__).resolve().parents[4];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
from model import Resource
F=W/'prealpha/quest_restoration_qr5';E=read(F/'source_epoch_00.json');C=Path(E['candidate']);A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';IDX=read(A/'resource_inventory.json');MI=read(A/'model_inventory.json');U=read(W/'research/gig_restoration/native_gigs_u9/manifest.json');UP={k.replace('\\','/'):v for k,v in U['source_pins'].items()};BP=W/'research/gig_restoration/family_b7/build_plan.json';assert sha(BP)==UP[BP.relative_to(W).as_posix()];B7=read(BP);B7P={k.replace('\\','/'):v for k,v in B7['pins'].items()}
Q=['sts_hey_gle_04','sts_hey_rey_09','sts_hey_rey_06','sts_hey_rey_08'];QUEUE=read(W/'prealpha/quest_restoration_qr4/queue.json');ROWS={q['id']:q for q in QUEUE['quests'] if q['id'] in Q};RECIPES=[r for r in U['recipes'] if r.get('id')in Q]
COMMON=[r'towercontinued\gig_phone_u9\fixer_parent.questphase',r'towercontinued\gig_phone_u9\support_wrapper.questphase',r'towercontinued\gig_phone_u9\fixer_initializer.questphase',r'towercontinued\gig_phone_u9\fixer_cleanup.questphase',r'towercontinued\phone_studios_ph3\studio_support.questphase',r'base\quest\holocalls\holocall_initializers.questphase']+[f'base\\quest\\holocalls\\{c}\\{c}_{s}' for c in ['padre','wakako'] for s in ['holocall.questphase','holocall.scene','cleanup.questphase']]
def selected():
 ds=set(COMMON)
 for row in ROWS.values():
  ds.update(row['restored_candidates']);ds.update(d for d in row['vanilla_candidates'] if d in MI)
 ds.update('recipe:'+r['raw'] for r in RECIPES)
 # Full actual body and explicit native prestate companion, not inferred ID list.
 for r in RECIPES:
  if r.get('native'):ds.add(r['native'])
  ds.update(c['depot'] for c in r.get('companions',[]))
 return sorted(ds)
def load(d):
 if d.startswith('recipe:'):
  rel=d[7:];raw=W/rel;j=Path(str(raw).replace('\\raw\\','\\json\\')+'.json');jr=j.relative_to(W).as_posix();expected=UP.get(jr,B7P.get(jr));assert expected and sha(j)==expected,(d,jr,'Missing original JSON pin: use fresh explicit readback, never invent pin')
  raw_expected=UP.get(rel,B7P.get(rel));assert raw.is_file() and (raw_expected is None or sha(raw)==raw_expected),d
  m=Resource(read(j)).normalize();return m,dict(depot=d,binary=str(raw),sha256=sha(raw),json=str(j),json_sha256=sha(j),historical_raw_sha256=raw_expected,provenance='Exact original manifest JSON; raw measured-only if historical_raw_sha256 null',errors=m['errors'])
 r=IDX[d];j=Path(r['json']);raw=C/'archive_source'/d.replace('\\','/') if d in E['source_resources'] else j.with_suffix('')
 if not raw.is_file():raw=Path(str(j).replace('\\json\\','\\raw\\')).with_suffix('')
 assert raw.is_file() and sha(raw)==r['sha256'],(d,'Indexed baseline not equal effective QR4 bytes; load actual corrected JSON if affected')
 if d in E['source_resources']:assert sha(raw)==E['source_resources'][d],d
 m=Resource(read(j)).normalize();cached=json.loads(gzip.decompress(Path(MI[d]['normalized_model']).read_bytes()));cached.setdefault('embedded_files',[]);assert m==cached,d
 return m,dict(depot=d,binary=str(raw),sha256=sha(raw),json=str(j),json_sha256=sha(j),model=MI[d]['normalized_model'],model_sha256=sha(MI[d]['normalized_model']),provider=r.get('archive'),errors=m['errors'])
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();out=Path(a.output).resolve();assert not out.exists();models={};pins=[]
 for d in selected():m,p=load(d);models[d]=m;pins.append(p)
 write(out/'models.json',models);write(out/'source_pins.json',pins);print(json.dumps(dict(resources=len(models),nodes=sum(len(g['nodes']) for m in models.values() for g in m['graphs'].values()))))
