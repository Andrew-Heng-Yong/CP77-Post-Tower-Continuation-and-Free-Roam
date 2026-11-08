"""Read phase graphs, retaining null and cross-graph socket boundaries."""

from collections import defaultdict, deque

from common import scalar, walk


class PhaseSource:
    def __init__(self, document):
        self.document = document
        self.handles = {}
        for path, obj in walk(document):
            if 'HandleId' in obj and 'Data' in obj:
                key = str(obj['HandleId'])
                if key in self.handles and self.handles[key] != obj['Data']:
                    raise ValueError('Conflicting serialized handle ' + key)
                self.handles[key] = obj['Data']
        self.graphs = []
        self.port_owners = defaultdict(list)
        root = document['Data']['RootChunk']
        self._collect(root.get('graph'), 'root', 'root', None, None,
                      root.get('phasePrefabs', []))
        if 'sceneGraph' in root:
            self._scene(root)
        for ordinal, embedded in enumerate(document['Data'].get('EmbeddedFiles', [])):
            content = embedded.get('Content', {})
            if 'graph' in content:
                name = str(scalar(embedded.get('FileName', '')))
                self._collect(content['graph'], 'embedded/' + name + '/root',
                              'embedded/' + str(ordinal), None, None,
                              content.get('phasePrefabs', []))
        for graph in self.graphs:
            if not graph.get('is_scene'):
                self._connections(graph)

    def _scene(self, root):
        source = self.deref(root['sceneGraph'])
        nodes = {}
        graph = {'path':'scene','subresource':'root','parent_graph':None,'parent_node':None,
                 'root_prefabs':[],'nodes':nodes,'entries':[], 'connections':[],
                 'is_scene':True,'edges':[]}
        self.graphs.append(graph)
        for handle in source.get('graph',[]):
            node = self.deref(handle)
            key = str(scalar(node['nodeId']))
            if key in nodes:
                raise ValueError('Duplicate scene node ' + key)
            nodes[key] = {'source':node,'payload':self.clean(node),'ports':[]}
            quest = self.deref(node.get('questNode'))
            if isinstance(quest,dict) and quest.get('phaseGraph') is not None:
                self._collect(quest['phaseGraph'],'scene/'+key,'root','scene',key,[])
            for socket in node.get('outputSockets',[]):
                stamp = socket.get('stamp',{})
                output = str(stamp.get('name',0))+':'+str(stamp.get('ordinal',0))
                for end in socket.get('destinations',[]):
                    target = end.get('isockStamp',{})
                    graph['edges'].append((key,output,str(scalar(end['nodeId'])),
                        str(target.get('name',0))+':'+str(target.get('ordinal',0))))
        graph['entries'] = [(str(scalar(e['name'])),str(scalar(e['nodeId']))) for e in root.get('entryPoints',[])]
        self._reachability(graph)

    def deref(self, value):
        if not isinstance(value, dict):
            return value
        if 'HandleId' in value:
            return value['Data']
        if 'HandleRefId' in value:
            key = str(value['HandleRefId'])
            if key in {'0', '-1'} and key not in self.handles:
                return None
            if key not in self.handles:
                raise ValueError('Unresolved serialized handle ' + key)
            return self.handles[key]
        return value

    @staticmethod
    def handle(value):
        if not isinstance(value, dict):
            return None
        key = value.get('HandleId', value.get('HandleRefId'))
        return str(key) if key is not None else None

    def clean(self, value, active=frozenset()):
        if isinstance(value, dict):
            if 'HandleId' in value or 'HandleRefId' in value:
                key = self.handle(value)
                if key in active:
                    return {'$cycle': key}
                return self.clean(self.deref(value), active | {key})
            return {k: self.clean(v, active) for k,v in value.items()
                    if k not in {'sockets','connections','phaseGraph','graph','debugSymbols'}}
        if isinstance(value, list):
            return [self.clean(v, active) for v in value]
        return value

    def _collect(self, handle, path, subresource, parent_graph, parent_node, prefabs):
        source = self.deref(handle)
        if source is None:
            return
        if not isinstance(source, dict) or 'nodes' not in source:
            raise ValueError('Unsupported phase graph ' + path)
        nodes = {}
        graph = {'path': path, 'subresource': subresource,
                 'parent_graph': parent_graph, 'parent_node': parent_node,
                 'root_prefabs': prefabs, 'nodes': nodes, 'entries': [], 'connections': []}
        self.graphs.append(graph)
        for wrapped in source['nodes']:
            node = self.deref(wrapped)
            key = str(node['id'])
            if key in nodes:
                raise ValueError('Duplicate phase node ' + path + '/' + key)
            nodes[key] = {'source': node, 'payload': self.clean(node), 'ports': []}
            if node['$type'] in {'questInputNodeDefinition','questStartNodeDefinition'}:
                graph['entries'].append((str(scalar(node.get('socketName',''))), key))
            for ordinal, socket_handle in enumerate(node.get('sockets', [])):
                socket = self.deref(socket_handle)
                port = {'graph': path, 'node': key, 'ordinal': ordinal,
                        'name': str(scalar(socket.get('name',''))),
                        'type': socket.get('type'), 'handle': self.handle(socket_handle),
                        'source': socket}
                nodes[key]['ports'].append(port)
                owner = {k:v for k,v in port.items() if k != 'source'}
                if owner not in self.port_owners[port['handle']]:
                    self.port_owners[port['handle']].append(owner)
            if node.get('phaseGraph') is not None:
                self._collect(node['phaseGraph'], path + '/' + key, subresource,
                              path, key, prefabs)

    def endpoint(self, handle):
        if handle is None:
            return {'status': 'NULL_SOURCE_ENDPOINT', 'handle': None, 'owners': []}
        key = self.handle(handle)
        owners = self.port_owners.get(key, [])
        status = ('LOCAL_OR_CROSS_GRAPH_SOCKET' if len(owners) == 1 else
                  'AMBIGUOUS_SOCKET_OWNER' if owners else 'UNLISTED_SOURCE_SOCKET')
        return {'status': status, 'handle': key, 'owners': owners,
                'serialized_socket': self.deref(handle) if not owners else None}

    def _connections(self, graph):
        seen = set()
        for node in graph['nodes'].values():
            for port in node['ports']:
                for handle in port['source'].get('connections', []):
                    key = self.handle(handle)
                    if key in seen:
                        continue
                    seen.add(key)
                    connection = self.deref(handle)
                    source = self.endpoint(connection.get('source'))
                    target = self.endpoint(connection.get('destination'))
                    owners = source['owners'], target['owners']
                    local = all(len(part) == 1 and part[0]['graph'] == graph['path'] for part in owners)
                    graph['connections'].append({'handle': key,
                        'source': source, 'destination': target,
                        'classification': 'LOCAL_EDGE' if local else 'SOURCE_INTERFACE_BOUNDARY'})
        graph['edges'] = []
        for connection in graph['connections']:
            if connection['classification'] != 'LOCAL_EDGE':
                continue
            start = connection['source']['owners'][0]
            end = connection['destination']['owners'][0]
            edge = (start['node'], start['name'], end['node'], end['name'])
            graph['edges'].append(edge)
        self._reachability(graph)

    @staticmethod
    def _reachability(graph):
        adjacency = defaultdict(list)
        for start,output,end,input_name in graph['edges']:
            if output!='CutSource' and input_name!='CutDestination':
                adjacency[start].append(end)
        graph['entry_names'] = defaultdict(set)
        for name, seed in graph['entries']:
            seen = {seed}
            todo = [seed]
            while todo:
                for target in adjacency[todo.pop()]:
                    if target not in seen:
                        seen.add(target)
                        todo.append(target)
            for node in seen:
                graph['entry_names'][node].add(name)
        graph['reachable'] = set(graph['entry_names'])

    def dispatches(self):
        for graph in self.graphs:
            for key, node in graph['nodes'].items():
                operations = [(path,obj) for path,obj in walk(node['payload'])
                              if obj.get('$type') == 'questPlayVoiceset_NodeType']
                for operation, (source_path, obj) in enumerate(operations):
                    for ordinal, param in enumerate(obj.get('params', [])):
                        yield graph, key, operation, ordinal, source_path, param
