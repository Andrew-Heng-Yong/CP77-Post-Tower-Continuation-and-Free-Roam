"""Private scene edits for the ten reviewed jobs."""

from copy import deepcopy

from resources import Resource, actor_reference, destination, value, walk
from scenes import SceneEdit


class BatchScene(SceneEdit):
    def __init__(self, doc, filename):
        super().__init__(doc)
        self.filename = filename
        self.cast = [a for h in self.r.root['actors'] if
                     'johnny' in (a := self.r.d(h))['actorName'].lower()
                     or (filename == 'sts_bls_ina_03_interactions.scene' and a['actorName'] == 'JS')]
        assert self.cast
        self.actor_ids = {a['actorId']['id'] for a in self.cast}
        self.names = {value(a['spawnDespawnParams']['dynamicEntityUniqueName']) for a in self.cast}
        self.names.discard('None')
        self.props = {}

    def targeted(self, payload):
        if actor_reference(payload, self.actor_ids):
            return True
        for item in walk(payload):
            if item.get('$type') == 'gameEntityReference' and value(
                    item['dynamicEntityUniqueName']) in self.names:
                return True
            if item.get('$type') == 'scnPropId' and item['id'] in self.props:
                return True
            if item.get('$type') == 'scnPerformerId' and item['id'] in self.prop_performers:
                return True
        return False

    def remove_presentation(self, selected):
        for a in self.cast:
            assert a['acquisitionPlan'] in ('spawnDespawn', 'spawnSet', 'findInContext', 'community')
            a['acquisitionPlan'] = 'spawnDespawn'
            for key in ('isEnabled', 'alwaysSpawned', 'spawnOnStart', 'keepAlive',
                        'findInWorld', 'prefetchAppearance'):
                a['spawnDespawnParams'][key] = 0
        keep = []
        for h in self.r.root.get('props', []):
            p = self.r.d(h)
            item = p['propName'].lower()
            if actor_reference(self.r.clean(p), self.actor_ids) or item == 'johnny_glasses':
                self.props[p['propId']['id']] = p['propName']
            else:
                keep.append(h)
        if 'props' in self.r.root:
            self.r.root['props'] = keep
        self.prop_performers = {(i << 8) | 2 for i in self.props}
        found = set()
        for i, node in self.nodes.items():
            if 'actorBehaviors' in node:
                node['actorBehaviors'] = [a for a in node['actorBehaviors']
                                          if a['actorId']['id'] not in self.actor_ids]
            if 'events' not in node:
                continue
            kept = []
            for h in node['events']:
                e = self.r.d(h)
                event_id = str(e['id']['id'])
                if event_id in selected:
                    line = selected[event_id]
                    assert e['$type'] == 'scnDialogLineEvent' and i == int(line['node_id'])
                    found.add(event_id)
                    self.cut_events.append({'id': event_id, 'node': i, 'kind': e['$type'],
                                            'speaker': line['speaker']})
                elif e['$type'] != 'scnDialogLineEvent' and self.targeted(self.r.clean(e)):
                    self.cut_events.append({'id': event_id, 'node': i, 'kind': e['$type']})
                else:
                    kept.append(h)
            node['events'] = kept
        assert found == set(selected), (self.filename, set(selected) - found)

    def q(self, i):
        return self.r.d(self.nodes[i]['questNode'])

    def only_output(self, i):
        sockets = [s['destinations'] for s in self.nodes[i]['outputSockets'] if s['destinations']]
        assert len(sockets) <= 1, (self.filename, i, sockets)
        return deepcopy(sockets[0]) if sockets else []

    def skip(self, i, targets=None):
        self.bypass[i] = self.only_output(i) if targets is None else [destination(*t) for t in targets]

    def mute_dispatch(self, i, name, player=0):
        q = self.r.clean(self.q(i))
        assert q['$type'] == 'questVoicesetManagerNodeDefinition'
        param, = q['type']['params']
        assert value(param['voicesetName']) == name and param['isPlayer'] == player
        assert player or self.targeted(param)
        self.skip(i)

    def remove_menu(self, i, ids):
        n = self.nodes[i]
        assert [o['screenplayOptionId']['id'] for o in n['options']] == ids
        self.removed_options.append({'node': i, 'options': deepcopy(n['options'])})
        n['options'] = []
        self.clear(i)
        self.skip(i, [])

    def skip_actor_nodes(self, except_nodes=()):
        types = {
            'questPauseConditionNodeDefinition', 'questSpawnManagerNodeDefinition',
            'questUseWorkspotNodeDefinition', 'questSceneManagerNodeDefinition',
            'questUIManagerNodeDefinition', 'questVoicesetManagerNodeDefinition',
            'questVehicleNodeDefinition', 'questTeleportPuppetNodeDefinition',
            'questCharacterManagerNodeDefinition', 'questFXManagerNodeDefinition',
            'questEventManagerNodeDefinition',
        }
        for i, n in self.nodes.items():
            if i in except_nodes or i in self.bypass or n['$type'] != 'scnQuestNode':
                continue
            q = self.r.clean(self.q(i))
            if not self.targeted(q):
                continue
            assert q['$type'] in types, (self.filename, i, q['$type'])
            if q['$type'] == 'questSpawnManagerNodeDefinition':
                assert all(self.targeted(a) for a in q['actions']), (self.filename, i, q)
            self.skip(i)


