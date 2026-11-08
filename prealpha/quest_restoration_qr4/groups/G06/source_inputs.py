from pathlib import Path
import sys,json,gzip
W=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
from model import Resource
A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';IDX=read(A/'resource_inventory.json');MI=read(A/'model_inventory.json');C=W/'prealpha/quest_restoration_qr3/candidate_01'
P1='towercontinued\\side_job_pilot_s1\\owner.questphase';P1N='towercontinued\\side_job_pilot_s1\\native_owner.questphase';P1C='towercontinued\\side_job_pilot_s1\\combat.questphase';P13='towercontinued\\sidejobs_s23\\base_b\\mq013.questphase';P2='towercontinued\\sidejobs_s23\\base_a\\mq002_veterans.questphase'
N1='base\\quest\\minor_quests\\mq005\\mq005.questphase';N1C='base\\quest\\minor_quests\\mq005\\phases\\mq005_combat.questphase';N13='base\\quest\\minor_quests\\mq013\\mq013.questphase';N2='base\\quest\\minor_quests\\mq002\\mq002.questphase';PAR='base\\quest\\minor_quests\\minorquests.questphase'
def selected():return sorted({d for d,r in IDX.items() if r.get('graphs') and ('\\mq005\\' in d or '\\mq013\\' in d or '\\mq002\\' in d or d in [P1,P1N,P1C,P13,P2,PAR])})
def load(d):
 r=IDX[d];j=Path(r['json']);raw=C/'archive_source'/Path(d.replace('\\','/')) if d.startswith('towercontinued\\') else j.with_suffix('')
 if not raw.is_file():raw=Path(str(j).replace('\\json\\','\\raw\\')).with_suffix('')
 assert raw.is_file() and sha(raw)==r['sha256'],d
 m=Resource(read(j)).normalize();cached=json.loads(gzip.decompress(Path(MI[d]['normalized_model']).read_bytes()));cached.setdefault('embedded_files',[]);assert m==cached,d
 return m,{'depot':d,'binary':str(raw),'sha256':sha(raw),'json':str(j),'json_sha256':sha(j),'model':MI[d]['normalized_model'],'model_sha256':sha(MI[d]['normalized_model']),'errors':m['errors']}
if __name__=='__main__':
 O=Path(__file__).resolve().parent/'inspection_01';assert not O.exists()
 models={};pins=[]
 for d in selected():m,p=load(d);models[d]=m;pins.append(p)
 write(O/'models.json',models);write(O/'pins.json',pins)
 print({'resources':len(pins),'nodes':sum(len(g['nodes']) for m in models.values() for g in m['graphs'].values())})
