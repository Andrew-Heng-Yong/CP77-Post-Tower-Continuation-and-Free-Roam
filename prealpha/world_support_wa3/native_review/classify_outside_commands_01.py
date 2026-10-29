import json,collections
from pathlib import Path
R=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
rows=read(R/'outside_commands_01.json')
for x in rows:
 n=x['node'];t=n['$type'];sub=n.get('type',{}).get('$type','')
 if t=='questVoicesetManagerNodeDefinition':
  reason='IMPLEMENTED_NATIVE_CURRENT_ACTOR_GREETING' if 'pac_wwd' in x['source'] else 'UNREACHABLE_NATIVE_GREETING_BRANCH: nodes3/5 depend6<-8 but originalgraph no edge enters randomizer8; entry0 runs22->20->9 client lifecycle. Do not invent admission.'
 elif t=='questMovePuppetNodeDefinition':
  reason='OMITTED_CLIENT_LIFECYCLE_MOVE: parent spawns/moves client then deactivates; passive7workspots and generic speech restored under1001; no client population replay.' if 'bad_ina' in x['source'] else 'OMITTED_MONK_COMPANION_MOVE: native three spline followers executeWhileDespawned, repeat on interrupt, NotInterruptable companion teleport; exact current route+actor lifecycle not bound. Do not transform into generic patrol.'
 elif t=='questMiscAICommandNode':reason='OMITTED_DIRECT_ROLE_REASSIGNMENT: compiled function AIClearRoleCommandParams paired with AIAssignRoleCommandParams/AIPatrolRole; native parent actor activation/phase lifecycle not resumed. Exact existing native workspot/route resources preserved where matched; no speculative dispatch or role overwrite.'
 else:
  reason='OMITTED_'+sub+': vehicle ownership/driver/phase lifecycle belongs native parent; exact vehicle Ready and nonreplay boundary not established by current NPC support identity. Do not mount, flush traffic, change door interactions or spawn AVs from NPC admission.'
 x['disposition']=reason
out={'status':'COMPLETE_DISPOSITION_114_DISTRICT_ACTION_NODES','rows':rows,'counts':dict(collections.Counter(x['disposition'].split(':')[0] for x in rows)),'scope':'Direct ancillary commands in16base district communities; CE native action preservation and new fight-family proof are separate.','game_writes':0,'save_writes':0}
(R/'outside_command_dispositions_01.json').write_text(json.dumps(out,indent=2)+'\n',newline='\n');print(out['counts'])
