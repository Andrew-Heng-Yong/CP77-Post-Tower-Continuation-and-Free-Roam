import sys,json
from pathlib import Path
W=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(W/'tools'))
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten
r=SafeResource(json.loads((W/'research/q307_extracted/json/ep1/quest/main_quests/q307/q307.quest.json').read_bytes()))
for g in flatten(r,r.obj['Data']['RootChunk']):
 if not g['path'].startswith('root/6'):continue
 print(json.dumps(g,indent=2))
