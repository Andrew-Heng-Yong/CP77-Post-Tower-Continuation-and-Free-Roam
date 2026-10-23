"""Bind encounter08 current raw donors to immutable exact official extraction evidence."""
import json,sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import read,sha
HERE=ROOT/'research/sidejobs_s28/encounters'
def main():
 out=HERE/'current_donors_02.json';assert not out.exists()
 comp='prealpha/sidejobs_s28/encounters/build/encounters_08/component.json';audit='research/sidejobs_s28/encounters/current_donors_01/report.json';inventory='research/sidejobs_s28/vehicles/world_03/inventory.json';c=read(ROOT/comp);a=read(ROOT/audit);inv=read(ROOT/inventory);pins={p:sha(ROOT/p) for p in [comp,audit,inventory,str(Path(__file__).relative_to(ROOT)).replace('\\','/')]};hist=set(c['historical_comparison_sources']);wanted={};documentary=[];metadata=[]
 for p,h in c['source_pins'].items():
  assert sha(ROOT/p)==h
  if p in hist:documentary.append({'raw':p,'sha256':h,'purpose':'Historical patch delta comparison only; not current resource donor'});continue
  if p.endswith('.journal') and '/raw/' in p:metadata.append({'raw':p,'sha256':h,'purpose':'Path/class catalog only; current journal variants proved separately'});continue
  m=re.search(r'/raw/((?:base|ep1)/.+\.(?:quest|questphase|scene|workspot))$',p)
  if m:wanted.setdefault(m[1].replace('/','\\'),[]).append({'raw':p,'sha256':h,'archive':None})
 world=next(x for x in inv['rows'] if x['raw']=='research/sidejobs_s28/vehicles/world_03/raw/ep1_1_nightcity_always_loaded_1.streamingsector');assert c['source_pins'][world['raw']]==world['raw_sha256'];wanted[world['depot']]=[{'raw':world['raw'],'sha256':world['raw_sha256'],'archive':world['archive']}]
 rows=[]
 for dep,inputs in wanted.items():
  for v in [r for r in a['rows'] if r['depot']==dep]:
   selected=[p for p in inputs if p['archive'] is None or p['archive'].lower()==v['archive'].lower()]
   if not selected:continue
   assert all(p['sha256']==v['current_sha256'] for p in selected),(dep,selected,v)
   for p in selected:
    pins[p['raw']]=sha(ROOT/p['raw']);jp=p['raw'].replace('/raw/','/json/')+'.json';pins[jp]=sha(ROOT/jp)
   rows.append({'depot':dep,'archive':v['archive'],'sha256':v['current_sha256'],'raw':selected[0]['raw'],'sources':selected,'current_byte_exact':True,'proof_audit':audit})
 assert {r['depot'] for r in rows}==set(wanted);assert len(hist)==3 and len(documentary)==3
 result={'status':'PASS_CURRENT_OFFICIAL_ENCOUNTER_DONORS','component':comp,'component_sha256':sha(ROOT/comp),'rows':rows,'selected_depots':len(wanted),'official_comparisons':len(rows),'source_pins':pins,'archives':a['archives'],'historical_comparison_sources':documentary,'metadata_only_sources':metadata,'world_inventory':inventory,'scope':'Every current encounter phase/scene/workspot and prerequisite proof raw source is bound to current exact official archive content. World identity proof uses the exact archive variant recorded in its inventory. Historical comparison and journal metadata inputs remain hash-pinned but are never current gameplay donors. No override or engine-liveness claim.'}
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':result['status'],'depots':len(wanted),'comparisons':len(rows),'sha256':sha(out)}))
if __name__=='__main__':main()
