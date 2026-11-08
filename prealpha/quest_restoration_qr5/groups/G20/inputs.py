"""QR5 G20 EP1 gig source pins; existing verified raw inputs, fresh evidence only."""
from pathlib import Path
import sys,json,gzip
W=Path(__file__).resolve().parents[4];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
from model import Resource
IDX=read(W/'diagnostics/vanilla_parity_20261029_01/analysis_02/resource_inventory.json');MI=read(W/'diagnostics/vanilla_parity_20261029_01/analysis_02/model_inventory.json');E=read(W/'prealpha/quest_restoration_qr5/source_epoch_00.json');C=Path(E['candidate']);Q=read(W/'prealpha/quest_restoration_qr5/progress.json')['groups']['G20']['ids'];U=read(W/'research/gig_restoration/native_gigs_u9/manifest.json');REC=[r for r in U['recipes']if r['id']in Q]
HC='base\\quest\\holocalls\\mr_hands\\mr_hands_holocall.questphase';HS='base\\quest\\holocalls\\mr_hands\\mr_hands_holocall.scene';CL='base\\quest\\holocalls\\mr_hands\\mr_hands_cleanup.questphase'
COMMON=[HC,HS,CL,'towercontinued\\gig_phone_u9\\support_wrapper.questphase','towercontinued\\gig_phone_u9\\fixer_parent.questphase','towercontinued\\gig_phone_u9\\fixer_initializer.questphase','towercontinued\\gig_phone_u9\\fixer_cleanup.questphase','towercontinued\\phone_studios_ph3\\studio_support.questphase','ep1\\quest\\ep1.questphase','ep1\\openworld\\ep1_open_world.questphase']
def selected():return sorted({d for d,r in IDX.items()if r.get('graphs')and any(q in d for q in Q)}|set(COMMON)|{'recipe:'+r['raw']for r in REC})
def load(d):
 if d.startswith('recipe:'):
  raw=W/d[7:];j=Path(str(raw).replace('\\raw\\','\\json\\')+'.json');rel=j.relative_to(W).as_posix();expected=U['source_pins'].get(rel);assert expected and sha(j)==expected,rel;m=Resource(read(j)).normalize();return m,{'depot':d,'raw':str(raw),'raw_sha256':sha(raw),'json':str(j),'json_sha256':sha(j),'original_pin':'Exact U9 original recipe JSON; existing extraction, not new provider scan','errors':m['errors']}
 r=IDX[d];j=Path(r['json']);raw=C/'archive_source'/Path(d.replace('\\','/'))if d in E['source_resources']else j.with_suffix('')
 if not raw.is_file():raw=Path(str(j).replace('\\json\\','\\raw\\')).with_suffix('')
 assert raw.is_file()and sha(raw)==r['sha256'],d
 if d in E['source_resources']:assert sha(raw)==E['source_resources'][d],d
 m=Resource(read(j)).normalize();return m,{'depot':d,'raw':str(raw),'raw_sha256':sha(raw),'json':str(j),'json_sha256':sha(j),'provider':r['archive'],'errors':m['errors'],'epoch':'QR5epoch00; G20 payloads unchanged in canonical05'}
if __name__=='__main__':
 O=H/'inspection_01';assert not O.exists();M={};pins=[]
 for d in selected():m,p=load(d);M[d]=m;pins.append(p)
 write(O/'models.json',M);write(O/'source_pins.json',pins);print(json.dumps({'quests':Q,'resources':len(M),'nodes':sum(len(g['nodes'])for m in M.values()for g in m['graphs'].values())},ensure_ascii=True))
