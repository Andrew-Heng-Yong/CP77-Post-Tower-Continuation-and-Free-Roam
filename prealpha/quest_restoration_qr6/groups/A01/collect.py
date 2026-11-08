from pathlib import Path
import sys,re
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
from source_lib import *
IDS=['mq040_biosculpt','mq028_stalker','mq018_writer']
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);O=Path(ap.parse_args().output);assert not O.exists();S=Store();selection={};summ=[]
 for q in IDS:
  qr=QUEUE[q];prefix=q[:5];private=qr['restored_candidates'];deps=set(private)
  deps|={d.split('\\native\\',1)[1]for d in private if '\\native\\'in d}
  deps|={d for d in qr['vanilla_candidates']if '\\versions\\'not in d}
  deps|={d for d in IDX if not d.startswith('towercontinued\\')and prefix in d and d.endswith('.questphase')}
  selection[q]=sorted(deps)
  for d in sorted(deps):
   try:m=S.load(d)
   except KeyError:continue
   nr=rows(m);s={'quest':q,'depot':d,'type':m['type'],'root_prefabs':m['root_prefabs'],'errors':m['errors'],'graphs':{gp:{'nodes':len(g['nodes']),'entries':g['entries'],'unreachable':g['unreachable'],'edges':g['edges']if len(g['nodes'])<70 else 'see_models'}for gp,g in m['graphs'].items()}}
   s['nodes']=[{k:r[k]for k in ['graph','node','type','reads','writes','refs','prefabs','journal_paths','incoming','outgoing','payload']}for r in nr if d.endswith('.questphase') or r['writes']or r['reward']or r['sms']or any('call' in str(x).lower()for x in r['reads'])]
   summ.append(s)
 write(O/'models.json',S.models);write(O/'source_pins.json',S.pins);write(O/'missing.json',S.missing);write(O/'selection.json',selection);write(O/'summary.json',summ)
 print({'models':len(S.models),'missing':S.missing,'nodes':sum(len(g['nodes'])for m in S.models.values()for g in m['graphs'].values())})
