from pathlib import Path
import sys
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'A01'));from source_lib import *
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);O=Path(ap.parse_args().output);assert not O.exists();S=Store();allids=['mq016','mq006','mq029'];ds=set(read(H/'inspection_01/models.json'))
 ds|={d for d in IDX if any(q in d for q in allids)and'\\versions\\'not in d and d.endswith(('.scene','.questphase'))}
 ds|={r'base\quest\minor_quests\minorquests.questphase',r'towercontinued\b0_story_eight\nix.questphase',r'towercontinued\b0_story_eight\nix.scene',r'towercontinued\phone_support_ph1\nix.questphase',r'towercontinued\gig_phone_u9\fixer_cleanup.questphase',r'towercontinued\phone_studios_ph3\studio_support.questphase'}
 ds|={d for d in IDX if d.startswith(r'towercontinued\world_interactions\coaster')and d.endswith(('.scene','.questphase'))}
 ds|={f'base\\quest\\holocalls\\nix\\nix_{k}'for k in ['holocall.questphase','holocall.scene','cleanup.questphase']}
 for d in sorted(ds):S.load(d)
 write(O/'models.json',S.models);write(O/'source_pins.json',S.pins);write(O/'missing.json',S.missing);print(dict(resources=len(S.models),missing=S.missing))
