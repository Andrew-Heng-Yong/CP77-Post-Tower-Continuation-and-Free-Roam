"""Write bounded node/edge inspection text from exact normalized evidence."""
import json,sys
from pathlib import Path
import inputs as I
def run(group,folder):
 ms=I.read(folder/'models.json');lines=[]
 for q in I.ASSIGN[group]:
  lines.append('\n######## '+q)
  rr=[r for r in I.U['recipes'] if r.get('id')==q];lines.append('RECIPES '+json.dumps(rr,ensure_ascii=False))
  for d,m in ms.items():
   if q not in d or d.startswith('recipe:'):continue
   lines.append('\nRESOURCE '+d+' ROOTPREFABS '+json.dumps(m.get('root_prefabs'))+' metadata '+json.dumps(m.get('metadata',{}))[:800])
   for gp,g in m['graphs'].items():
    if gp=='scene' and 'holocall' not in d:continue
    lines.append(' GRAPH '+gp+' entries '+json.dumps(g.get('entries')))
    for ni,n in g['nodes'].items():
     typ=n['type'];interesting=gp=='root' or any(t in typ for t in ['Journal','Reward','Condition','Facts','Phone','Vehicle','Trigger','Logical','Phase','Cut','Checkpoint']) or n['writes']
     if not interesting:continue
     outgoing=[e for e in g['edges'] if e[0]==ni];incoming=[e for e in g['edges'] if e[2]==ni]
     p=n['payload'];short={k:v for k,v in p.items() if k not in ['$type','sockets','graph','id']}
     lines.append(ni+' '+typ+' READ '+json.dumps(n['reads'],ensure_ascii=False)+' WRITE '+json.dumps(n['writes'],ensure_ascii=False)+' J '+json.dumps(n['journal_paths'])+' REF '+json.dumps(n['refs'])+' PIP '+json.dumps(n['prefabs'])+' EDGES '+json.dumps(outgoing)+' IN '+json.dumps(incoming)+' PAYLOAD '+json.dumps(short,ensure_ascii=False)[:1700])
  lines.append('END '+q)
 p=folder/'inspection.txt';p.write_text('\n'.join(lines),encoding='utf8');print(p)
if __name__=='__main__':run(sys.argv[1],Path(sys.argv[2]))
