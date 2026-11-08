"""Read the verified successor, including dispatches and explicit coverage holds."""

import argparse
import importlib.util
import json
import sqlite3

from common import *

spec = importlib.util.spec_from_file_location('ptfr_parent_search',PREVIOUS/'search.py')
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)

KINDS = {**legacy.KIND_NAMES,'dispatch':'VOICESET_DISPATCH','voice-tag':'VOICE_TAG',
         'sound':'SUPPORT_SOUND_EVENT','metadata':'VOICE_METADATA','boundary':'BOUNDARY'}


def open_database(path):
    if not path.is_file():
        raise SystemExit('Verified successor database is missing')
    db = sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)
    db.row_factory = sqlite3.Row
    metadata = dict(db.execute('SELECT key,value FROM metadata'))
    if metadata.get('status')!='VERIFIED' or metadata.get('coverage_successor_schema')!='1':
        raise SystemExit('Use the successor sealed by Step 2 source verification')
    return db


def search(db,args):
    if args.kind=='boundary':
        filters=[];parameters=[]
        if args.text:
            filters.append('(b.details_json LIKE ? OR b.kind LIKE ?)')
            parameters.extend(['%'+args.text+'%']*2)
        if args.scene:
            filters.append('(r.depot LIKE ? OR b.details_json LIKE ?)')
            parameters.extend(['%'+args.scene+'%']*2)
        if args.scope:
            filters.append('r.scope=?');parameters.append(args.scope)
        sql='SELECT b.*,r.depot,r.scope,r.raw_sha256 FROM coverage_boundaries b LEFT JOIN resources r ON r.resource_id=b.resource_id'
        if filters:sql+=' WHERE '+' AND '.join(filters)
        rows=[dict(r) for r in db.execute(sql+' ORDER BY b.boundary_id LIMIT ?',parameters+[args.limit])]
        for row in rows:
            row['item_key']=row['boundary_id'];row['details']=json.loads(row.pop('details_json'))
        return rows
    filters=[];parameters=[]
    joins='LEFT JOIN resources r ON r.resource_id=s.resource_id LEFT JOIN nodes n ON n.root_id=s.root_id AND n.graph_path=s.graph_path AND n.node_id=s.node_id'
    if args.text:
        joins+=' JOIN search_fts ON search_fts.rowid=s.item_id'
        filters.append('search_fts MATCH ?');parameters.append(args.text)
    if args.kind=='default':filters.append("s.kind IN ('DIALOGUE_EVENT','CHOICE')")
    elif args.kind!='all':filters.append('s.kind=?');parameters.append(KINDS[args.kind])
    for field in ['speaker','addressee']:
        term=getattr(args,field)
        if not term:continue
        if term.lower()=='johnny':
            filters.append('s.'+field+"_role IN ('JOHNNY','JOHNNY_REFERENCE_LEAD')")
        elif term.lower()=='v':
            filters.append('s.'+field+"_role='V'")
        else:
            filters.append('s.'+field+' LIKE ?');parameters.append('%'+term+'%')
    for value,column in [(args.actor,'s.actor_roles'),(args.scene,'s.depot'),(args.binding,'s.binding_status')]:
        if value:filters.append(column+' LIKE ?');parameters.append('%'+value+'%')
    if args.scope:filters.append('r.scope=?');parameters.append(args.scope)
    sql='''SELECT s.item_key,s.kind,s.depot,s.graph_path,s.node_id,s.line_id,s.loc_id,
        s.speaker,s.speaker_role,s.addressee,s.addressee_role,s.text,s.text_source,s.binding_status,
        r.scope,r.archive,r.raw_sha256,n.reachable AS structural_reachable,n.entry_names_json
        FROM search_items s '''+joins
    if filters:sql+=' WHERE '+' AND '.join(filters)
    rows=[dict(r) for r in db.execute(sql+' ORDER BY s.depot,s.root_id,s.graph_path,s.node_id,s.item_id LIMIT ?',parameters+[args.limit])]
    for row in rows:
        names=row.pop('entry_names_json')
        row['structural_entry_names']=json.loads(names) if names else []
    return rows


