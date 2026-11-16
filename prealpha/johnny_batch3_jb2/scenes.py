"""Author the approved dialogue cuts and their local scene continuations."""

import copy
import importlib.util

from resources import WS, Edit, Resource, actor_reference, destination, order_handles, scene_nodes, stamp, value

spec = importlib.util.spec_from_file_location(
    'jb1_scene_helpers', WS / 'prealpha/johnny_batch2_jb1/prepare.py')
jb1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jb1)

# Additional speech within the approved whole exchanges. The situational
# package/stash remarks and V's independent observations at the plaque stay.
REPLIES = {
    'mq003_pod.scene': {45: [2085301810800939032, 2085301810800939040],
                        50: [2085301810800939052, 2085301810800939060]},
    'mq010_03_columbarium.scene': {
        4: [1986798192131469320], 12: [1986798192148246540, 1986798192148246552],
        29: [1986798192148246564, 1986798192148246568],
        31: [1986798192148246572, 1986798192148246576],
    },
    'mq019_04_manager.scene': {
        171: [1984867574953070616, 1984867574953070624, 1984867574953070632],
        173: [1984867574953070640, 1984867574953070652],
    },
}


class SceneEdit(Edit):
    def __init__(self, doc):
        super().__init__(doc)
        self.nodes = scene_nodes(self.r)
        self.original_edges = {i: copy.deepcopy(n['outputSockets']) for i, n in self.nodes.items()}
        self.actor_ids = set()
        self.cut_events = []
        self.removed_options = []
        self.bypass = {}
        self.timing = {}

    def clean_presentation(self, selected):
        for h in self.r.root['actors']:
            actor = self.r.d(h)
            if 'johnny' not in actor['actorName'].lower():
                continue
            self.actor_ids.add(actor['actorId']['id'])
            assert actor['acquisitionPlan'] in ('spawnSet', 'spawnDespawn', 'findInContext')
            actor['acquisitionPlan'] = 'spawnDespawn'
            for flag in ('isEnabled', 'alwaysSpawned', 'spawnOnStart', 'keepAlive',
                         'findInWorld', 'prefetchAppearance'):
                actor['spawnDespawnParams'][flag] = 0
        assert self.actor_ids

        seen = set()
        for i, n in self.nodes.items():
            if 'actorBehaviors' in n:
                n['actorBehaviors'] = [a for a in n['actorBehaviors'] if a['actorId']['id'] not in self.actor_ids]
            if 'events' not in n:
                continue
            kept = []
            for h in n['events']:
                e = self.r.d(h)
                event_id = str(e['id']['id'])
                if event_id in selected:
                    assert e['$type'] == 'scnDialogLineEvent' and i == int(selected[event_id]['node_id'])
                    seen.add(event_id)
                    self.cut_events.append({'id': event_id, 'node': i, 'kind': e['$type'],
                                            'speaker': selected[event_id]['speaker_role']})
                elif e['$type'] != 'scnDialogLineEvent' and actor_reference(self.r.clean(e), self.actor_ids):
                    self.cut_events.append({'id': event_id, 'node': i, 'kind': e['$type']})
                else:
                    kept.append(h)
            n['events'] = kept
        assert seen == set(selected), set(selected) - seen

    def set_out(self, i, targets, port=(0, 0), create=False):
        sockets = self.nodes[i]['outputSockets']
        matches = [s for s in sockets if stamp(s['stamp']) == port]
        if not matches and create:
            matches = [{'$type': 'scnOutputSocket', 'destinations': [],
                        'stamp': {'$type': 'scnOutputSocketStamp', 'name': port[0], 'ordinal': port[1]}}]
            sockets.extend(matches)
        socket, = matches
        socket['destinations'] = [destination(*t) for t in targets]

    def clear(self, i):
        for s in self.nodes[i]['outputSockets']:
            s['destinations'] = []

    def timer(self, i, ms=50):
        q = self.r.d(self.nodes[i]['questNode'])
        assert q['$type'] == 'questPauseConditionNodeDefinition'
        q['condition'] = self.h({'$type': 'questTimeCondition', 'type': self.h({
            '$type': 'questRealtimeDelay_ConditionType', 'hours': 0, 'miliseconds': ms,
            'minutes': 0, 'seconds': 0})})

    def shorten(self, i):
        self.timing[i] = jb1.compress_section(self.nodes[i], self.r)

    def drop_actor_operations(self, forward=False):
        for i, n in self.nodes.items():
            q = self.r.d(n.get('questNode'))
            if not q or not actor_reference(self.r.clean(q), self.actor_ids):
                continue
            assert q['$type'] in {
                'questSpawnManagerNodeDefinition', 'questPauseConditionNodeDefinition',
                'questUseWorkspotNodeDefinition', 'questTeleportPuppetNodeDefinition',
                'questCharacterManagerNodeDefinition', 'questEventManagerNodeDefinition',
                'questConditionNodeDefinition',
            }, (i, q['$type'])
            outs = [s['destinations'] for s in n['outputSockets'] if s['destinations']]
            if forward:
                assert len(outs) <= 1, (i, outs)
            self.bypass[i] = copy.deepcopy(outs[0]) if forward and outs else []

    def remove_option(self, node, ordinal, option_id):
        n = self.nodes[node]
        assert n['$type'] == 'scnChoiceNode' and ordinal == len(n['options']) - 1
        assert n['options'][ordinal]['screenplayOptionId']['id'] == option_id
        option = n['options'].pop(ordinal)
        socket, = [s for s in n['outputSockets'] if stamp(s['stamp']) == (0, ordinal)]
        n['outputSockets'].remove(socket)
        self.removed_options.append({'node': node, 'ordinal': ordinal, 'option': option, 'socket': socket})

    def finish(self):
        def resolve(dest, seen=frozenset()):
            i = dest['nodeId']['id']
            if i not in self.bypass:
                return [dest]
            assert i not in seen, i
            node = self.nodes[i]
            name, ordinal = stamp(dest['isockStamp'])
            mappings = node.get('isockMappings', [])
            if name == 1026 or (ordinal < len(mappings) and value(mappings[ordinal]) == 'CutDestination'):
                return []
            return [end for next_dest in self.bypass[i] for end in resolve(next_dest, seen | {i})]

        for n in self.nodes.values():
            for socket in n['outputSockets']:
                result = []
                for dest in socket['destinations']:
                    for end in resolve(dest):
                        if end not in result:
                            result.append(copy.deepcopy(end))
                socket['destinations'] = result
        jb1.api.cleanup_event_ids(self.doc, {e['id'] for e in self.cut_events})
        edited = order_handles(self.doc, self.r.handles)
        return edited, {
            'actor_ids': sorted(self.actor_ids), 'events_removed': self.cut_events,
            'options_removed': self.removed_options, 'duration_changes': self.timing,
            'bypassed_actor_nodes': sorted(self.bypass),
            'edge_changes': [
                {'node': i, 'before': old, 'after': self.nodes[i]['outputSockets']}
                for i, old in self.original_edges.items() if old != self.nodes[i]['outputSockets']
            ],
        }


