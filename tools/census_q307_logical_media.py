"""Summarize existing q307 indexes and EP1 journal export for the 2079 census."""
from __future__ import annotations
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/phase2b_p4/logical_media_data'
INDEX = ROOT / 'research/q307_analysis'

def journal_entries(wrapper, path=''):
    if not isinstance(wrapper, dict):
        return
    obj = wrapper.get('Data', wrapper)
    if not isinstance(obj, dict):
        return
    ident = obj.get('id', '')
    here = '/'.join(filter(None, (path, ident)))
    yield here, obj
    for child in obj.get('entries', []):
        yield from journal_entries(child, here)

def flatten(value, path=''):
    if isinstance(value, dict):
        if '$value' in value:
            yield path, value['$value']
        else:
            for k,v in value.items():
                if k not in ('entries', 'sockets', 'connections', 'HandleId'):
                    yield from flatten(v, f'{path}.{k}' if path else k)
    elif isinstance(value, list):
        for i,v in enumerate(value):
            yield from flatten(v, f'{path}.{i}')
    elif isinstance(value, (str,int,float,bool)):
        yield path, value

def objects(value,path='',node=None):
    if isinstance(value,dict):
        if value.get('$type','').endswith('NodeDefinition') or value.get('$type','').endswith('Node'):
            node=value.get('id',value.get('nodeId',node))
        yield path,node,value
        for k,v in value.items():
            yield from objects(v,f'{path}.{k}' if path else k,node)
    elif isinstance(value,list):
        for i,v in enumerate(value):
            yield from objects(v,f'{path}.{i}',node)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data=json.loads((INDEX/'analysis.json').read_text(encoding='utf-8'))
    source_nodes=[n for n in data['nodes'] if ('\\q307\\' in n['resource'] and '\\test\\' not in n['resource']) or 'ep1_media_bugfixing' in n['resource']]
    selected=[]
    for n in source_nodes:
        if n['node_type'] in ('questJournalNodeDefinition','questCharacterManagerNodeDefinition','questInventoryNodeDefinition','questItemManagerNodeDefinition','questEquipItemNodeDefinition','questPhoneManagerNodeDefinition','questGameManagerNodeDefinition') or 'persistent_content' in n['resource'] or 'ep1_media_bugfixing' in n['resource']:
            edges=[e for e in data['edges'] if e['graph']==n['graph'] and (e['destination_node_id']==n['node_id'] or e['source_node_id']==n['node_id'])]
            selected.append({**n,'edges':[{k:e[k] for k in ('source_node_id','source_socket','destination_node_id','destination_socket')} for e in edges]})
    (OUT/'logical_nodes.json').write_text(json.dumps(selected,indent=2),encoding='utf-8')
    journal=json.loads((ROOT/'research/phase2b_p2/extracted/json/ep1/journal/cooked_journal.journal.json').read_text(encoding='utf-8'))
    found=[]
    for path,obj in journal_entries(journal['Data']['RootChunk']['entry']):
        if re.search(r'q307|internet_2_years_later|2079',path,re.I):
            found.append({'path':path,'class':obj.get('$type'),'fields':dict(flatten(obj))})
    (OUT/'journal_entries.json').write_text(json.dumps(found,indent=2),encoding='utf-8')
    with (INDEX/'facts.csv').open(encoding='utf-8-sig') as f:
        facts=[r for r in csv.DictReader(f) if ('\\q307\\' in r['resource'] and '\\test\\' not in r['resource']) or 'ep1_media_bugfixing' in r['resource']]
    (OUT/'facts.json').write_text(json.dumps(facts,indent=2),encoding='utf-8')
    effects=[]
    dialogue=[]
    qroot=ROOT/'research/q307_extracted/json/ep1/quest/main_quests/q307'
    wanted={'questCharacterManagerParameters_SetStatusEffect','questRemoveAllContacts_NodeType','questChangeContactList_NodeTypeParams','questAddRemoveItem_NodeType','questSetItemTags_NodeType','questEquipItemParams','questCharacterManagerVisuals_ChangeEntityAppearance'}
    for src in qroot.rglob('*.json'):
        if 'test' in src.parts:
            continue
        raw=json.loads(src.read_text(encoding='utf-8'))
        for path,node,obj in objects(raw):
            if obj.get('$type') in wanted:
                effects.append({'resource':str(src.relative_to(ROOT/'research/q307_extracted/json'))[:-5], 'json_path':path,'node':node,'fields':dict(flatten(obj))})
            content=obj.get('content','')
            if content and re.search(r'cyberware|implant|relic|engram|zetatech|evict|apartment|garage',content,re.I):
                dialogue.append({'resource':src.name[:-5],'json_path':path,'content':content,'variant_id':obj.get('variantId')})
    (OUT/'item_contact_effects.json').write_text(json.dumps(effects,indent=2),encoding='utf-8')
    (OUT/'narrative_content_matches.json').write_text(json.dumps(dialogue,indent=2,ensure_ascii=False),encoding='utf-8')
    with (INDEX/'internet_2_years_later_nodes.csv').open(encoding='utf-8-sig') as f:
        internet=[r for r in csv.DictReader(f) if r['journal_path'] and r['reachable_from_input']=='True']
    groups=defaultdict(Counter)
    for r in internet:
        p=r['journal_path']
        site=p.split('internet_2_years_later/')[-1].split('/')[0] if 'internet_2_years_later/' in p else '/'.join(p.split('/')[:2])
        groups[site][r['incoming_sockets']]+=1
    summary={'scoped_resource_count':len(set(n['resource'] for n in source_nodes)),
      'selected_logical_node_count':len(selected),'journal_classes':dict(Counter(r['class'] for r in found)),
      'internet_journal_nodes_by_site_and_input':{k:dict(v) for k,v in sorted(groups.items())},
      'production_fact_count':len(set(r['fact'] for r in facts)),
      'journal_entries_count':len(found)}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    main()
