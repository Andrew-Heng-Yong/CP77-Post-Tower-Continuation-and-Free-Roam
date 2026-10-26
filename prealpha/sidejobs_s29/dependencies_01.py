import sys,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import read,value
from audit_activity_batches_b1 import references
rows=read(ROOT/'research/sidejobs_s29/native_01/inventory.json')['rows'];idx={r['depot']:r for r in rows}
wanted=set([r'base\quest\minor_quests\minorquests.questphase',r'base\quest\side_quests\sidequests.questphase',r'base\quest\holocalls\holocall_initializers.questphase',r'base\quest\holocalls\holocall_cleanup.questphase',r'ep1\openworld\world_stories\ep1_world_stories.questphase',r'base\journal\cooked_journal.journal',r'ep1\journal\cooked_journal.journal'])
for dep,row in idx.items():
 if dep in [r'base\quest\default_dialogs.questphase',r'base\quest\main_quests\prologue\q003\q003.questphase',r'ep1\quest\main_quests\q305\q305.questphase',r'ep1\quest\ep1.questphase',r'ep1\quest\ep1.quest']:continue
 if any(x in dep for x in ['\\test\\','\\temp\\','\\versions\\','chickentest']):continue
 root=read(ROOT/row['json'])['Data']['RootChunk']
 for field in ['phaseResource','sceneFile']:
  wanted.update(d for d in references(root,field) if d not in idx)
out=ROOT/'research/sidejobs_s29/dependencies_01.json';assert not out.exists();out.write_text(json.dumps(sorted(wanted),indent=2)+'\n',encoding='utf-8');print(len(wanted),'dependencies')