def pod(s):
    s.clear(20)
    s.set_out(20, [(40,), (119, 1)], create=True)
    s.timer(119)
    s.set_out(119, [(68,)])
    s.bypass[47] = []
    s.shorten(20)


def columbarium(s):
    # The two captions are V's reactions to the plaque. Both real choices
    # converge on V's realization and the original discovery and cleanup exits.
    for start in (248, 484):
        s.clear(start)
    for menu in (7, 28):
        s.bypass[menu] = []
    s.set_out(402, [(44, 1)])
    s.set_out(43, [(39,)], create=True)
    s.set_out(39, [], port=(1, 0))
    s.set_out(39, [(9,)], port=(0, 0))
    s.clear(4)
    s.set_out(4, [(9,)], create=True)
    s.set_out(9, [(143,)])
    s.timer(52)
    s.set_out(52, [(54,)])
    for section in (4, 9):
        s.shorten(section)


def stash(s):
    s.set_out(123, [(204, 1), (21, 1)])
    # Preserve both the genuine item-grant chain and V's independent reaction.
    s.set_out(14, [(287, 0)])
    s.set_out(20, [(287, 1)])
    s.set_out(287, [(163, 1)])
    s.set_out(163, [(209, 1)])
    s.set_out(209, [(2,), (119, 1)])
    s.timer(119)
    s.set_out(119, [(222,)])


def manager(s):
    s.set_out(200, [(202,)])


def hook(s):
    s.remove_option(134, 0, 2306)
    s.bypass[134] = []
    s.clear(143)
    s.set_out(1, [(188,)])
    s.set_out(82, [(103, 1)])


def maelstrom(s):
    s.set_out(463, [(231, 1)])
    s.set_out(17, [(154,), (158,), (197, 1), (217,)])
    # 351 only re-enabled scanning on Johnny. Retain the monk's cleanup wait.
    s.set_out(231, [(49,), (454, 1)])


def epilogue(s):
    s.remove_option(61, 3, 2306)


def car(s):
    s.set_out(1, [(21, 1, 666)])
    s.set_out(21, [(7,), (15, 1)], port=(666, 0))
    s.timer(15)
    s.set_out(15, [(2,)])


WIRES = {
    'mq003_pod.scene': pod,
    'mq010_03_columbarium.scene': columbarium,
    'mq015_04_stash.scene': stash,
    'mq019_04_manager.scene': manager,
    'mq032_01_hook.scene': hook,
    'mq032_02_maelstrom.scene': maelstrom,
    'mq032_03_epilogue.scene': epilogue,
    'mq050_johnny_start.scene': car,
}


def prepare_scene(doc, basename, selected):
    s = SceneEdit(doc)
    cuts = {str(e['event_id']): e for e in selected}
    for node, ids in REPLIES.get(basename, {}).items():
        for event_id in ids:
            assert str(event_id) not in cuts
            cuts[str(event_id)] = {'node_id': node, 'speaker_role': 'V'}
    assert len({e['event_id'] for e in selected}) == len(selected)
    s.clean_presentation(cuts)
    if basename in WIRES:
        WIRES[basename](s)
    s.drop_actor_operations(forward=basename == 'mq030_01_melisa.scene')
    edited, evidence = s.finish()
    r = Resource(edited)
    graph = r.normalize()['graphs']['scene']
    assert not r.errors, r.errors
    for i in graph['reachable']:
        node = graph['nodes'][i]
        assert not actor_reference(node['payload'].get('questNode'), s.actor_ids), (basename, i)
        if node['type'] == 'scnChoiceNode':
            assert not actor_reference(node['payload'], s.actor_ids), (basename, i)
    return edited, evidence
