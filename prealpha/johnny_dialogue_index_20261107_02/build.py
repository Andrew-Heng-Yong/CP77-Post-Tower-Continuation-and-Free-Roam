"""Create an additive index successor; no game resources are modified."""

import json
import re
import shutil
import sqlite3
from collections import Counter, defaultdict

from common import *
from graphs import PhaseSource

SCHEMA = '''
CREATE TABLE supplemental_sources(resource_id TEXT PRIMARY KEY, json_path TEXT,
 json_sha256 TEXT, reasons_json TEXT, reused_parent_resource INTEGER);
CREATE TABLE phase_graphs(root_id TEXT, graph_path TEXT, subresource TEXT,
 parent_graph TEXT, parent_node TEXT, entries_json TEXT, prefabs_json TEXT,
 interface_boundaries INTEGER, PRIMARY KEY(root_id,graph_path));
CREATE TABLE graph_connections(root_id TEXT, graph_path TEXT, connection_ordinal INTEGER,
 handle_id TEXT, classification TEXT, source_json TEXT, destination_json TEXT,
 PRIMARY KEY(root_id,graph_path,connection_ordinal));
CREATE TABLE dispatches(dispatch_key TEXT PRIMARY KEY, resource_id TEXT, root_id TEXT,
 graph_path TEXT, node_id TEXT, operation_ordinal INTEGER, param_ordinal INTEGER,
 source_path TEXT, voiceset_name TEXT, is_player INTEGER, role_lead TEXT,
 binding_status TEXT, puppet_json TEXT, payload_json TEXT);
CREATE TABLE voice_tags(tag_key TEXT PRIMARY KEY, resource_id TEXT, source_path TEXT,
 tag_id TEXT, tag_name TEXT, scene_depot TEXT, scene_key TEXT, payload_json TEXT);
CREATE INDEX voice_tags_name ON voice_tags(tag_name);
CREATE TABLE dispatch_targets(target_key TEXT PRIMARY KEY, dispatch_key TEXT,
 tag_key TEXT, target_resource_id TEXT, target_root_id TEXT, entry_name TEXT,
 entry_node TEXT, status TEXT, evidence_json TEXT);
CREATE INDEX dispatch_targets_dispatch ON dispatch_targets(dispatch_key);
CREATE TABLE dispatch_dialogue_candidates(dispatch_key TEXT, target_key TEXT,
 event_key TEXT, evidence TEXT, PRIMARY KEY(dispatch_key,target_key,event_key));
CREATE TABLE sound_events(sound_key TEXT PRIMARY KEY, resource_id TEXT,
 source_path TEXT, event_name TEXT, payload_json TEXT);
CREATE TABLE voice_metadata(metadata_key TEXT PRIMARY KEY, resource_id TEXT,
 source_path TEXT, type TEXT, payload_json TEXT);
CREATE TABLE coverage_boundaries(boundary_id TEXT PRIMARY KEY, resource_id TEXT,
 root_id TEXT, graph_path TEXT, node_id TEXT, kind TEXT, details_json TEXT);
CREATE INDEX entries_name_lookup ON entries(name,root_id,graph_path);
CREATE INDEX resources_depot_key ON resources(depot_key);
CREATE INDEX search_resource_kind ON search_items(resource_id,kind);
ALTER TABLE search_items ADD COLUMN binding_status TEXT DEFAULT 'SOURCE_DEFINED';
'''