def source_check(db,item):
    if not item['resource_id']:return None
    row=db.execute('SELECT * FROM supplemental_sources WHERE resource_id=?',(item['resource_id'],)).fetchone()
    if row and item['kind'] in {'VOICESET_DISPATCH','VOICE_TAG','VOICE_METADATA','SUPPORT_SOUND_EVENT'}:
        path,digest=row['json_path'],row['json_sha256']
    else:
        resource=db.execute('SELECT json_path,json_sha256 FROM resources WHERE resource_id=?',(item['resource_id'],)).fetchone()
        path,digest=resource
    if path and sha(path)!=digest:
        raise SystemExit('Retained source export changed after indexing')
    return {'json_path':path,'json_sha256':digest,'hash_verified':bool(path)}


def parsed(row):
    result=dict(row)
    for key in list(result):
        if key.endswith('_json'):
            result[key[:-5]]=json.loads(result.pop(key))
    return result


def ancestors(path,source_path):
    document=read(path)
    result=[];obj=document;at=''
    for part in source_path.strip('/').split('/'):
        if isinstance(obj,dict) and '$type' in obj:
            fields={k:scalar(v) for k,v in obj.items() if k!='$type' and
                    (isinstance(v,(str,int,float,bool)) or isinstance(v,dict) and
                     (v.get('$type') in {'CName','NodeRef','ResourcePath','TweakDBID'} or v.get('$type','').endswith('Id')))}
            result.append({'source_path':at,'type':obj['$type'],'scalar_fields':fields})
        obj=obj[int(part)] if isinstance(obj,list) else obj[part]
        at+='/'+part
    return result


