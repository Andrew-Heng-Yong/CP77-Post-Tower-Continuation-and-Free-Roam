"""Join every q307 world-variant operation to compiled world descriptors.

Read-only game/resource analysis; generated evidence is workspace-only. Keys use
both variant name and owner reference so generic names are not conflated.
"""
import json
import sys
from collections import Counter,defaultdict
from pathlib import Path
from analyze_q307 import walk

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/phase2b_p4'
SOURCE=ROOT/'research/q307_extracted/json/ep1/quest/main_quests/q307'
BLOCKROOT=OUT/'staging_scan/ep1_1_nightcity/json/base/worlds/03_night_city/_compiled/default'

def val(v):return v.get('$value') if isinstance(v,dict) else v
def norm(v):return str(v).replace('\\','/').lower().strip()
def refs_match(a,b):
    a,b=norm(a),norm(b)
    if a==b:return True
    if a.startswith('#'):
        return any(a in part.split(';') for part in b.split('/'))
    # Exact full reference can be rendered with aliases in exports; preserve such
    # name-only matches as candidates, never silently count them as proved joins.
    return False

def main():
    ops=[]
    for p in sorted(SOURCE.rglob('*.json')):
        if '/test/' in p.as_posix():continue
        for obj,loc,parents in walk(json.loads(p.read_text(encoding='utf-8-sig'))):
            if obj.get('$type')!='questTogglePrefabVariant_NodeTypeParams':continue
            nodes=[{'type':x['$type'],'id':x.get('id')} for x in parents if '$type'in x and 'Node'in x['$type'] and 'id'in x]
            for state in obj.get('variantStates',[]):
                ops.append({'resource':str(p.relative_to(SOURCE)),'json_path':'.'.join(map(str,loc)),'nodes':nodes,'owner':val(obj.get('prefabNodeRef')),'name':val(state.get('name')),'show':state.get('show')})
    bykey=defaultdict(list)
    for op in ops:bykey[(op['owner'],op['name'])].append(op)
    block_variants=[]
    for p in (BLOCKROOT/'blocks/all.streamingblock.json',BLOCKROOT/'ep1/blocks/all.streamingblock.json'):
        doc=json.loads(p.read_text(encoding='utf-8-sig'))['Data']['RootChunk']
        for di,d in enumerate(doc['descriptors']):
            for v in d.get('variants',[]):
                block_variants.append({'block':str(p.relative_to(ROOT)),'descriptor_index':di,'sector':val(d['data']['DepotPath']),'category':d.get('category'),'level':d.get('level'),'variant':{k:val(x) for k,x in v.items() if k!='$type'}})
    groups=[]
    for (owner,name),items in bykey.items():
        named=[v for v in block_variants if v['variant']['name']==name]
        exact=[v for v in named if refs_match(owner,v['variant']['nodeRef'])]
        candidates=[v for v in named if v not in exact]
        sectors=sorted(set(v['sector'] for v in exact))
        cleanup=[i for i in items if i['resource']=='phases\\q307_cleanup.questphase.json']
        groups.append({'owner':owner,'name':name,'operations':items,'cleanup_requests':[{'show':i['show'],'nodes':i['nodes'],'json_path':i['json_path']} for i in cleanup],'exact_owner_matches':exact,'name_only_candidates':candidates,'sector_count':len(sectors),'sectors':sectors,'levels':sorted(set(v['level'] for v in exact))})
    summary={'operation_count':len(ops),'owner_variant_pairs':len(groups),'pair_exact_matched_count':sum(bool(g['exact_owner_matches']) for g in groups),'pair_name_candidate_only_count':sum(not g['exact_owner_matches'] and bool(g['name_only_candidates']) for g in groups),'unique_matched_sectors':len(set(s for g in groups for s in g['sectors'])),'warning':'Counts include setup/cleanup alternatives, pre-2079 pickup, hospital and presentation variants, and LOD sectors; not counts of independent 2079 features.'}
    compiled_siblings=[];compiled_additional=[]
    requested_names={g['name']for g in groups}
    linked_owners={v['variant']['nodeRef']for g in groups for v in g['exact_owner_matches']}
    for row in block_variants:
        name=row['variant']['name'];owner=row['variant']['nodeRef']
        if name not in requested_names and owner in linked_owners:compiled_siblings.append(row)
        if name not in requested_names and ('q307'in str(name).lower()or'2079'in str(name)):compiled_additional.append(row)
    summary['additional_q307_or_2079_compiled_owner_name_pairs']=len({(v['variant']['nodeRef'],v['variant']['name'])for v in compiled_additional})
    extra_consumers=[]
    for p in sorted((OUT/'physical_extra_quest/json').rglob('*.json')):
        for obj,loc,parents in walk(json.loads(p.read_text(encoding='utf-8-sig'))):
            if obj.get('$type')!='questTogglePrefabVariant_NodeTypeParams':continue
            if any('q307_city_scenes'in str(val(s.get('name')))for s in obj.get('variantStates',[])):
                extra_consumers.append({'resource':str(p.relative_to(OUT/'physical_extra_quest/json')),'json_path':'.'.join(map(str,loc)),'nodes':[{'type':x['$type'],'id':x.get('id')}for x in parents if'$type'in x and'Node'in x['$type']and'id'in x],'owner':val(obj.get('prefabNodeRef')),'states':[{'name':val(s.get('name')),'show':s.get('show')}for s in obj.get('variantStates',[])]})
    (OUT/'physical_variant_census.json').write_text(json.dumps({'summary':summary,'variants':groups,'compiled_sibling_variants_without_direct_operation':compiled_siblings,'additional_q307_or_2079_compiled_variants_without_direct_operation':compiled_additional,'additional_variant_consumers':extra_consumers},indent=2),encoding='utf-8')
    print(json.dumps(summary))
    if'--summary-only'in sys.argv:return
    for g in groups:
        print(json.dumps({'owner':g['owner'],'name':g['name'],'ops':len(g['operations']),'cleanup':[r['show'] for r in g['cleanup_requests']],'sector_count':g['sector_count'],'candidate_only':len(g['name_only_candidates']) if not g['exact_owner_matches'] else 0,'resources':sorted(set(i['resource'] for i in g['operations']))},separators=(',',':')))
if __name__=='__main__':main()
