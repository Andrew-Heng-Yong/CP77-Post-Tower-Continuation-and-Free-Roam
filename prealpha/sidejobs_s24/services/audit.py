"""Read-only native service-sidejob audit; no game/save/runtime writes."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'prealpha/sidejobs_s22/delamain_v2')]
from test import graphs,read,sha

SOURCES={
 'wilson':'research/b0_wilson_vendor/vanilla/json/base/quest/main_quests/prologue/q001/phases/q001_wilson.questphase.json',
 'wakako':'research/sidejobs_s22/the_gig/native_01/json/base/quest/main_quests/prologue/q001/phases/q101_wakako_reward.questphase.json',
 'heroes':'research/activity_state_r3/native_sources/json/base/quest/side_quests/sq018/sq018.questphase.json',
 'heroes_intro':'research/activity_state_r3/native_sources/json/base/quest/side_quests/sq018/phases/sq018_00_holocall.questphase.json',
 'heroes_persistent':'research/activity_state_r3/native_sources/json/base/quest/side_quests/sq018/phases/sq018_persistent_content.questphase.json',
 'viktor_current':'research/b0_story_eight/validation/viktor.questphase.json',
}
if __name__=='__main__':
 key=sys.argv[1]
 if key=='contacts':
  for p in (ROOT/'research/sidejobs_s24/services/native_01/json/base/quest/main_quests/prologue/q001').rglob('*.json'):
   for gp,g in graphs(p).items():
    for n in g['nodes']:
     if isinstance(n.get('type'),dict) and n['type'].get('$type')=='questAddRemoveContact_NodeType':print(p.relative_to(ROOT),gp,json.dumps(n))
 elif key=='capture':
  cap=read(ROOT/'research/sidejobs_s23/live_20261016_01/capture.json')
  for j in cap['second']['jobs']:
   if j['id'] in ('sq_q001_wilson','sq_q001_wakako','mq045_victor_debt','sq018_jackie'):
    print(json.dumps(j,indent=2))
 else:
  gs=graphs(ROOT/SOURCES[key])
  print(json.dumps(gs if len(sys.argv)<3 else gs[sys.argv[2]],indent=2))