def razor(s):
    s.skip(556, [(558,)])
    s.shorten(558)


def war_pigs(s):
    s.set_out(1, [(222, 1)])
    s.remove_menu(168, [1538, 1794])
    s.skip(367)
    for section in (212, 1006, 1028, 1041, 1055, 1069):
        s.shorten(section)


def freedom(s):
    # The pre-existing speech lock remains paired with its native release.
    for i in (6, 23, 24, 26, 28, 30):
        s.shorten(i)


def apartment(s):
    # The apartment callback still enables the native interaction objects.
    s.set_out(594, [(297,)])
    # A real wrong-plant selection still runs the authored inspection and
    # device callback, with no dependency on a finished Johnny conversation.
    for i in (525, 528, 532, 636, 639, 643):
        s.skip(i)
    s.mute_dispatch(442, 'scene_insult_var_2', player=1)
    for i in (194, 276):
        s.shorten(i)


def bunker(s):
    # Only the ordinary lab/bunker scenes run through this alias. The phase
    # disconnects the two presentation-only callers at their original gates.
    s.clear(2408)
    s.clear(4719)
    s.set_out(5746, [(5766,)])
    s.skip(2695, [])
    for i in (4271, 4275, 2872):
        s.skip(i, [])
    s.mute_dispatch(4717, 'reaction_criticizing_var_2')
    s.mute_dispatch(4840, 'reaction_criticizing_var_4')


def bunker_exploration(s):
    s.mute_dispatch(2667, 'reaction_location_bad_var_3')
    s.set_out(2661, [(2663,)])


def hands(s):
    s.set_out(251, [(253,)])


def aaron_intro(s):
    s.mute_dispatch(1633, 'reaction_general_var_6')


def aaron_alley(s):
    s.mute_dispatch(658, 'danger_var_3')
    s.set_out(361, [(52,)])
    s.clear(52)
    s.set_out(52, [(324,)], create=True)
    s.shorten(52)
    s.remove_menu(320, [1026, 1282])
    s.set_out(324, [(303, 3), (207, 1)])
    s.timer(207)
    s.set_out(207, [(214,)])


def pony(s):
    # Keep the original inventory-or-visited gate, minus the Johnny camera
    # condition. The clue and camp are still driven by their native triggers.
    q = s.q(54)
    condition = s.r.d(q['condition'])
    assert condition['operation'] == 'AND' and len(condition['conditions']) == 2
    gate, camera = condition['conditions']
    assert s.r.d(gate)['operation'] == 'OR'
    assert s.targeted(s.r.clean(camera))
    q['condition'] = gate
    s.set_out(50, [(54, 1)])
    s.mute_dispatch(12, 'Start 2')


def pony_camp(s):
    q = s.q(18)
    johnny, porsche = q['actions']
    assert s.targeted(s.r.clean(johnny))
    assert not s.targeted(s.r.clean(porsche))
    assert 'questSpawner_NodeType' in str(s.r.clean(porsche))
    q['actions'] = [porsche]
    s.set_out(24, [(12, 1)])


def flying_drugs(s):
    for section in (75, 110, 114):
        s.shorten(section)


def minefield(s):
    s.shorten(188)
    s.shorten(267)


def trevor(s):
    # The Secret Room caller still uses the untouched native depot.
    s.clear(137)
    for section in (11, 18, 26, 32):
        s.shorten(section)


def killer(s):
    s.set_out(1, [(2,)])
    s.set_out(47, [(2,)])


SCENES = {
    'mq025_08_finale.scene': razor,
    'mq041_corpo_02_confrontation.scene': war_pigs,
    'mq059_play_vos.scene': freedom,
    'mq305_03_apartment_johnny.scene': apartment,
    'mq305_04_bunker.scene': bunker,
    'mq305_04b_lab_exploration.scene': bunker_exploration,
    'mq305_05_outcome_mr_hands.scene': hands,
    'mq306_01_intro.scene': aaron_intro,
    'mq306_04a_aaron_meeting.scene': aaron_alley,
    'mws_se5_07.scene': pony,
    'mws_se5_07_camp.scene': pony_camp,
    'sts_bls_ina_03_interactions.scene': flying_drugs,
    'sts_bls_ina_07_comments.scene': minefield,
    'sts_bls_ina_08_johnny.scene': trevor,
    'sts_cct_dtn_02_johnny.scene': killer,
}


def prepare_scene(doc, filename, selected):
    s = BatchScene(doc, filename)
    s.remove_presentation(selected)
    SCENES[filename](s)
    s.skip_actor_nodes()
    edited, evidence = s.finish()
    r = Resource(edited)
    graph = r.normalize()['graphs']['scene']
    assert not r.errors, (filename, r.errors)
    for i in graph['reachable']:
        p = graph['nodes'][i]['payload']
        assert not s.targeted(p.get('questNode')), (filename, i)
        if p['$type'] == 'scnChoiceNode':
            assert not s.targeted(p), (filename, i)
        if p['$type'] == 'scnSectionNode':
            assert all(not s.targeted(event) for event in p['events']
                       if event['$type'] != 'scnDialogLineEvent'), (filename, i)
    evidence['removed_props'] = s.props
    return edited, evidence
