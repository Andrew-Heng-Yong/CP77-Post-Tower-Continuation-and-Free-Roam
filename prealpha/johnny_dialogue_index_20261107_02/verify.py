"""Compare the successor with its parent and independently pinned source evidence."""

import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone

from common import *


def objects(value,path=''):
    if isinstance(value,dict):
        yield path,value
        for key,child in value.items():
            yield from objects(child,path+'/'+key)
    elif isinstance(value,list):
        for ordinal,child in enumerate(value):
            yield from objects(child,path+'/'+str(ordinal))


def independent_graphs(document):
    handles={str(obj['HandleId']):obj['Data'] for _,obj in objects(document)
             if 'HandleId' in obj and 'Data' in obj}
    def deref(obj):
        if isinstance(obj,dict) and 'HandleId' in obj:return obj['Data']
        if isinstance(obj,dict) and 'HandleRefId' in obj:return handles.get(str(obj['HandleRefId']))
        return obj
    def hid(obj):
        return str(obj.get('HandleId',obj.get('HandleRefId'))) if isinstance(obj,dict) else None
    result=[]
    def phase(wrapped,path):
        graph=deref(wrapped)
        if graph is None:return
        nodes=[deref(x) for x in graph.get('nodes',[])]
        ports={};connections={};entries=[]
        for node in nodes:
            node_id=str(node['id'])
            if node['$type'] in {'questInputNodeDefinition','questStartNodeDefinition'}:
                entries.append((str(scalar(node.get('socketName',''))),node_id))
            for wrapped_socket in node.get('sockets',[]):
                socket=deref(wrapped_socket)
                ports[hid(wrapped_socket)]=(node_id,str(scalar(socket.get('name',''))))
                for wrapped_connection in socket.get('connections',[]):
                    connections[hid(wrapped_connection)]=deref(wrapped_connection)
        edges=[];boundary_handles=[]
        for key,connection in connections.items():
            start=ports.get(hid(connection.get('source')))
            end=ports.get(hid(connection.get('destination')))
            if start and end:edges.append((*start,*end))
            else:
                # Both known boundary fixtures have literal null endpoints.
                assert connection.get('source') is None or connection.get('destination') is None
                boundary_handles.append(key)
        result.append({'path':path,'nodes':[(str(n['id']),n['$type']) for n in nodes],
                       'entries':entries,'edges':edges,'connections':connections,'boundaries':boundary_handles})
        for node in nodes:
            if node.get('phaseGraph') is not None:phase(node['phaseGraph'],path+'/'+str(node['id']))
    root=document['Data']['RootChunk']
    phase(root.get('graph'),'root')
    if root.get('sceneGraph') is not None:
        graph=deref(root['sceneGraph'])
        nodes=[deref(x) for x in graph.get('graph',[])]
        edges=[]
        for node in nodes:
            key=str(scalar(node['nodeId']))
            for socket in node.get('outputSockets',[]):
                stamp=socket.get('stamp',{})
                for end in socket.get('destinations',[]):
                    to=end.get('isockStamp',{})
                    edges.append((key,str(stamp.get('name',0))+':'+str(stamp.get('ordinal',0)),
                        str(scalar(end['nodeId'])),str(to.get('name',0))+':'+str(to.get('ordinal',0))))
            quest=deref(node.get('questNode'))
            if isinstance(quest,dict) and quest.get('phaseGraph') is not None:
                phase(quest['phaseGraph'],'scene/'+key)
        result.append({'path':'scene','nodes':[(str(scalar(n['nodeId'])),n['$type']) for n in nodes],
            'entries':[(str(scalar(e['name'])),str(scalar(e['nodeId']))) for e in root.get('entryPoints',[])],
            'edges':edges,'connections':{},'boundaries':[]})
    for embedded in document['Data'].get('EmbeddedFiles',[]):
        if 'graph' in embedded.get('Content',{}):
            phase(embedded['Content']['graph'],'embedded/'+str(scalar(embedded['FileName']))+'/root')
    return result


