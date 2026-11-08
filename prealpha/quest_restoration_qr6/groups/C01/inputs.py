"""Pure QR6 worker C inputs. Reads pinned resources; no output effects on import."""
from pathlib import Path
import sys,json,gzip
H=Path(__file__).resolve().parent;W=H.parents[3]
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource,compare_graph,digest
F=W/'prealpha/quest_restoration_qr5';E=read(F/'source_epoch_08.json');C=Path(E['candidate'])
A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';IDX=read(A/'resource_inventory.json');MI=read(A/'model_inventory.json')
U=read(W/'research/gig_restoration/native_gigs_u9/manifest.json');UP={k.replace('\\','/'):v for k,v in U['source_pins'].items()}
B=read(W/'research/gig_restoration/family_b7/build_plan.json');BP={k.replace('\\','/'):v for k,v in B['pins'].items()}
Q=read(F/'queue.json');ROWS={q['id']:q for q in Q['quests']}
D=read(W/'prealpha/gigs_u10/native/build/native_06/component.json');DP={k.replace('\\','/'):v for k,v in D['source_pins'].items()}
ASSIGN={'C01':['sts_hey_gle_03','sts_hey_gle_05','sts_hey_rey_01','sts_hey_rey_02'],'C02':['sts_std_arr_03','sts_wat_nid_07','sts_wbr_hil_06','sts_wbr_jpn_12'],'C03':['q305_postcontent','wst_ep1_09','sts_ep1_12_pickup']}
COMMON=[r'towercontinued\gig_phone_u9\fixer_parent.questphase',r'towercontinued\gig_phone_u9\support_wrapper.questphase',r'towercontinued\gig_phone_u9\fixer_initializer.questphase',r'towercontinued\gig_phone_u9\fixer_cleanup.questphase',r'towercontinued\phone_studios_ph3\studio_support.questphase',r'base\quest\holocalls\holocall_initializers.questphase',r'base\quest\holocalls\holocall_interrupts.questphase']+[f'base\\quest\\holocalls\\{c}\\{c}_{s}' for c in ['padre','muamar','reggie','wakako','rogue'] for s in ['holocall.questphase','holocall.scene','cleanup.questphase']]
def selected(group,extra=()):
 ids=ASSIGN[group];ds=set(COMMON if group!='C03' else [])|set(extra)
 for q in ids:
  row=ROWS[q];ds.update(d for d in row['restored_candidates']+row['vanilla_candidates'] if d in MI)
 for r in U['recipes']+D['recipes']:
  if r.get('id') in ids or any(q in r.get('depot','') for q in ids):
   if r.get('raw'):ds.add('recipe:'+r['raw'])
   if r.get('native'):ds.add(r['native'])
   ds.update(c['depot'] for c in r.get('companions',[]) if c.get('depot'))
 return sorted(d for d in ds if d.startswith('recipe:') or d in MI)
def load(d):
 if d.startswith('recipe:'):
  raw=W/d[7:];j=Path(str(raw).replace('\\raw\\','\\json\\')+'.json');rel=j.relative_to(W).as_posix();expect=UP.get(rel,BP.get(rel,DP.get(rel)));assert expect and sha(j)==expect,(d,j)
  expected_raw=UP.get(raw.relative_to(W).as_posix(),BP.get(raw.relative_to(W).as_posix(),DP.get(raw.relative_to(W).as_posix())))
  if expected_raw:assert sha(raw)==expected_raw
  m=Resource(read(j)).normalize();return m,{'depot':d,'binary':str(raw),'sha256':sha(raw),'json':str(j),'json_sha256':sha(j),'native_manifest_export_pin':expect,'historical_raw_pin':expected_raw,'errors':m['errors']}
 r=IDX[d];j=Path(r['json']);raw=C/'archive_source'/d.replace('\\','/') if d in E['source_resources'] else j.with_suffix('')
 if not raw.is_file():raw=Path(str(j).replace('\\json\\','\\raw\\')).with_suffix('')
 assert raw.is_file() and sha(raw)==r['sha256'],(d,raw,'Fresh readback required if changed')
 if d in E['source_resources']:assert sha(raw)==E['source_resources'][d]
 m=Resource(read(j)).normalize();cached=json.loads(gzip.decompress(Path(MI[d]['normalized_model']).read_bytes()));cached.setdefault('embedded_files',[]);assert m==cached,d
 return m,{'depot':d,'binary':str(raw),'sha256':sha(raw),'json':str(j),'json_sha256':sha(j),'model':MI[d]['normalized_model'],'model_sha256':sha(MI[d]['normalized_model']),'provider':r.get('archive'),'errors':m['errors'],'source_epoch':'QR5:08'}
def run(group,out):
 assert not out.exists();ms={};pins=[]
 for d in selected(group):m,p=load(d);ms[d]=m;pins.append(p)
 write(out/'models.json',ms);write(out/'source_pins.json',pins)
 print({'group':group,'resources':len(ms),'graphs':sum(len(m['graphs']) for m in ms.values()),'out':str(out)})
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--group',choices=ASSIGN,required=True);p.add_argument('--output',required=True);a=p.parse_args();run(a.group,Path(a.output))