def context(db,key,depth):
    boundary=db.execute('SELECT * FROM coverage_boundaries WHERE boundary_id=?',(key,)).fetchone()
    if boundary:
        result={'boundary':parsed(boundary)}
        if boundary['resource_id']:
            resource=dict(db.execute('SELECT * FROM resources WHERE resource_id=?',(boundary['resource_id'],)).fetchone())
            path=resource['json_path'] or resource['raw_path']
            expected=resource['json_sha256'] if resource['json_path'] else resource['raw_sha256']
            if path and sha(path)!=expected:
                raise SystemExit('Boundary source changed after indexing')
            result['resource']=resource
            result['verified_boundary_source']={'path':path,'sha256':expected,'hash_verified':bool(path)}
        return result
    item=db.execute('SELECT * FROM search_items WHERE item_key=?',(key,)).fetchone()
    if item is None:raise SystemExit('Unknown result key')
    checked=source_check(db,item)
    result=legacy.context(db,key,depth)
    result['verified_source_export']=checked
    result['coverage_boundaries']=[parsed(r) for r in db.execute(
        'SELECT * FROM coverage_boundaries WHERE resource_id=? OR resource_id IS NULL',(item['resource_id'],))]
    if item['root_id'] and item['graph_path']:
        graph=db.execute('SELECT * FROM phase_graphs WHERE root_id=? AND graph_path=?',
                         (item['root_id'],item['graph_path'])).fetchone()
        if graph:
            result['graph_source']=parsed(graph)
            result['adjacent_source_connections']=[]
            for row in db.execute('SELECT * FROM graph_connections WHERE root_id=? AND graph_path=?',
                                  (item['root_id'],item['graph_path'])):
                row=parsed(row)
                if any(o['node']==item['node_id'] for end in [row['source'],row['destination']] for o in end['owners']):
                    result['adjacent_source_connections'].append(row)
    if item['kind']=='VOICESET_DISPATCH':
        result['dispatch']=parsed(db.execute('SELECT * FROM dispatches WHERE dispatch_key=?',(key,)).fetchone())
        result['target_binding_candidates']=[]
        for row in db.execute('''SELECT t.*,v.tag_name,v.tag_id,v.scene_depot,v.resource_id AS tag_provider_resource_id,
            r.archive AS target_archive,r.raw_sha256 AS target_sha256 FROM dispatch_targets t
            LEFT JOIN voice_tags v ON v.tag_key=t.tag_key LEFT JOIN resources r ON r.resource_id=t.target_resource_id
            WHERE dispatch_key=? ORDER BY target_key''',(key,)):
            target=parsed(row)
            target['dialogue_candidates']=[dict(r) for r in db.execute('''SELECT c.event_key,c.evidence,s.speaker,
                s.speaker_role,s.addressee,s.loc_id,s.text,s.text_source FROM dispatch_dialogue_candidates c
                JOIN search_items s ON s.item_key=c.event_key WHERE c.target_key=? ORDER BY c.event_key''',(row['target_key'],))]
            result['target_binding_candidates'].append(target)
        if not result['target_binding_candidates']:
            name=result['dispatch']['voiceset_name']
            result['entry_name_leads']=[dict(r) for r in db.execute('''SELECT e.root_id,e.name,e.node_id,r.depot,
                r.archive,r.raw_sha256 FROM entries e JOIN roots rt ON rt.root_id=e.root_id
                JOIN resources r ON r.resource_id=rt.resource_id WHERE e.graph_path='scene' AND e.name=?
                ORDER BY r.depot LIMIT 25''',(name,))]
            result['entry_name_lead_limit']='Exact name matches only; these do not bind the caller to an actor or scene.'
        result['dispatch_limit']='Named-entry links and reachable lines are candidates. Actor/player context, conditions, provider selection and post-Tower execution remain unproved.'
    elif item['kind']=='VOICE_TAG':
        result['voice_tag']=parsed(db.execute('SELECT * FROM voice_tags WHERE tag_key=?',(key,)).fetchone())
        result['scene_provider_candidates']=[dict(r) for r in db.execute('SELECT * FROM resources WHERE depot_key=?',
            (result['voice_tag']['scene_key'],))]
    elif item['kind']=='SUPPORT_SOUND_EVENT':
        result['sound_event']=parsed(db.execute('SELECT * FROM sound_events WHERE sound_key=?',(key,)).fetchone())
        result['source_ancestors']=ancestors(checked['json_path'],result['sound_event']['source_path'])
        result['sound_limit']='Animation sound-event names do not establish speech, actor voice or Johnny attribution.'
    elif item['kind']=='VOICE_METADATA':
        result['voice_metadata']=parsed(db.execute('SELECT * FROM voice_metadata WHERE metadata_key=?',(key,)).fetchone())
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,default=INDEX/'dialogue.sqlite3')
    for name in ['text','speaker','addressee','actor','scene','binding']:
        parser.add_argument('--'+name)
    parser.add_argument('--scope',choices=['CURRENT_PTFR_PAYLOAD','REFERENCE_CENSUS','GLOBAL_CENSUS_UNCLASSIFIED','AUXILIARY_SOURCE'])
    parser.add_argument('--kind',default='default',choices=['default','all',*KINDS])
    parser.add_argument('--limit',type=int,default=20)
    parser.add_argument('--context')
    parser.add_argument('--depth',type=int,default=1,choices=range(6))
    args=parser.parse_args()
    if not 1<=args.limit<=1000:parser.error('--limit must be between 1 and 1000')
    if args.kind=='boundary' and any([args.speaker,args.addressee,args.actor,args.binding]):
        parser.error('Boundary queries support --text, --scene and --scope filters')
    db=open_database(args.database)
    try:
        result=context(db,args.context,args.depth) if args.context else search(db,args)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except sqlite3.OperationalError as error:
        parser.error(str(error))
    finally:db.close()


if __name__=='__main__':
    main()
