"""Apply the reviewed Batch 6 selections to their connected scene entries."""

from copy import deepcopy
import sys

from baseline import PRE
sys.path.extend(str(PRE / p) for p in ('johnny_batch4_jb3', 'johnny_batch5_source'))
from edit_scenes import BatchScene
from resources import Resource, actor_reference, stamp, value, walk
from scene_edits import reachable
from scenes import SceneEdit
from common import fnv


class Batch6Scene(BatchScene):
    def __init__(self, doc, review):
        SceneEdit.__init__(self, doc)
        self.filename = review['depot'].rsplit('\\', 1)[-1]
        self.cast = [a for h in self.r.root['actors'] if
                     (a := self.r.d(h))['actorId']['id'] == review['actor_id']]
        assert len(self.cast) == 1 and self.cast[0]['actorName'] == review['actor_name']
        self.actor_ids = {review['actor_id']}
        self.names = {review['dynamic_entity_name']} - {'None'}
        self.props = {}
        self.prop_performers = set()
        starts = {value(p['name']): p['nodeId']['id'] for p in self.r.root['entryPoints']}
        self.starts = [starts[e] for e in review['bound_entries']]
        self.scope = reachable(self.nodes, self.starts)

    def cut_presentation(self, selected):
        actor, = self.cast
        assert actor['acquisitionPlan'] in ('spawnDespawn', 'spawnSet', 'findInContext', 'community')
        actor['acquisitionPlan'] = 'spawnDespawn'
        for key in ('isEnabled', 'alwaysSpawned', 'spawnOnStart', 'keepAlive',
                    'findInWorld', 'prefetchAppearance'):
            actor['spawnDespawnParams'][key] = 0
        props = []
        for h in self.r.root.get('props', []):
            p = self.r.d(h)
            dogtags = self.filename == 'sts_ep1_03_wagner_standoff.scene' and p['propName'] == 'dogtags_johnny'
            if dogtags or actor_reference(self.r.clean(p), self.actor_ids):
                self.props[p['propId']['id']] = p['propName']
            else:
                props.append(h)
        if 'props' in self.r.root:
            self.r.root['props'] = props
        self.prop_performers = {(i << 8) | 2 for i in self.props}

        found = set()
        for i in sorted(self.scope):
            n = self.nodes[i]
            if 'actorBehaviors' in n:
                n['actorBehaviors'] = [b for b in n['actorBehaviors'] if b['actorId']['id'] not in self.actor_ids]
            if 'events' not in n:
                continue
            kept = []
            for ordinal, h in enumerate(n['events']):
                e = self.r.d(h)
                eid = str(e['id']['id'])
                kind = e['$type']
                if eid in selected:
                    row = selected[eid]
                    assert kind == 'scnDialogLineEvent' and i == int(row['node_id'])
                    assert ordinal == row['event_ordinal'] and str(e['startTime']) == row['start_time']
                    self.cut_events.append({'id': eid, 'node': i, 'kind': kind, 'speaker': row['speaker_role']})
                    found.add(eid)
                elif kind != 'scnDialogLineEvent' and self.targeted(self.r.clean(e)):
                    self.cut_events.append({'id': eid, 'node': i, 'kind': kind})
                else:
                    kept.append(h)
            n['events'] = kept
        assert found == set(selected), (self.filename, set(selected) - found)

    def skip_presentation_nodes(self):
        kinds = {'questPauseConditionNodeDefinition', 'questSpawnManagerNodeDefinition',
                 'questUseWorkspotNodeDefinition', 'questSceneManagerNodeDefinition',
                 'questUIManagerNodeDefinition', 'questVoicesetManagerNodeDefinition',
                 'questVehicleNodeDefinition', 'questTeleportPuppetNodeDefinition',
                 'questCharacterManagerNodeDefinition', 'questFXManagerNodeDefinition',
                 'questEventManagerNodeDefinition', 'questEquipItemNodeDefinition',
                 'questLookAtDrivenTurnsNode'}
        for i in sorted(self.scope):
            n = self.nodes[i]
            if i in self.bypass or n['$type'] != 'scnQuestNode':
                continue
            q = self.r.clean(self.q(i))
            if not self.targeted(q):
                continue
            kind = q['$type']
            assert kind in kinds, (self.filename, i, kind)
            if kind == 'questSpawnManagerNodeDefinition':
                assert all(self.targeted(a) for a in q['actions']), (self.filename, i, q)
            assert (q.get('condition') or {}).get('$type') != 'questLogicalCondition', (self.filename, i)
            self.skip(i)

    def screen_choice(self, i):
        n = self.nodes[i]
        assert n['mode'] == 'attachToActor' and n['ataParams']['actorId']['id'] in self.actor_ids
        n['mode'] = 'attachToScreen'
        n['ataParams']['actorId']['id'] = 4294967295
        reminder = self.r.d(n['reminderParams'])
        assert reminder['reminderActor']['id'] in self.actor_ids and not reminder['useCustomReminder']
        reminder['reminderActor']['id'] = 4294967295

    def option_label(self, i):
        store = self.r.d(self.r.root['screenplayStore'])
        option, = [o for o in store['options'] if o['itemId']['id'] == i]
        return option['locstringId']

    def use_stand_label(self, donor):
        ruid = '1985010349784772608'  # Restaurant's physical [Stand].
        label = self.option_label(4866)
        label['ruid'] = ruid
        target = self.r.d(self.r.root['locStore'])
        source = donor.d(donor.root['locStore'])
        variants = [d for d in source['vdEntries'] if str(d['locstringId']['ruid']) == ruid]
        assert {d['localeId'] for d in variants} == {'db_db', 'en_us', 'pl_pl'}
        assert not any(str(d['locstringId']['ruid']) == ruid for d in target['vdEntries'])
        for descriptor in variants:
            copy = deepcopy(descriptor)
            payload = deepcopy(source['vpEntries'][descriptor['vpeIndex']])
            copy['vpeIndex'] = len(target['vpEntries'])
            target['vpEntries'].append(payload)
            target['vdEntries'].append(copy)
        assert {source['vpEntries'][d['vpeIndex']]['content'] for d in variants
                if d['localeId'] == 'en_us'} == {'[Stand]'}

    def use_regina_label(self):
        store = self.r.d(self.r.root['locStore'])
        label = self.option_label(6658)
        old = label['ruid']
        key = 'towercontinued\\johnny_batch6\\consider_regina'
        ruid = fnv(key)
        assert not any(str(d['locstringId']['ruid']) == ruid for d in store['vdEntries'])
        label['ruid'] = ruid
        text = {'db_db': '', 'en_us': '[Consider calling Regina]', 'pl_pl': '[Rozważ telefon do Reginy]'}
        variants = [d for d in store['vdEntries'] if d['locstringId']['ruid'] == old]
        assert len(variants) == 3 and {d['localeId'] for d in variants} == text.keys()
        for descriptor in variants:
            variant = fnv(key + '\\' + descriptor['localeId'])
            copy = deepcopy(descriptor)
            payload = deepcopy(store['vpEntries'][descriptor['vpeIndex']])
            copy['locstringId']['ruid'] = ruid
            copy['variantId']['ruid'] = payload['variantId']['ruid'] = variant
            payload['content'] = text[descriptor['localeId']]
            copy['vpeIndex'] = len(store['vpEntries'])
            store['vpEntries'].append(payload)
            store['vdEntries'].append(copy)

    def keep_cancel_ports_inactive(self):
        for node in self.nodes.values():
            for socket in node['outputSockets']:
                socket['destinations'] = [
                    dest for dest in socket['destinations']
                    if not (dest['nodeId']['id'] in self.bypass
                            and self.nodes[dest['nodeId']['id']]['$type'] in ('scnChoiceNode', 'scnSectionNode')
                            and stamp(dest['isockStamp']) != (0, 0))
                ]


