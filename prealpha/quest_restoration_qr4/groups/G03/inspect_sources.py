from lib import *
O=Path(__file__).resolve().parent
assert not (O/'inspection.json').exists(),'Preserve initial inspection; use the fresh-output verifier instead'
S=Store();prefixes=['\\mq010\\','\\mq015\\','\\mq019\\','\\mq024\\','\\holocalls\\sandra\\','\\holocalls\\nix\\','\\holocalls\\lizzy\\']
extra=[r'base\quest\minor_quests\minorquests.questphase',r'base\quest\holocalls\holocall_initializers.questphase',r'towercontinued\gig_phone_u9\fixer_cleanup.questphase',r'towercontinued\phone_studios_ph3\studio_support.questphase',r'towercontinued\sidejobs_s23\phone\sandra.questphase',r'towercontinued\phone_support_ph1\nix.questphase',r'towercontinued\sidejobs_s24\phone\lizzy.questphase',r'towercontinued\b0_story_eight\nix.questphase']
private=[r'towercontinued\sidejobs_s23\base_a\mq024_sandra.questphase']+['towercontinued\\sidejobs_s24\\base\\'+q+'.questphase' for q in ['mq010','mq015','mq019']]
DS=sorted({d for d in S.MI if any(t in d for t in prefixes)}|set(extra+private));data={}
for d in DS:
 m=S.load(d);graphs={}
 for gp,g in m['graphs'].items():
  rows={}
  for i,n in g['nodes'].items():
   rows[i]={'type':n['type'],'reads':n['reads'],'writes':n['writes'],'refs':n['refs'],'journal':n['journal_paths'],'prefabs':n['prefabs'],'node_refs':n['node_refs'],'tweak_ids':[val(x) for x in walk(n['payload']) if x.get('$type')=='TweakDBID'],'in':[e for e in g['edges'] if e[2]==i],'out':[e for e in g['edges'] if e[0]==i]}
  graphs[gp]={'entries':g['entries'],'nodes':rows,'edges':g['edges']}
 data[d]={'root_prefabs':m['root_prefabs'],'graphs':graphs,'refs':m['refs']}
save(O/'inspection.json',data);save(O/'source_pins_initial.json',S.pins)
print(json.dumps({'resources':len(data),'graphs':sum(len(m['graphs']) for m in data.values()),'nodes':sum(len(g['nodes']) for m in data.values() for g in m['graphs'].values()),'errors':[p for p in S.pins if p['errors']]}))
