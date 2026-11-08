"""Bounded independent raw export preparation; author verifiers never imported."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;W=H.parents[4];G=W/'prealpha/quest_restoration_qr5/groups/G20'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write
P=read(G/'verification_01/source_pins.json')+read(G/'lifecycle_01/source_pins.json')
tails=['sts_ep1_06_entry.questphase','sts_ep1_03_entry.questphase','sts_ep1_12_entry.questphase','sts_ep1_06_zembinsky.questphase','sts_ep1_03_phase.questphase','sts_ep1_12_phase.questphase','sts_ep1_06_cleanup.questphase','sts_ep1_03_cleanup.questphase','sts_ep1_12_cleanup.questphase','ep1_street_stories.questphase','q302_ronald_tree.questphase','ronald.questphase']
rows=[]
for i,t in enumerate(tails):
 p=next(p for p in P if p.get('depot','').endswith('\\'+t)or p.get('depot','').endswith('/'+t))
 rows.append({'name':'r'+str(i),'depot':p['depot'],'raw':p['raw'],'sha256':p['raw_sha256']})
assert not(H/'inputs.json').exists();write(H/'inputs.json',rows);print('Prepared '+str(len(rows))+' independent binary exports')
