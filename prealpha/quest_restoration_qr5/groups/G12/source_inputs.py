"""Pure QR5/G12 inputs. All writes remain in this group; no runtime imports."""
from pathlib import Path
import sys,json,gzip
W=Path(__file__).resolve().parents[4];H=Path(__file__).resolve().parent;sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
from model import Resource
A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';IDX=read(A/'resource_inventory.json');MI=read(A/'model_inventory.json');E=read(W/'prealpha/quest_restoration_qr5/source_epoch_00.json');C=Path(E['candidate']);Q=read(W/'prealpha/quest_restoration_qr5/progress.json')['groups']['G12']['ids'];U=read(W/'research/gig_restoration/native_gigs_u9/manifest.json');PLAN=W/'research/gig_restoration/family_b7/build_plan.json';assert sha(PLAN)==U['source_pins'][PLAN.relative_to(W).as_posix()];B7=read(PLAN)
HC='base\\quest\\holocalls\\reggie\\reggie_holocall.questphase';HS='base\\quest\\holocalls\\reggie\\reggie_holocall.scene';CL='base\\quest\\holocalls\\reggie\\reggie_cleanup.questphase';CAP='recipe:research/gig_restoration/family_b7/fixers/raw/base/open_world/fixers/reggie/phases/reggie.questphase';LOOP='recipe:research/gig_restoration/lifecycle_sources/raw/base/open_world/street_stories/street_stories_new_fixer_loop.questphase'
COMMON=[HC,HS,CL,'towercontinued\\gig_phone_u9\\support_wrapper.questphase','towercontinued\\gig_phone_u9\\fixer_parent.questphase','towercontinued\\gig_phone_u9\\fixer_initializer.questphase','towercontinued\\gig_phone_u9\\fixer_cleanup.questphase','towercontinued\\phone_studios_ph3\\studio_support.questphase','base\\quest\\holocalls\\holocall_initializers.questphase','base\\quest\\holocalls\\holocall_interrupts.questphase',CAP,LOOP]
RECIPES=[r for r in U['recipes']if r.get('id')in Q]
EXTRA=[]
def selected():return sorted({d for d,r in IDX.items()if r.get('graphs')and any(q in d for q in Q)}|set(COMMON)|set(EXTRA)|{'recipe:'+r['raw']for r in RECIPES})
def load(d):
 if d.startswith('recipe:'):
  raw=W/d[7:];j=Path(str(raw).replace('\\raw\\','\\json\\')+'.json');rel=j.relative_to(W).as_posix();expected=U['source_pins'].get(rel,B7['pins'].get(str(j.relative_to(W))));assert expected and sha(j)==expected,rel
  m=Resource(read(j)).normalize();return m,{'depot':d,'binary':str(raw),'sha256':sha(raw),'json':str(j),'json_sha256':sha(j),'role':'Exact U9/B7 original extraction pin; raw/export relationship reused, not a new provider scan','errors':m['errors']}
 r=IDX[d];j=Path(r['json']);raw=C/'archive_source'/Path(d.replace('\\','/'))if d.startswith('towercontinued\\')else j.with_suffix('')
 if not raw.is_file():raw=Path(str(j).replace('\\json\\','\\raw\\')).with_suffix('')
 assert raw.is_file()and sha(raw)==r['sha256'],d
 if d.startswith('towercontinued\\'):assert sha(raw)==E['source_resources'][d],d
 m=Resource(read(j)).normalize();cached=json.loads(gzip.decompress(Path(MI[d]['normalized_model']).read_bytes()));cached.setdefault('embedded_files',[]);assert json.loads(json.dumps(m))==cached,d
 return m,{'depot':d,'binary':str(raw),'sha256':sha(raw),'json':str(j),'json_sha256':sha(j),'model':MI[d]['normalized_model'],'model_sha256':sha(MI[d]['normalized_model']),'provider':r['archive'],'errors':m['errors'],'source_epoch':'QR5epoch00=currentQR4candidate/epoch03; relevant payload unchanged'}
if __name__=='__main__':
 O=H/'inspection_01';assert not O.exists();ms={};pins=[]
 for d in selected():m,p=load(d);ms[d]=m;pins.append(p)
 write(O/'models.json',ms);write(O/'pins.json',pins);print({'resources':len(pins),'nodes':sum(len(g['nodes'])for m in ms.values()for g in m['graphs'].values()),'quests':Q})
