import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
cs={r['id']:r for r in read(R/'ep1_prefab_candidates_02.json')};ds=read(R/'ep1_prefab_decoded_01/report_01.json')['rows'];reg=read(R/'ep1_registry_03/report_01.json');found={x['hash']:x for a in reg['rows'] for x in a['found']};ident={x['id']:x for x in reg['identities']};inv=read(R/'ep1_family_inventory_01.json');checks=[];cohort=[];rejected=[]
def ck(n,b):checks.append({'name':n,'pass':bool(b)});assert b,n
hashnames={1103:'356664e005c6bb0d',1107:'0fcc0d951120e13b',1108:'1aa164f3a67b057d',1111:'746e38ed6d41094a'}
for i in hashnames:
 src=cs[{1103:1109,1108:1112}.get(i,i)];d=next(x for x in ds if x['resource'].endswith('quest_'+hashnames[i]+'.streamingsector') and '\\ep1\\' in x['resource']);j=read(d['json']);spots={p['quest_ref'] for p in j['placements'] if p['type']=='worldAISpotNode'};marks={m['$value'] for n in j['nodes'] for m in n['definition'].get('markings',[])};communities=[]
 for c in ident[i]['candidates']:
  if c['hash'] not in found:continue
  f=found[c['hash']];entries=[]
  for ee in read(f['json'])['template']['Data']['entries']:
   e=ee['Data'];refs={n['$value'] for ph in e['phases'] for t in ph['Data']['timePeriods'] for n in t['spotNodeRefs']};mm={m['$value'] for ph in e['phases'] for t in ph['Data']['timePeriods'] for m in t['markings']};bb=[]
   for ref in sorted(refs):
    suffix=ref.replace('~/../','');hits=[s for s in spots if s==ref or s.endswith('/'+suffix)];bb.append({'native_ref':ref,'matches':hits})
   ent={'entry':e['entryName']['$value'],'spot_bindings':bb,'markings':sorted(mm),'unmapped_markings':sorted(mm-marks),'eligible':any(b['matches'] for b in bb) or bool(mm&marks)};entries.append(ent)
  if not any(e['eligible'] for e in entries):rejected.append({'id':i,'ref':c['ref'],'hash':c['hash'],'reason':'No exact support spot or marking in selected prefab','entries':entries});continue
  missing=[b['native_ref'] for e in entries for b in e['spot_bindings'] if not b['matches']]
  ck(str(i)+'/'+c['hash']+' exact bindings or two known native defects',not missing or (i==1108 and set(missing)=={'#q303_ws_phase_C_scrapper_03_02','#q303_ws_phase_C_scrapper_03_03'}))
  ck(str(i)+'/'+c['hash']+' unambiguous matches',all(len(b['matches'])<=1 for e in entries for b in e['spot_bindings']))
  communities.append({'ref':c['ref'],'hash':c['hash'],'registry':f['json'],'registry_sha256':sha(f['json']),'entries':entries})
 ck(str(i)+' expected community count',len(communities)=={1103:32,1107:1,1108:1,1111:20}[i])
 facts=([{'fact':'ep1_side_content','comparison':'Equal','value':0}] if i==1107 else [{'fact':'q303_1_done','comparison':'Greater','value':0},{'fact':'q303_1_active','comparison':'Equal','value':0}] if i==1108 else [])
 proof=R/'ep1_support_assessment_01.json';spec=R/f'ep1_{i}_filter_spec_{"01" if i==1103 else "02"}.json'
 cohort.append({'id':i,'prefab':cs[i]['resolved_candidates'][0],'community_refs':[x['ref'] for x in communities],'spawner_hashes':[x['hash'] for x in communities],'native_binary':src['native_binary'],'native_binary_sha256':src['native_binary_sha256'],'node_path':src['node_path'],'resource':d['resource'],'support_sector_resource':d['resource'],'support_sector_raw':d['winner']['raw'],'support_sector_sha256':d['winner']['sha256'],'support_sector_json':d['json'],'proof':str(proof),'prefix':f'PTFRWA3_{i}_','native_admission_facts':facts,'communities':communities,'requires_private_filtered_sector':True,'filter_spec':str(spec),'extra_dependency_proof':str(R/'ep1_ambient_scene_assessment_01.json') if i==1108 else str(R/'ep1_passive_filter_assessment_01.json')})
# Pin exact original parent edges and relevant native condition payloads.
life=[]
for suffix,paths in [('container_zone_combat.questphase',['root','root/35']),('monument_av_combat.questphase',['root','root/3']),('high_peak_combat.questphase',['root','root/5','root/5/249'])]:
 r=next(x for x in inv if x['resource'].endswith(suffix))
 for p in r['phases']:
  if p['path'] in paths:life.append({'source':r['source'],'binary_sha256':r['binary_sha256'],'path':p['path'],'edges':p['edges'],'prefabs':p['prefabs'],'direct_nodes':[{k:v for k,v in n.items() if k!='phaseGraph'} for n in (p['payload'].get('phaseGraph') or {}).get('nodes',[])]})
report={'status':'PASS','checks':checks,'cohort_ids':list(hashnames),'communities':sum(len(c['communities']) for c in cohort),'lifecycle':life,'excluded_communities':rejected,'native_alias_defects':{'1108':['#q303_ws_phase_C_scrapper_03_02','#q303_ws_phase_C_scrapper_03_03'],'disposition':'Keep native sector and registry byte payloads; affected entry admitted only because it has another exactly bound native spot. Do not rewrite or fabricate aliases.'},'lifecycle_dispositions':{'1103':'Choose original Monument root/3 persistent prefab; native root input enters it directly. Exact existing active entries only, including red-alert variants; no native population or security writes.','1107':'Original root/35 starts directly; ep1_side_content>0 cuts and deactivates lower_after actors. Mirror ep1_side_content==0 and exact lower_after actor binding. Do not start story support or Hasan owner.','1108':'Choose alternate pure support owner high_peak root/5/249 behind q303_1_done>0 and q303_1_active==0. Omit randomizer/respawn and story actor activation.','1111':'Native high_peak root input3 enters root/5 directly. ep1_side_content applies sibling10, not prefab owner5. Exact already active native communities only.'},'limits':['Static/native support validation, not live-game proof.','No community activation, respawn, encounter reset, loot, stage scene, security commands or reward replay.','1107 cannot be admitted after ep1_side_content is enabled; this preserves vanilla availability rather than reintroducing pre-story staging.']}
(R/'ep1_support_assessment_01.json').write_text(json.dumps(report,indent=2)+'\n',newline='\n');(R/'ep1_cohort_01.json').write_text(json.dumps(cohort,indent=2)+'\n',newline='\n');print(json.dumps({'checks':len(checks),'groups':len(cohort),'communities':report['communities'],'excluded':len(rejected),'native_sources':[(c['id'],c['node_path']) for c in cohort]}))