def main():
    result_path=INDEX/'verification.json'
    if result_path.exists():raise SystemExit('Preserve the existing verification receipt')
    prepared=read(TASK/'evidence_01/prepared.json')
    build=read(INDEX/'index_build.json')
    expected={str(Path(r['path']).resolve()):r['sha256'] for r in prepared['protected']+prepared['pins']}
    expected[str(Path(prepared['parent']['path']).resolve())]=prepared['parent']['sha256']
    for row in prepared['resources']:
        expected[row['raw']]=row['sha256'];expected[row['json']]=row['json_sha256']
    for path,digest in expected.items():assert sha(path)==digest,path
    archive_checks=read(COVERAGE/'evidence_01/prepared.json')['archives']
    # Reuse the exact nanosecond conversion from the immutable coverage verifier.
    import importlib.util
    spec=importlib.util.spec_from_file_location('coverage_verify',COVERAGE/'verify.py')
    module=importlib.util.module_from_spec(spec)
    # Its only project helper import is prepare. Load the pure helper explicitly.
    import sys
    sys.path.insert(0,str(COVERAGE))
    spec.loader.exec_module(module)
    for row in archive_checks:
        info=Path(row['path']).stat()
        assert info.st_size==row['bytes'] and info.st_mtime_ns==module.expected_ns(row['mtime_utc'])
    db=sqlite3.connect(build['database'],uri=True)
    parent_uri=Path(prepared['parent']['path']).as_uri()+'?mode=ro'
    db.execute('ATTACH DATABASE ? AS parent',(parent_uri,))
    retained=['resources','roots','actors','lines','nodes','edges','entries','events','choices',
              'localization','aux_links','script_calls','source_references','issues','search_items']
    retained_checks={}
    for table in retained:
        columns=[r[1] for r in db.execute('PRAGMA parent.table_info("'+table+'")')]
        if table=='search_items':columns=[c for c in columns if c not in {'text','text_source'}]
        equality=' AND '.join('s."'+c+'" IS p."'+c+'"' for c in columns)
        differences=db.execute('SELECT count(*) FROM parent."'+table+'" p LEFT JOIN main."'+table+
            '" s ON s.rowid=p.rowid WHERE s.rowid IS NULL OR NOT ('+equality+')').fetchone()[0]
        assert differences==0,(table,differences)
        retained_checks[table]=db.execute('SELECT count(*) FROM parent."'+table+'"').fetchone()[0]
        print('Retained parent records verified:',table,retained_checks[table],flush=True)
    assert db.execute("SELECT count(*) FROM search_items WHERE item_id<=(SELECT max(item_id) FROM parent.search_items) AND binding_status!='SOURCE_DEFINED'").fetchone()[0]==0
    source_counts=Counter();new_ids=set();reused=Counter();voice_params=0;graph_count=0;null_connections=0
    for ordinal,row in enumerate(prepared['resources'],1):
        obj=read(row['json']);rid=row['resource_id'];root=rid+'/root'
        resource=db.execute('SELECT raw_sha256 FROM resources WHERE resource_id=?',(rid,)).fetchone()
        assert resource[0]==row['sha256']
        old=db.execute('SELECT kind FROM parent.resources WHERE resource_id=?',(rid,)).fetchone()
        if old:reused[old[0]]+=1
        if 'UNNAMED_ENGLISH_TEXT' in row['reasons']:
            expected_text=[]
            for path,item in objects(obj):
                if item.get('$type')=='localizationPersistenceSubtitleEntry':
                    new_ids.add(str(item['stringId']))
                    expected_text.extend((str(item['stringId']),gender,item.get(field,''),path+'/'+field)
                        for gender,field in [('female','femaleVariant'),('male','maleVariant')])
            actual=list(db.execute('SELECT loc_id,gender,text,source_path FROM localization WHERE provider_resource_id=?',(rid,)))
            assert Counter(actual)==Counter(expected_text),('subtitle variants',rid)
            source_counts['subtitle_entries']+=len(expected_text)//2
        elif 'VOICESET_DISPATCH_GRAPH' in row['reasons']:
            graphs=independent_graphs(obj);graph_count+=len(graphs)
            actual_nodes=defaultdict(list);actual_edges=defaultdict(list);actual_entries=defaultdict(list)
            for gp,node,kind in db.execute('SELECT graph_path,node_id,type FROM nodes WHERE root_id=?',(root,)):actual_nodes[gp].append((node,kind))
            for gp,a,b,c,d in db.execute('SELECT graph_path,source_node,output_stamp,destination_node,input_stamp FROM edges WHERE root_id=?',(root,)):actual_edges[gp].append((a,b,c,d))
            for gp,name,node in db.execute('SELECT graph_path,name,node_id FROM entries WHERE root_id=?',(root,)):actual_entries[gp].append((name,node))
            for graph in graphs:
                gp=graph['path']
                assert Counter(actual_nodes[gp])==Counter(graph['nodes']),('nodes',rid,gp)
                assert Counter(actual_edges[gp])==Counter(graph['edges']),('edges',rid,gp)
                assert Counter(actual_entries[gp])==Counter(graph['entries']),('entries',rid,gp)
                actual_connections={r[0]:r[1] for r in db.execute('SELECT handle_id,classification FROM graph_connections WHERE root_id=? AND graph_path=?',(root,gp))}
                assert set(actual_connections)==set(graph['connections'])
                assert {k for k,v in actual_connections.items() if v=='SOURCE_INTERFACE_BOUNDARY'}==set(graph['boundaries'])
                null_connections+=len(graph['boundaries'])
            voice_params+=sum(len(item.get('params',[])) for _,item in objects(obj) if item.get('$type')=='questPlayVoiceset_NodeType')
        else:
            tags=[];sounds=[];metadata=[]
            for path,item in objects(obj):
                kind=item.get('$type','')
                if kind=='locVoiceTag':tags.append((path,item))
                elif kind=='animAnimEvent_Sound':sounds.append((path,item))
                elif re.search(r'(?i)(voice|dialogline|speech)',kind) and kind!='locVoiceTagListResource':metadata.append((path,item))
            for table,key,items in [('voice_tags','payload_json',tags),('sound_events','payload_json',sounds),('voice_metadata','payload_json',metadata)]:
                actual=[(p,json.loads(payload)) for p,payload in db.execute('SELECT source_path,'+key+' FROM '+table+' WHERE resource_id=?',(rid,))]
                assert Counter((p,encode(v)) for p,v in actual)==Counter((p,encode(v)) for p,v in items),(table,rid)
                source_counts[table]+=len(items)
        if ordinal%80==0:print('Supplemental sources independently compared:',ordinal,flush=True)
    assert dict(reused)=={'SCENE':26,'ENGLISH_SUBTITLES':12}
    assert voice_params==3433 and graph_count==7043 and null_connections==6
    old_dispatches=read(COVERAGE/'evidence_07/voiceset_dispatch_inventory.json')['dispatches']
    for row in old_dispatches:
        rid=resource_id(row['source_archive'],row['source_key'])
        key=rid+'/root/'+row['graph_path']+'/'+row['node_id']+'/voiceset/'+str(row['operation_ordinal'])+'/'+str(row['param_ordinal'])
        actual=db.execute('SELECT payload_json,voiceset_name,role_lead FROM dispatches WHERE dispatch_key=?',(key,)).fetchone()
        assert actual and json.loads(actual[0])==row['payload'] and actual[1]==row['voiceset_name'] and actual[2]==row['role_lead']
    assert db.execute('SELECT count(*) FROM dispatches').fetchone()[0]==3433
    print('All dispatch identities, raw parameters, graphs and source boundaries verified',flush=True)

    external=defaultdict(list)
    for start in range(0,len(new_ids),400):
        chunk=sorted(new_ids)[start:start+400]
        for loc,text in db.execute("SELECT loc_id,text FROM localization WHERE root_id IS NULL AND locale='en_us' AND text<>'' AND loc_id IN ("+','.join('?' for _ in chunk)+') ORDER BY text_id',chunk):
            if text not in external[loc]:external[loc].append(text)
    new_text_candidates=Counter();text_changes=0;choice_count=0
    for item,kind,loc,old_text,old_source in db.execute('SELECT item_id,kind,loc_id,text,text_source FROM parent.search_items'):
        actual=db.execute('SELECT text,text_source FROM main.search_items WHERE item_id=?',(item,)).fetchone()
        expected_text,expected_source=old_text,old_source
        if kind in {'DIALOGUE_EVENT','STORED_LINE'} and loc in new_ids:
            assert external[loc]
            expected_text='\n'.join(external[loc]);expected_source='EXTERNAL_SUBTITLE_VARIANTS'
            if old_source=='UNRESOLVED':new_text_candidates[kind]+=1
        if kind=='CHOICE':choice_count+=1
        assert tuple(actual)==(expected_text,expected_source),('text domain',item)
        text_changes+=tuple(actual)!=(old_text,old_source)
    assert dict(new_text_candidates)=={'DIALOGUE_EVENT':308,'STORED_LINE':10}
    assert text_changes==1347 and choice_count==44663
    print('All retained search text and choice lookup domains verified',flush=True)
    target_rows=db.execute('''SELECT t.target_key,t.dispatch_key,t.target_root_id,t.entry_name,t.entry_node,t.status,
        t.target_resource_id,v.scene_key,d.voiceset_name FROM dispatch_targets t
        JOIN voice_tags v ON v.tag_key=t.tag_key JOIN dispatches d ON d.dispatch_key=t.dispatch_key''').fetchall()
    target_event_cache={}
    for target,dispatch,root,name,node,status,rid,key,dispatch_name in target_rows:
        assert name==dispatch_name
        if rid:assert db.execute('SELECT depot_key FROM resources WHERE resource_id=?',(rid,)).fetchone()[0]==key
        candidates={r[0] for r in db.execute('SELECT event_key FROM dispatch_dialogue_candidates WHERE target_key=?',(target,))}
        if node:
            assert status=='EXACT_NAMED_ENTRY_CANDIDATE'
            assert db.execute("SELECT 1 FROM entries WHERE root_id=? AND graph_path='scene' AND name=? AND node_id=?",(root,name,node)).fetchone()
            cache=(root,node)
            if cache not in target_event_cache:
                adjacency=defaultdict(set)
                for a,b in db.execute("SELECT source_node,destination_node FROM edges WHERE root_id=? AND graph_path='scene'",(root,)):adjacency[a].add(b)
                visited={node};todo=[node]
                while todo:
                    for end in adjacency[todo.pop()]-visited:visited.add(end);todo.append(end)
                target_event_cache[cache]={event for event,n in db.execute("SELECT event_key,node_id FROM events WHERE root_id=? AND graph_path='scene' AND type='scnDialogLineEvent'",(root,)) if n in visited}
            assert candidates==target_event_cache[cache]
        else:assert not candidates and status=='NO_EXACT_ENTRY_OR_SCENE_PROVIDER'
    assert len(target_rows)==468
    assert db.execute('SELECT count(*) FROM dispatch_dialogue_candidates').fetchone()[0]==572
    assert db.execute("SELECT count(*) FROM coverage_boundaries WHERE kind='SOURCE_SOCKET_INTERFACE_BOUNDARY'").fetchone()[0]==6
    assert db.execute("SELECT count(*) FROM coverage_boundaries WHERE kind='OPAQUE_SCENE_DECODE_HOLD'").fetchone()[0]==1
    assert db.execute('PRAGMA integrity_check').fetchall()==[('ok',)]
    db.execute("INSERT INTO search_fts(search_fts,rank) VALUES('integrity-check',1)")
    # Source verification seals the DB; selection additionally requires CLI checks.
    stamp=datetime.now(timezone.utc).isoformat()
    db.execute("UPDATE metadata SET value='VERIFIED' WHERE key='status'")
    db.execute('INSERT INTO metadata VALUES(?,?)',('verified_utc',stamp))
    db.commit()
    unresolved={kind:count for kind,count in db.execute("SELECT kind,count(*) FROM search_items WHERE kind IN ('DIALOGUE_EVENT','CHOICE') AND text_source='UNRESOLVED' GROUP BY kind")}
    db.close()
    partial=Path(build['database']);final=INDEX/'dialogue.sqlite3'
    assert not final.exists();partial.rename(final)
    manifest={'path':str(final),'sha256':sha(final),'bytes':final.stat().st_size}
    write(INDEX/'database_manifest.json',manifest)
    write(result_path,{'status':'PASS','verified_utc':stamp,'database':manifest,
        'exact_source_and_protected_file_hash_checks':len(expected),'archive_metadata_checks':len(archive_checks),
        'parent_records_compared':retained_checks,'supplemental_exports_compared':476,
        'reused_parent_resources':dict(reused),'new_resources':438,'new_english_providers':29,
        'independent_graphs_compared':graph_count,'independent_dispatch_params_compared':voice_params,
        'independent_voice_and_sound_records':dict(source_counts),'retained_choices_unchanged':choice_count,
        'requalified_text_items':text_changes,'new_nonempty_text_matches':dict(new_text_candidates),
        'unresolved_english_items':unresolved,'candidate_named_entry_bindings':len(target_rows),
        'candidate_dialogue_links_verified':572,'literal_null_socket_connections_preserved':null_connections,
        'q303_decode_status':'HELD_WITH_EXACT_RAW_PROVENANCE','sqlite_and_fts_integrity':'PASS',
        'game_writes':0,'save_writes':0,'parent_index_writes':0,'step3_started':False})
    print(encode(read(result_path)))


if __name__=='__main__':
    main()