class Builder:
    def __init__(self, connection, prepared):
        self.db = connection
        self.prepared = prepared
        self.counts = Counter()
        self.source_scope_changes = []
        first = WORKSPACE / 'prealpha/johnny_dialogue_removal_20261107_01/step1_01'
        self.captured = {(r['archive'].casefold(),r['key']) for name in ['capture.json','capture_additions.json']
                         for r in read(first/name)['resources']}

    def search(self, key, kind, resource, text, root=None, graph=None, node=None,
               speaker='', role='', actors='', binding='SOURCE_DEFINED'):
        self.db.execute('''INSERT INTO search_items(kind,item_key,resource_id,root_id,
            graph_path,node_id,line_id,loc_id,speaker,speaker_role,addressee,addressee_role,
            text,depot,actor_roles,text_source,binding_status)
            VALUES(?,?,?,?,?,?,NULL,NULL,?,?,NULL,NULL,?,?,?,'NON_DIALOGUE_SOURCE',?)''',
            (kind,key,resource['resource_id'],root,graph,node,speaker,role,text,resource['depot'],actors,binding))

    def add_resource(self, row):
        reasons = row['reasons']
        kind = ('ENGLISH_SUBTITLES' if 'UNNAMED_ENGLISH_TEXT' in reasons else
                'QUEST_SOURCE' if 'VOICESET_DISPATCH_GRAPH' in reasons else
                'VOICE_IDENTITY_SOURCE' if 'VOICE_IDENTITY_METADATA' in reasons else 'SOUND_SUPPORT_SOURCE')
        scope = row['scope']
        if kind == 'QUEST_SOURCE' and scope != 'CURRENT_PTFR_PAYLOAD':
            scope = ('REFERENCE_CENSUS' if (row['archive'].casefold(),row['key']) in self.captured
                     else 'GLOBAL_CENSUS_UNCLASSIFIED')
        if scope != row['scope']:
            self.source_scope_changes.append({'resource_id':row['resource_id'],'prepared_scope':row['scope'],'qualified_scope':scope})
        previous = self.db.execute('SELECT raw_sha256,kind FROM resources WHERE resource_id=?', (row['resource_id'],)).fetchone()
        self.db.execute('INSERT INTO supplemental_sources VALUES(?,?,?,?,?)',
            (row['resource_id'],row['json'],row['json_sha256'],encode(reasons),int(previous is not None)))
        if previous:
            assert previous[0] == row['sha256']
            assert ((previous[1]=='SCENE' and row['root_type']=='scnSceneResource') or
                    (previous[1]=='ENGLISH_SUBTITLES' and 'UNNAMED_ENGLISH_TEXT' in reasons))
            self.counts['reused_parent_'+previous[1].lower()+'_resources'] += 1
            return False
        self.db.execute('INSERT INTO resources VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (row['resource_id'],kind,row['depot'],row['key'],row['archive'],row['provider_role'],scope,
             row['sha256'],row['raw'],row['json'],row['json_sha256'],'INDEXED',row['root_type'],None))
        self.counts['new_resources'] += 1
        return True

    def subtitles(self, row, document):
        for path, obj in walk(document):
            if obj.get('$type') != 'localizationPersistenceSubtitleEntry':
                continue
            for gender, field in [('female','femaleVariant'),('male','maleVariant')]:
                self.db.execute('''INSERT INTO localization(provider_resource_id,root_id,loc_id,
                    locale,gender,signature,text,source_path) VALUES(?,NULL,?,'en_us',?,NULL,?,?)''',
                    (row['resource_id'],str(obj['stringId']),gender,obj.get(field,''),path+'/'+field))
                self.counts['new_localization_variants'] += 1

    def root(self, row, document):
        key = row['resource_id'] + '/root'
        if self.db.execute('SELECT 1 FROM roots WHERE root_id=?',(key,)).fetchone():
            assert row['root_type']=='scnSceneResource'
            return key
        root = document['Data']['RootChunk']
        self.db.execute('INSERT INTO roots VALUES(?,?,?,?,?)',
            (key,row['resource_id'],'root',root['$type'],encode({
                'source_kind':self.db.execute('SELECT kind FROM resources WHERE resource_id=?',(row['resource_id'],)).fetchone()[0],
                'root_phase_prefabs':root.get('phasePrefabs',[]),
                'embedded_files':[{'ordinal':i,'name':e.get('FileName'),
                                   'type':e.get('Content',{}).get('$type'),
                                   'phase_prefabs':e.get('Content',{}).get('phasePrefabs',[])}
                                  for i,e in enumerate(document['Data'].get('EmbeddedFiles',[]))]})))
        return key

    def phase(self, row, document):
        root_id = self.root(row,document)
        source = PhaseSource(document)
        for graph in source.graphs:
            boundaries = [c for c in graph['connections'] if c['classification'] != 'LOCAL_EDGE']
            self.db.execute('INSERT INTO phase_graphs VALUES(?,?,?,?,?,?,?,?)',
                (root_id,graph['path'],graph['subresource'],graph['parent_graph'],graph['parent_node'],
                 encode(graph['entries']),encode(graph['root_prefabs']),len(boundaries)))
            if row['root_type']!='scnSceneResource':
                self.db.executemany('INSERT INTO entries VALUES(?,?,?,?)',
                    [(root_id,graph['path'],name,node) for name,node in graph['entries']])
            for key,node in graph['nodes'].items() if row['root_type']!='scnSceneResource' else []:
                objects = [obj for _,obj in walk(node['payload'])]
                conditions = [obj for obj in objects if 'Condition' in obj.get('$type','')]
                reads = [obj for obj in objects if obj.get('$type') in {
                    'questVarComparison_ConditionType','questVarVsVarComparison_ConditionType','questJournalEntryState_ConditionType'}]
                writes = [obj for obj in objects if obj.get('$type') == 'questSetVar_NodeType']
                self.db.execute('INSERT INTO nodes VALUES(?,?,?,?,?,?,?,?,?,?)',
                    (root_id,graph['path'],key,node['source']['$type'],int(key in graph['reachable']),
                     encode(sorted(graph['entry_names'].get(key,set()))),encode(conditions),encode(reads),
                     encode(writes),encode(node['payload'])))
            if row['root_type']!='scnSceneResource':
                self.db.executemany('INSERT INTO edges VALUES(?,?,?,?,?,?,?)',
                    [(root_id,graph['path'],i,*edge) for i,edge in enumerate(graph['edges'])])
            for i,connection in enumerate(graph['connections']):
                self.db.execute('INSERT INTO graph_connections VALUES(?,?,?,?,?,?,?)',
                    (root_id,graph['path'],i,connection['handle'],connection['classification'],
                     encode(connection['source']),encode(connection['destination'])))
                if connection['classification'] != 'LOCAL_EDGE':
                    boundary_key = root_id + '/' + graph['path'] + '/connection/' + str(i)
                    self.db.execute('INSERT INTO coverage_boundaries VALUES(?,?,?,?,?,?,?)',
                        (boundary_key,row['resource_id'],root_id,graph['path'],None,
                         'SOURCE_SOCKET_INTERFACE_BOUNDARY',encode(connection)))
                    self.counts['source_socket_boundaries'] += 1
        for graph,node,operation,ordinal,path,param in source.dispatches():
            puppet = param.get('puppetRef',{})
            label = encode(puppet).lower()
            is_player = int(bool(param.get('isPlayer')))
            role = 'PLAYER_CONTEXT_REQUIRED' if is_player else (
                'JOHNNY_REFERENCE_LEAD' if re.search(r'johnny|silverhand',label) else 'CALLER_BINDING_REQUIRED')
            key = root_id+'/'+graph['path']+'/'+node+'/voiceset/'+str(operation)+'/'+str(ordinal)
            name = str(scalar(param.get('voicesetName','')))
            self.db.execute('INSERT INTO dispatches VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (key,row['resource_id'],root_id,graph['path'],node,operation,ordinal,path,name,is_player,
                 role,'REFERENCE_LEAD_REQUIRES_CALLER_CONTEXT',encode(puppet),encode(param)))
            self.search(key,'VOICESET_DISPATCH',row,name+' '+role+' '+encode(puppet),root_id,graph['path'],node,
                '#johnny (reference lead)' if role=='JOHNNY_REFERENCE_LEAD' else 'player (context required)' if is_player else '',
                role,role,'REFERENCE_LEAD_REQUIRES_CALLER_CONTEXT')
            self.counts['voiceset_dispatch_params'] += 1

    def support(self, row, document):
        root_id = self.root(row,document)
        for path,obj in walk(document):
            kind = obj.get('$type','')
            if kind == 'locVoiceTag':
                key = row['resource_id'] + '/tag' + path
                name = str(scalar(obj.get('voiceTag','')))
                scene = obj.get('voicesetScenePath','')
                self.db.execute('INSERT INTO voice_tags VALUES(?,?,?,?,?,?,?,?)',
                    (key,row['resource_id'],path,str(obj.get('id','')),name,scene,depot_key(scene) if scene else None,encode(obj)))
                self.search(key,'VOICE_TAG',row,name+' '+scene,root_id,
                    actors='JOHNNY' if name=='johnny' else 'V' if name=='v' else '',binding='VOICE_TAG_SOURCE_MAPPING')
                self.counts['voice_tags'] += 1
            elif kind == 'animAnimEvent_Sound':
                key = row['resource_id'] + '/sound' + path
                name = str(scalar(obj.get('eventName','')))
                self.db.execute('INSERT INTO sound_events VALUES(?,?,?,?,?)',
                    (key,row['resource_id'],path,name,encode(obj)))
                self.search(key,'SUPPORT_SOUND_EVENT',row,name,root_id,binding='SOUND_EVENT_PURPOSE_UNRESOLVED')
                self.counts['support_sound_events'] += 1
            elif re.search(r'(?i)(voice|dialogline|speech)',kind) and kind not in {'locVoiceTagListResource'}:
                key = row['resource_id'] + '/metadata' + path
                self.db.execute('INSERT INTO voice_metadata VALUES(?,?,?,?,?)',
                    (key,row['resource_id'],path,kind,encode(obj)))
                names = [str(scalar(child)) for _,child in walk(obj)
                         if child.get('$type')=='CName' and scalar(child) not in {'None',''}]
                self.search(key,'VOICE_METADATA',row,kind+' '+' '.join(dict.fromkeys(names)),root_id,
                    binding='VOICE_METADATA_SOURCE')
                self.counts['voice_metadata_records'] += 1

    def qualify_text(self, ids):
        changed = []
        for start in range(0,len(ids),400):
            chunk = ids[start:start+400]
            placeholders = ','.join('?' for _ in chunk)
            external = defaultdict(list)
            embedded = defaultdict(list)
            for root,loc,text in self.db.execute('SELECT root_id,loc_id,text FROM localization '
                    "WHERE locale='en_us' AND text<>'' AND loc_id IN ("+placeholders+') ORDER BY text_id',chunk):
                values = external[loc] if root is None else embedded[(root,loc)]
                if text not in values:
                    values.append(text)
            rows = self.db.execute('SELECT item_id,kind,root_id,loc_id,text,text_source FROM search_items '
                "WHERE kind IN ('DIALOGUE_EVENT','STORED_LINE') AND loc_id IN ("+placeholders+')',chunk).fetchall()
            for item,kind,root,loc,old_text,old_source in rows:
                values = external.get(loc,[]) or embedded.get((root,loc),[])
                source = ('EXTERNAL_SUBTITLE_VARIANTS' if external.get(loc) else
                          'EMBEDDED_ENGLISH_CANDIDATE' if values else 'UNRESOLVED')
                text = '\n'.join(values)
                if text != old_text or source != old_source:
                    self.db.execute('UPDATE search_items SET text=?,text_source=? WHERE item_id=?',(text,source,item))
                    changed.append({'item_id':item,'kind':kind,'previous_source':old_source,'qualified_source':source,
                                    'text_changed':text!=old_text})
        return changed

    def link_dispatches(self):
        tags = defaultdict(list)
        for row in self.db.execute('SELECT tag_key,tag_name,scene_key,scene_depot FROM voice_tags'):
            tags[row[1].lower()].append(row)
        entry_cache = {}
        for key,name,role,puppet in self.db.execute('SELECT dispatch_key,voiceset_name,role_lead,puppet_json FROM dispatches'):
            aliases = ['johnny'] if role=='JOHNNY_REFERENCE_LEAD' else ['v','johnny'] if role=='PLAYER_CONTEXT_REQUIRED' else []
            reason = 'JOHNNY_REFERENCE_AND_VOICE_TAG_CANDIDATE' if role=='JOHNNY_REFERENCE_LEAD' else 'PLAYER_VOICE_CONTEXT_CANDIDATE'
            if not aliases:
                obj = json.loads(puppet)
                candidates = [str(scalar(v)) for _,v in walk(obj) if v.get('$type')=='CName']
                reference = str(scalar(obj.get('reference',''))).lstrip('#')
                candidates.append(reference)
                aliases = sorted({v.lower() for v in candidates if v.lower() in tags and v.lower() not in {'none',''}})
                reason = 'PUPPET_NAME_VOICE_TAG_ALIAS_CANDIDATE'
            ordinal = 0
            for alias in aliases:
                for tag_key,tag_name,scene_key,scene_depot in tags[alias]:
                    targets = self.db.execute('SELECT resource_id FROM resources WHERE kind=\'SCENE\' AND depot_key=?',(scene_key,)).fetchall()
                    for (resource,) in targets or [(None,)]:
                        root = resource+'/root' if resource else None
                        entries = self.db.execute("SELECT node_id FROM entries WHERE root_id=? AND graph_path='scene' AND name=?",(root,name)).fetchall() if root else []
                        for (node,) in entries or [(None,)]:
                            target_key = key+'/target/'+str(ordinal); ordinal += 1
                            status = 'EXACT_NAMED_ENTRY_CANDIDATE' if node else 'NO_EXACT_ENTRY_OR_SCENE_PROVIDER'
                            self.db.execute('INSERT INTO dispatch_targets VALUES(?,?,?,?,?,?,?,?,?)',
                                (target_key,key,tag_key,resource,root,name,node,status,encode({'rule':reason,'alias':alias,
                                    'scene_depot':scene_depot,'binding_resolved':False})))
                            if not node:
                                continue
                            cache_key = root,node
                            if cache_key not in entry_cache:
                                adjacency = defaultdict(list)
                                for a,b in self.db.execute("SELECT source_node,destination_node FROM edges WHERE root_id=? AND graph_path='scene'",(root,)):
                                    adjacency[a].append(b)
                                seen = {node};todo = [node]
                                while todo:
                                    for end in adjacency[todo.pop()]:
                                        if end not in seen:
                                            seen.add(end);todo.append(end)
                                entry_cache[cache_key] = [event for event,source_node in self.db.execute(
                                    "SELECT event_key,node_id FROM events WHERE root_id=? AND graph_path='scene' AND type='scnDialogLineEvent'",(root,)) if source_node in seen]
                            self.db.executemany('INSERT INTO dispatch_dialogue_candidates VALUES(?,?,?,?)',
                                [(key,target_key,event,'EXACT_ENTRY_STRUCTURAL_BRANCH_CANDIDATE') for event in entry_cache[cache_key]])
            self.counts['dispatch_target_candidates'] += ordinal

    def references_and_boundaries(self):
        seen = set(self.db.execute('SELECT source_depot,source_archive,source_sha256,target_depot,evidence FROM source_references'))
        for line in (COVERAGE/'evidence_07/reference_leads.jsonl').read_text().splitlines():
            row = json.loads(line)
            key = row['source_depot'],row['source_archive'],row['source_sha256'],row['target_depot'],row['evidence']
            if key not in seen:
                self.db.execute('INSERT INTO source_references VALUES(?,?,?,?,?,NULL)',key)
                seen.add(key);self.counts['additional_reference_leads'] += 1
        for row in read(COVERAGE/'evidence_09/boundary_ledger.json')['boundaries']:
            self.db.execute('INSERT INTO coverage_boundaries VALUES(?,NULL,NULL,NULL,NULL,?,?)',
                (row['id'],row['status'],encode(row)))
        probe = read(TASK/'evidence_02/decoder_probe.json')
        assert all(r['code']=='EXCEPTION' and 'fadeColor' in r['error'] for r in probe['attempts'])
        resource = self.db.execute('SELECT resource_id FROM resources WHERE depot=? AND archive=?',
            (probe['depot'],probe['archive'])).fetchone()[0]
        self.db.execute('INSERT INTO coverage_boundaries VALUES(?,?,NULL,NULL,NULL,?,?)',
            ('DECODE-Q303-CONCERT',resource,'OPAQUE_SCENE_DECODE_HOLD',encode(probe)))


