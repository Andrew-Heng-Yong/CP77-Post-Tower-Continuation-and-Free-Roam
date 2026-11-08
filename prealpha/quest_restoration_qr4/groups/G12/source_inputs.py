from pathlib import Path
import sys,json,gzip
W=Path(__file__).resolve().parents[4];sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
from model import Resource
A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';IDX=read(A/'resource_inventory.json');MI=read(A/'model_inventory.json');C=W/'prealpha/quest_restoration_qr3/candidate_01';U=read(W/'research/gig_restoration/native_gigs_u9/manifest.json');PLAN=W/'research/gig_restoration/family_b7/build_plan.json';assert sha(PLAN)==U['source_pins'][PLAN.relative_to(W).as_posix()];B7=read(PLAN)
Q=['sts_hey_gle_06','sts_hey_gle_01'];GL='recipe:research/gig_restoration/expanded_sources/raw/base/open_world/street_stories/heywood/glenn/sts_hey_glenn.questphase';PAD='recipe:research/gig_restoration/family_b7/fixers/raw/base/open_world/fixers/padre/phases/padre.questphase';LOOP='recipe:research/gig_restoration/lifecycle_sources/raw/base/open_world/street_stories/street_stories_new_fixer_loop.questphase'
HC='base\\quest\\holocalls\\padre\\padre_holocall.questphase';HS='base\\quest\\holocalls\\padre\\padre_holocall.scene';CL='base\\quest\\holocalls\\padre\\padre_cleanup.questphase'
def selected():return sorted({d for d,r in IDX.items()if r.get('graphs')and(any(q in d for q in Q)or d in [HC,HS,CL,'towercontinued\\gig_phone_u9\\fixer_parent.questphase','towercontinued\\gig_phone_u9\\fixer_initializer.questphase','towercontinued\\gig_phone_u9\\fixer_cleanup.questphase'])})+[GL,PAD,LOOP]
def load(d):
 if d.startswith('recipe:'):
  raw=W/d[7:];j=Path(str(raw).replace('\\raw\\','\\json\\')+'.json');rel=j.relative_to(W).as_posix();expected=U['source_pins'].get(rel,B7['pins'].get(str(j.relative_to(W))));assert expected and sha(j)==expected,rel
  m=Resource(read(j)).normalize();return m,{'depot':d,'binary':str(raw),'sha256':sha(raw),'json':str(j),'json_sha256':sha(j),'role':'exact U9 original recipe JSON pin; binary/export correspondence reused from existing extraction, current provider precedence not newly resolved','errors':m['errors']}
 r=IDX[d];j=Path(r['json']);raw=C/'archive_source'/Path(d.replace('\\','/'))if d.startswith('towercontinued\\')else j.with_suffix('')
 if not raw.is_file():raw=Path(str(j).replace('\\json\\','\\raw\\')).with_suffix('')
 assert raw.is_file()and sha(raw)==r['sha256'],d
 m=Resource(read(j)).normalize();cached=json.loads(gzip.decompress(Path(MI[d]['normalized_model']).read_bytes()));cached.setdefault('embedded_files',[]);assert m==cached,d
 return m,{'depot':d,'binary':str(raw),'sha256':sha(raw),'json':str(j),'json_sha256':sha(j),'model':MI[d]['normalized_model'],'model_sha256':sha(MI[d]['normalized_model']),'errors':m['errors']}
if __name__=='__main__':
 O=Path(__file__).resolve().parent/'inspection_01';assert not O.exists();ms={};ps=[]
 for d in selected():m,p=load(d);ms[d]=m;ps.append(p)
 write(O/'models.json',ms);write(O/'pins.json',ps);print({'resources':len(ps),'nodes':sum(len(g['nodes'])for m in ms.values()for g in m['graphs'].values())})