def restaurant(s):
    # All three spoken responses rejoin at the same hub and arm the same
    # camera state. The real stand/sit and Rachel offer menus remain.
    s.skip(709, [(5162, 1), (2233,)])
    s.skip(825, [(858,)])
    for i in (5151, 5152, 5184, 5195):
        # The alternating look-at conditions only animate the absent actor.
        # Bypassing them would turn their alternating waits into a busy loop.
        s.skip(i, [])


def delamain_core(s):
    # Both callbacks in 1289 remain, including the actual skill conditions
    # and the route that lets the player choose what to do to the core.
    s.skip(1283, [(1289,)])


def bomb(s):
    # Signal the completed swap first. The V unmount and gameplay return
    # still run in the original exit section, with its original timing.
    s.set_out(51, [(59, 1)])
    s.set_out(59, [(2,), (201,)])
    s.skip(232, [])


def auction(s, donor):
    s.remove_option(913, 1, 5122)
    s.screen_choice(913)
    s.use_stand_label(donor)
    # The other authored stand choice also disables the stool's collision.
    s.set_out(917, [(2626, 1), (857,)], port=(2, 0))
    s.skip(2567, [(1923, 1)])


def rinder(s):
    s.screen_choice(2466)
    s.use_regina_label()


def coaster(s):
    # This repeats Johnny's two look-at events until the ride owner cuts it.
    # Keep the cart and V's actions on their own authored timing.
    assert s.nodes[917]['events'] == []
    s.skip(915, [])


def edit_scene(doc, review, stand_donor):
    s = Batch6Scene(doc, review)
    cuts = {e['event_id']: e for e in review['speech_cuts']}
    assert len(cuts) == len(review['speech_cuts'])
    s.cut_presentation(cuts)
    for menu in review['menu_edits']:
        if menu['action'] == 'remove_johnny_exchange':
            s.remove_menu(int(menu['node_id']), [int(o['option_id']) for o in menu['options']])
    for row in review['bark_dispatch_cuts']:
        s.mute_dispatch(int(row['node_id']), row['voiceset_name'])
    rewires = {
        'sq023_07_restaurant.scene': restaurant, 'sq025_10_resolution.scene': delamain_core,
        'sts_ep1_07_bomb_interaction.scene': bomb, 'sts_ep1_03_wagner_standoff.scene': rinder,
        'mq006_02_finale.scene': coaster,
        'sts_ep1_13_v_auction.scene': lambda s: auction(s, stand_donor),
        'sts_cct_dtn_05_johnny.scene': lambda s: s.set_out(1, [(2,)]),
        'sts_pac_cvi_02_johnny.scene': lambda s: s.set_out(1, [(2,)]),
    }
    if s.filename in rewires:
        rewires[s.filename](s)
    fixed_timing = {442, 445} if s.filename == 'sq023_10_bd_studio.scene' else set()
    if s.filename != 'mq006_02_finale.scene':
        for i in sorted({int(e['node_id']) for e in cuts.values()} - fixed_timing):
            s.shorten(i)
    s.skip_presentation_nodes()
    s.keep_cancel_ports_inactive()
    result, evidence = s.finish()
    return result, {**evidence, 'removed_props': s.props, 'bound_entries': review['bound_entries']}