def main():
    if INDEX.exists():
        raise SystemExit('Use a fresh successor index directory')
    prepared = read(TASK/'evidence_01/prepared.json')
    assert sha(prepared['parent']['path']) == prepared['parent']['sha256']
    parent_db=sqlite3.connect(Path(prepared['parent']['path']).as_uri()+'?mode=ro',uri=True)
    reused=Counter()
    for row in prepared['resources']:
        assert sha(row['raw']) == row['sha256'] and sha(row['json']) == row['json_sha256']
        existing=parent_db.execute('SELECT raw_sha256,kind FROM resources WHERE resource_id=?',(row['resource_id'],)).fetchone()
        if existing:
            assert existing[0]==row['sha256']
            assert ((existing[1]=='SCENE' and row['root_type']=='scnSceneResource') or
                    (existing[1]=='ENGLISH_SUBTITLES' and 'UNNAMED_ENGLISH_TEXT' in row['reasons']))
            reused[existing[1]]+=1
    parent_db.close()
    assert dict(reused)=={'SCENE':26,'ENGLISH_SUBTITLES':12},reused
    print('Preflight: reuse 26 scene and 12 subtitle providers; add 438 resources',flush=True)
    INDEX.mkdir()
    database = INDEX/'dialogue.partial.sqlite3'
    shutil.copyfile(prepared['parent']['path'],database)
    assert sha(database) == prepared['parent']['sha256']
    connection = sqlite3.connect(database)
    connection.executescript(SCHEMA)
    # Retained tables are append-only. The only updated dialogue columns are
    # searchable text and its source qualification, never source event records.
    retained = {'resources','roots','actors','lines','nodes','edges','entries','events','choices','localization','issues','script_calls','source_references'}
    def authorizer(action, first, second, database_name, trigger):
        if action in {sqlite3.SQLITE_UPDATE,sqlite3.SQLITE_DELETE} and first in retained:
            return sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_UPDATE and first=='search_items' and second not in {'text','text_source'}:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    connection.set_authorizer(authorizer)
    builder = Builder(connection,prepared)
    subtitle_ids = set()
    for i,row in enumerate(prepared['resources'],1):
        document = read(row['json'])
        added=builder.add_resource(row)
        if 'UNNAMED_ENGLISH_TEXT' in row['reasons']:
            if added:
                builder.subtitles(row,document)
            subtitle_ids.update(str(obj['stringId']) for _,obj in walk(document) if obj.get('$type')=='localizationPersistenceSubtitleEntry')
        elif 'VOICESET_DISPATCH_GRAPH' in row['reasons']:
            builder.phase(row,document)
        else:
            builder.support(row,document)
        if i%40==0:
            print('Indexed supplemental providers',i,flush=True)
    changes = builder.qualify_text(sorted(subtitle_ids))
    builder.link_dispatches()
    builder.references_and_boundaries()
    connection.set_authorizer(None)
    connection.execute("INSERT INTO search_fts(search_fts) VALUES('rebuild')")
    parent_status = dict(connection.execute('SELECT key,value FROM metadata'))
    connection.execute("DELETE FROM metadata WHERE key='verified_utc'")
    connection.execute("UPDATE metadata SET value='INDEXED_PENDING_VERIFICATION' WHERE key='status'")
    for key,value in {'coverage_successor_schema':'1','coverage_parent_sha256':prepared['parent']['sha256'],
        'coverage_parent_verified_utc':parent_status.get('verified_utc',''),
        'coverage_builder_sha256':sha(Path(__file__)),'coverage_source_preparation_sha256':sha(TASK/'evidence_01/prepared.json')}.items():
        connection.execute('INSERT INTO metadata VALUES(?,?)',(key,value))
    connection.commit()
    counts = {name:connection.execute('SELECT count(*) FROM "'+name+'"').fetchone()[0]
              for (name,) in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'search_fts%' AND name NOT LIKE 'sqlite_%'")}
    connection.close()
    write(INDEX/'index_build.json',{'status':'PENDING_VERIFICATION','database':str(database),
        'parent':prepared['parent'],'additional_counts':dict(builder.counts),'counts':counts,
        'qualified_source_scopes':builder.source_scope_changes,'text_qualification_changes':changes,
        'game_writes':0,'save_writes':0,'parent_index_writes':0,'step3_started':False})
    print(encode({'status':'PENDING_VERIFICATION','additional_counts':dict(builder.counts),
        'text_items_requalified':len(changes),'counts':counts}))


if __name__=='__main__':
    main()
