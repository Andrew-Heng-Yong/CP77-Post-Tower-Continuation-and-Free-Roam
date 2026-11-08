from pathlib import Path
import sys,json,gzip
W=Path(__file__).resolve().parents[4];sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
from model import Resource
A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';IDX=read(A/'resource_inventory.json');MI=read(A/'model_inventory.json');C=W/'prealpha/quest_restoration_qr3/candidate_01'
P7='towercontinued\\sidejobs_s23\\base_a\\mq007_smartgun.questphase';B7='towercontinued\\sidejobs_s23\\base_a_v2\\mq007_resume_boot.questphase';R7='towercontinued\\sidejobs_s23\\base_a_v2\\mq007_resume_owner.questphase';SC3='towercontinued\\skippy_ambient_sc3\\skippy_ambient_owner.questphase';P8='towercontinued\\sidejobs_s2\\mq008_party.questphase';P21='towercontinued\\sidejobs_s23\\base_a\\mq021_guide.questphase'
N7='base\\quest\\minor_quests\\mq007\\mq007.questphase';N8='base\\quest\\minor_quests\\mq008\\mq008.questphase';N21='base\\quest\\minor_quests\\mq021\\mq021.questphase';PAR='base\\quest\\minor_quests\\minorquests.questphase'
def selected():return sorted({d for d,r in IDX.items()if r.get('graphs')and(any(s in d for s in ['\\mq007\\','\\mq008\\','\\mq021\\'])or d in [P7,B7,R7,SC3,P8,P21,PAR])})
def load(d):
 r=IDX[d];j=Path(r['json']);raw=C/'archive_source'/Path(d.replace('\\','/'))if d.startswith('towercontinued\\')else j.with_suffix('')
 if not raw.is_file():raw=Path(str(j).replace('\\json\\','\\raw\\')).with_suffix('')
 assert raw.is_file()and sha(raw)==r['sha256'],d
 m=Resource(read(j)).normalize();cached=json.loads(gzip.decompress(Path(MI[d]['normalized_model']).read_bytes()));cached.setdefault('embedded_files',[]);assert m==cached,d
 return m,{'depot':d,'binary':str(raw),'sha256':sha(raw),'json':str(j),'json_sha256':sha(j),'model':MI[d]['normalized_model'],'model_sha256':sha(MI[d]['normalized_model']),'errors':m['errors']}
if __name__=='__main__':
 O=Path(__file__).resolve().parent/'inspection_01';assert not O.exists();models={};pins=[]
 for d in selected():m,p=load(d);models[d]=m;pins.append(p)
 write(O/'models.json',models);write(O/'pins.json',pins);print({'resources':len(pins),'nodes':sum(len(g['nodes'])for m in models.values()for g in m['graphs'].values())})
