"""QR5 G17 frozen resource inputs. Read-only; no historical builder imports."""
from pathlib import Path
import sys,json,gzip
W=Path(__file__).resolve().parents[4];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
from model import Resource
IDX=read(W/'diagnostics/vanilla_parity_20261029_01/analysis_02/resource_inventory.json');MI=read(W/'diagnostics/vanilla_parity_20261029_01/analysis_02/model_inventory.json');E=read(W/'prealpha/quest_restoration_qr5/source_epoch_00.json');C=Path(E['candidate']);Q=read(W/'prealpha/quest_restoration_qr5/progress.json')['groups']['G17']['ids'];CONTRACT=W/'prealpha/sidejobs_s24/ep1/contract02.json';S24=read(CONTRACT);S23=read(W/'prealpha/sidejobs_s23/ep1/contract.json');OWN=[o for o in S24['owners']if o['id']in Q]
PARENT='ep1\\quest\\minor_quests\\ep1_minor_quests.questphase'
COMMON=[PARENT,'ep1\\quest\\ep1.questphase','base\\quest\\holocalls\\mr_hands\\mr_hands_holocall.questphase','base\\quest\\holocalls\\mr_hands\\mr_hands_holocall.scene','base\\quest\\holocalls\\mr_hands\\mr_hands_cleanup.questphase','towercontinued\\gig_phone_u9\\support_wrapper.questphase','towercontinued\\gig_phone_u9\\fixer_initializer.questphase','towercontinued\\gig_phone_u9\\fixer_parent.questphase','towercontinued\\gig_phone_u9\\fixer_cleanup.questphase','towercontinued\\phone_studios_ph3\\studio_support.questphase']
def selected():return sorted({d for d,r in IDX.items()if r.get('graphs')and any(q in d for q in ['mq305','mq306'])}|set(COMMON))
def load(d):
 r=IDX[d];j=Path(r['json']);raw=C/'archive_source'/Path(d.replace('\\','/'))if d in E['source_resources']else j.with_suffix('')
 if not raw.is_file():raw=Path(str(j).replace('\\json\\','\\raw\\')).with_suffix('')
 assert raw.is_file()and sha(raw)==r['sha256'],d
 if d in E['source_resources']:assert sha(raw)==E['source_resources'][d]
 m=Resource(read(j)).normalize();p={'depot':d,'raw':str(raw),'raw_sha256':sha(raw),'json':str(j),'json_sha256':sha(j),'provider':r['archive'],'errors':m['errors'],'source_epoch':'QR5epoch00 unchanged G17 payload; separate staged monitor repairs unrelated'}
 original=W/'research/sidejobs_s24/ep1/native_01/raw'/Path(d.replace('\\','/'));origjson=W/'research/sidejobs_s24/ep1/native_01/json'/Path(d.replace('\\','/')+'.json')
 if original.is_file()and origjson.is_file():p['original']={'raw':str(original),'raw_sha256':sha(original),'json':str(origjson),'json_sha256':sha(origjson)}
 return m,p
if __name__=='__main__':
 O=H/'inspection_01';assert not O.exists();ms={};pins=[]
 for d in selected():m,p=load(d);ms[d]=m;pins.append(p)
 write(O/'models.json',ms);write(O/'source_pins.json',pins);print(json.dumps({'quests':Q,'resources':len(ms),'nodes':sum(len(g['nodes'])for m in ms.values()for g in m['graphs'].values())},ensure_ascii=True))
