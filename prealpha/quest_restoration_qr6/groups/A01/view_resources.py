from pathlib import Path
import sys,json,re
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));from source_lib import *
import argparse
ap=argparse.ArgumentParser();ap.add_argument('--file',default=str(H/'inspection_01/models.json'));ap.add_argument('--depot',default='');ap.add_argument('--graph',default='');ap.add_argument('--mode',default='compact');ap.add_argument('--node');args=ap.parse_args();M=read(args.file)
for d,m in M.items():
 if args.depot not in d:continue
 print('\nRESOURCE',d,'PIP',m['root_prefabs'],'ERRORS',m['errors'])
 for gp,g in m['graphs'].items():
  if args.graph and gp!=args.graph:continue
  print('GRAPH',gp,'ENTRIES',g['entries'],'unreachable',g['unreachable'])
  for i,n in g['nodes'].items():
   if args.node and i not in args.node.split(','):continue
   if args.mode=='payload':print(i,json.dumps(n['payload'],ensure_ascii=False));continue
   if args.mode=='phones'and not(n['sms']or any(re.search('phone|call|holo|audio|sms',str(x),re.I)for x in n['writes'])or any(re.search('Phone|Call|Message',x.get('$type',''))for x in walk(n['payload']))):continue
   parts=[i,n['type'].replace('quest','').replace('NodeDefinition','')]
   if n['reads']:parts.append('R='+str([(r.get('factName',r.get('path',{}).get('realPath')),r.get('comparisonType'),r.get('value',r.get('state')))for r in n['reads']]))
   if n['writes']:parts.append('W='+str([(r['factName'],r['value'])for r in n['writes']]))
   if n['refs']:parts.append('REF='+str(n['refs']))
   if n['journal_paths']:parts.append('J='+str(n['journal_paths']))
   if n['prefabs']:parts.append('PIP='+str(n['prefabs']))
   parts.append('E='+str([e for e in g['edges']if e[0]==i]))
   if any(x.get('$type')in['questTimeCondition','questTriggerCondition','questRewardManagerNodeDefinition','questConditionNodeDefinition']for x in walk(n['payload'])):parts.append('PAYLOAD='+json.dumps(n['payload'],ensure_ascii=False)[:2000])
   print(' '.join(parts))
