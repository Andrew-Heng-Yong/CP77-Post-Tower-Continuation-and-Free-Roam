"""Targeted independent captured-model producer/parent census for three C03 jobs."""
from pathlib import Path
import sys,json,gzip
W=Path(__file__).resolve().parents[4];sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
def run(O):
 assert not O.exists();idx=read(W/'diagnostics/vanilla_parity_20261029_01/analysis_02/model_inventory.json');facts=['wst_ep1_09_active','wst_ep1_02_active','q305_haunted_breadcrumb_start','Q305_haunted_component_talk_ready','q305_haunted_component_ready','Q305_haunted_component_craft_ready'];targets=['ep1\\openworld\\world_stories\\ep1_world_stories.questphase','ep1\\quest\\main_quests\\q305\\phases\\q305_12_haunted_weapon.questphase','ep1\\openworld\\world_stories\\wst_ep1_09\\wst_ep1_09.questphase','ep1\\openworld\\world_stories\\wst_ep1_02\\wst_ep1_02.questphase'];rows=[];pins=[]
 for d,r in idx.items():
  p=Path(r['normalized_model']);m=json.loads(gzip.decompress(p.read_bytes()));pins.append({'depot':d,'path':str(p),'sha256':sha(p)})
  for gp,g in m.get('graphs',{}).items():
   for ni,n in g['nodes'].items():
    fs=[x for x in n['writes'] if x.get('factName') in facts];refs=[x for x in n['refs'] if x in targets]
    if fs or refs:rows.append({'depot':d,'graph':gp,'node':ni,'payload':n['payload'],'writes':fs,'refs':refs,'incoming':[e for e in g['edges'] if e[2]==ni],'outgoing':[e for e in g['edges'] if e[0]==ni]})
 write(O/'census_pins.json',pins);write(O/'crossowners.json',rows);write(O/'summary.json',{'models':len(pins),'matches':len(rows),'facts':facts,'targets':targets,'limit':'Captured5136 model census is bounded evidence, not every engine registration path. Actual effective QR5 bytes must be pinned before applicability.'});print({'models':len(pins),'matches':len(rows)})
if __name__=='__main__':run(Path(sys.argv[1]))
