"""Edit Johnny's presentation and the approved scene paths in Batch 5."""

from edit_scenes import BatchScene
from resources import stamp, value
from scenes import SceneEdit


def reachable(nodes, entries):
    """Follow activation edges. Cancellation inputs do not activate a node."""
    seen = set()
    pending = list(entries)
    while pending:
        node_id = pending.pop()
        if node_id in seen:
            continue
        seen.add(node_id)
        for socket in nodes[node_id]['outputSockets']:
            for dest in socket['destinations']:
                target = dest['nodeId']['id']
                name, ordinal = stamp(dest['isockStamp'])
                node = nodes[target]
                mappings = node.get('isockMappings', [])
                if name == 1026 or (ordinal < len(mappings)
                                    and value(mappings[ordinal]) == 'CutDestination'):
                    continue
                if node['$type'] in ('scnChoiceNode', 'scnSectionNode') and (name, ordinal) != (0, 0):
                    continue
                pending.append(target)
    return seen


class ReviewedScene(BatchScene):
    def __init__(self, doc, filename, entries):
        # The prologue cat's separate cast entry uses the same scene as Backs.
        SceneEdit.__init__(self, doc)
        self.filename = filename
        self.cast = [a for h in self.r.root['actors']
                     if (a := self.r.d(h))['actorName'].casefold() in ('johnny', 'silverhand')]
        assert len(self.cast) == 1, filename
        self.actor_ids = {a['actorId']['id'] for a in self.cast}
        self.names = {value(a['spawnDespawnParams']['dynamicEntityUniqueName']) for a in self.cast} - {'None'}
        self.props = {}
        self.prop_performers = set()
        starts = {value(p['name']): p['nodeId']['id'] for p in self.r.root['entryPoints']}
        self.starts = [starts[entry] for entry in entries]
        self.scope = reachable(self.nodes, self.starts)

    def remove_presentation(self, selected):
        actor, = self.cast
        assert actor['acquisitionPlan'] in ('spawnDespawn', 'spawnSet', 'findInContext', 'community')
        actor['acquisitionPlan'] = 'spawnDespawn'
        for key in ('isEnabled', 'alwaysSpawned', 'spawnOnStart', 'keepAlive',
                    'findInWorld', 'prefetchAppearance'):
            actor['spawnDespawnParams'][key] = 0
        assert all(not self.targeted(self.r.clean(self.r.d(h))) for h in self.r.root.get('props', []))
        found = set()
        for node_id in sorted(self.scope):
            node = self.nodes[node_id]
            if 'actorBehaviors' in node:
                node['actorBehaviors'] = [a for a in node['actorBehaviors']
                                          if a['actorId']['id'] not in self.actor_ids]
            if 'events' not in node:
                continue
            kept = []
            for h in node['events']:
                event = self.r.d(h)
                event_id = str(event['id']['id'])
                kind = event['$type']
                if event_id in selected:
                    line = selected[event_id]
                    assert kind == 'scnDialogLineEvent' and node_id == int(line['node_id'])
                    found.add(event_id)
                    self.cut_events.append({'id': event_id, 'node': node_id, 'kind': kind,
                                            'speaker': line['speaker']})
                elif kind != 'scnDialogLineEvent' and self.targeted(self.r.clean(event)):
                    self.cut_events.append({'id': event_id, 'node': node_id, 'kind': kind})
                else:
                    kept.append(h)
            node['events'] = kept
        assert found == set(selected), (self.filename, set(selected) - found)


def backs(s):
    s.remove_menu(8, [2, 258, 514])
    s.set_out(1, [(4,)])
    # Keep the meds/completed-exchange XOR and its native gunshot signal.
    s.set_out(4, [(117, 1), (17,)])
    # The outside-room trigger formerly cancelled the removed conversation.
    assert s.nodes[214]['$type'] == 'scnHubNode'
    assert all(stamp(d['isockStamp']) == (1, 0) for socket in s.nodes[214]['outputSockets']
               for d in socket['destinations'])
    s.set_out(183, [(205, 1)])
    for section in (4, 17, 195):
        s.shorten(section)


def pure_exchange(s):
    s.set_out(1, [(2,)])


def family_matters(s):
    for section in (10, 17, 20, 24, 30, 36, 41):
        s.shorten(section)


def freedom(s):
    # Retain the Max check, carry fact and both extraction callbacks. V's
    # parallel line must finish before the terminating callback can fire.
    s.set_out(1308, [(353,)])
    s.shorten(353)
    floor = s.nodes[482]['sectionDuration']['stu']
    assert floor == 2232
    duration = max(floor, s.timing[353]['after_ms'])
    s.nodes[353]['sectionDuration']['stu'] = duration
    s.timing[353].update(after_ms=duration, parallel_v_floor_ms=floor)
    s.timer(889)


def greed(s):
    # The doorway trigger and the authored optional-code increment stay paired.
    s.set_out(4, [(141, 1)])
    for section in (4, 12, 17, 22, 27, 41, 49, 57, 63):
        s.shorten(section)


def last_login(s):
    s.shorten(29)
    # Let the body focus cleanup run before the original terminating exit.
    s.timer(39)


def nasty(s):
    # The payment continues to write its native fact. Only the presentation
    # listener is disconnected, along with its camera and workspot chain.
    s.skip(293, [])


def playing(s):
    s.set_out(1, [(2,)])
    s.set_out(16, [(19,)])


WIRES = {
    'sts_wat_kab_03_johnny.scene': backs,
    'sts_std_rcr_02_johnny.scene': pure_exchange,
    'sts_wbr_hil_06_johnny.scene': pure_exchange,
    'sts_std_rcr_05_clues.scene': family_matters,
    'sts_hey_gle_04_johnny.scene': pure_exchange,
    'sts_wat_nid_12_max_jones.scene': freedom,
    'sts_wbr_jpn_12_silverhand.scene': greed,
    'sts_wat_kab_05_johnny.scene': last_login,
    'sts_std_arr_06_scn.scene': nasty,
    'sts_wat_lch_05_johnny.scene': playing,
}


def edit_scene(doc, filename, entries, selected):
    s = ReviewedScene(doc, filename, entries)
    s.remove_presentation(selected)
    WIRES[filename](s)
    s.skip_actor_nodes(except_nodes=set(s.nodes) - s.scope)
    edited, changes = s.finish()
    return edited, {**changes, 'bound_entries': entries, 'original_scope': sorted(s.scope)}
