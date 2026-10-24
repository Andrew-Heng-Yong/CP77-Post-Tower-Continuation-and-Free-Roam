from pathlib import Path
import re,sys,json
H=Path(__file__).resolve().parent;W=H.parent.parent;O=H/'candidate_01/diagnosis_01'
s=(W/'prealpha/loading_cover_lc3/candidate_01/compile_01/compiled.script').read_text(encoding='utf-8-sig')
def block(s,pat):
 m=re.search(pat,s);assert m,pat
 i=s.index('{',m.start());n=1;j=i+1
 while n:
  n+=(s[j]=='{')-(s[j]=='}');j+=1
 return s[m.start():j]
for cls in ['DoorControllerPS','Door','ScriptableDeviceAction','DeviceAction','ActionBool','ActionNotifier','DoorProximityDetectorControllerPS','ToggleOpen','QuestForceClose','QuestForceLock','QuestForceUnlock']:
 t=block(s,r'(?m)^public (?:abstract |native |importonly )*class '+cls+r'\b');(O/(cls+'.script')).write_text(t,encoding='utf-8')
for name in sys.argv[1:]:
 if name.startswith('facts'):
  for p in O.glob('AutoSave-*.audit.json'):
   d=json.loads(p.read_text());print(p.name,json.dumps([x for x in d['facts'] if re.search(r'PTFRH1_|PTFRB0WV|PTFRB0H10|wat_lch_gunsmith|wilson_attention|mq011_active|PTFRPA2_Finished',x['name'])],indent=1))
 else:print(block(s,name))
