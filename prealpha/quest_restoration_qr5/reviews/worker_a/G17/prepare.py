"""Prepare independent G17 binary exports; no author verifier imports."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;W=H.parents[4];G=W/'prealpha/quest_restoration_qr5/groups/G17'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write
pins=read(G/'verification_01/source_pins.json')
tails=['ep1_minor_quests.questphase','mq305.questphase','mq305_outcome.questphase','mq305_04_bunker.scene','mq306.questphase','mq306_01_intro.questphase','mq306_04a_aaron_meeting.questphase','mq305_fresh_boot.questphase','mq306_fresh_boot.questphase','mq306_boot.questphase','mq306_aaron.questphase','mr_hands_holocall.scene']
rows=[]
for i,t in enumerate(tails):
 p=next(p for p in pins if p.get('depot','').endswith('\\'+t))
 rows.append({'name':'r'+str(i),'depot':p['depot'],'raw':p['raw'],'sha256':p['raw_sha256']})
assert not (H/'inputs.json').exists();write(H/'inputs.json',rows)
print(json.dumps(rows,indent=2))
