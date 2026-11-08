from pathlib import Path
import sys
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'A01'));from source_lib import *
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);O=Path(ap.parse_args().output);assert not O.exists();S=Store();ds=set(read(H/'inspection_01/models.json'));queue=[d for d in ds if d.startswith('towercontinued')]
 ds|={r'base\quest\minor_quests\minorquests.questphase',r'towercontinued\sidejobs_s29\phone\kirk.questphase',r'towercontinued\gig_phone_u9\fixer_cleanup.questphase',r'towercontinued\phone_studios_ph3\studio_support.questphase'}
 ds|={f'base\\quest\\holocalls\\{c}\\{c}_{k}'for c in ['kirk','meredith']for k in ['holocall.questphase','holocall.scene','cleanup.questphase']}
 for d in sorted(ds):S.load(d)
 seen=set()
 while queue:
  d=queue.pop()
  if d in seen:continue
  seen.add(d);m=S.load(d)
  for r in m['refs']:
   if not r.endswith(('.scene','.questphase'))or not any(t in r for t in ['\\mq017\\','\\mq036\\','\\q003\\']):continue
   if r not in S.models:
    try:S.load(r)
    except KeyError:continue
   queue.append(r)
 write(O/'models.json',S.models);write(O/'source_pins.json',S.pins);write(O/'missing.json',S.missing);print(dict(resources=len(S.models),missing=S.missing))
