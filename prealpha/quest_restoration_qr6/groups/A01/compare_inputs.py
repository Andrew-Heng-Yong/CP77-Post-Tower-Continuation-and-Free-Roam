from pathlib import Path
import sys,collections,copy
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));from source_lib import *
def run(O):
 assert not O.exists();S=Store();M=read(H/'inspection_01/models.json');comparisons=[];models={};pairs=[]
 prefix='towercontinued\\sidejobs_s29\\native\\'
 reloc={d[len(prefix):]:d for d in E['source_resources']if d.startswith(prefix)}
 for d in M:
  if not d.startswith(prefix):continue
  orig=d[len(prefix):];a=S.load(orig);b=S.load(d)
  dif=compare_graph(a,b,reloc)
  comparisons.append(dict(vanilla=orig,current=d,diffs=dif,vanilla_errors=a['errors'],current_errors=b['errors']))
  pairs.append((orig,d))
 for d in [r'base\quest\minor_quests\minorquests.questphase',r'base\quest\cyberpunk2077.questphase',r'ep1\quest\main_quests\q307\q307.quest',r'towercontinued\b0_story_services\pepe.questphase',r'towercontinued\gig_phone_u9\fixer_cleanup.questphase',r'towercontinued\phone_studios_ph3\studio_support.questphase']:
  try:S.load(d)
  except KeyError:pass
 for c in ['cynthia','pepe','blue_moon','nancy']:
  for d in [f'base\\quest\\holocalls\\{c}\\{c}_holocall.questphase',f'base\\quest\\holocalls\\{c}\\{c}_holocall.scene',f'base\\quest\\holocalls\\{c}\\{c}_cleanup.questphase',f'towercontinued\\sidejobs_s29\\phone\\{c}.questphase']:S.load(d)
 write(O/'comparisons.json',comparisons);write(O/'models.json',S.models);write(O/'source_pins.json',S.pins);write(O/'missing.json',S.missing)
 for r in comparisons:
  print(r['current'],collections.Counter(x['kind']for x in r['diffs']));print(r['diffs'][:8])
 print('MISSING',S.missing)
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);run(Path(ap.parse_args().output))
