"""Author the post-Tower main-world dialogue changes against pinned providers."""

from pathlib import Path
import shutil
import stat
import sys


HERE = Path(__file__).resolve().parent
PRE = HERE.parent
sys.path[:0] = [str(PRE / folder) for folder in ('johnny_batch3_jb2', 'johnny_batch4_jb3')]
from edit_scenes import BatchScene
from resources import ARCHIVE, Edit, order_handles, read, sha, stamp, value, walk, write


INSTALLED = PRE / 'history_snapshot_cutoff/deployment_01/installed_manifest_01.json'
BASE = PRE / 'quest_parity_qp2/candidate_01'
AUDIT = PRE / 'johnny_main_world_audit_20261111_01'
OUT = HERE / 'authored_03'
CANDIDATE = HERE / 'candidate_02'
WELLSPRINGS = r'towercontinued\johnny_world\wellsprings_exposition.scene'
DAM = r'towercontinued\johnny_world\courier_dam.scene'
TOWER_FACT = 'PostTowerFreeRoamActive'

PINS = {
    'ma_bls_ina_se1_40_phase.questphase': '89F0E9A6AE3F619ABD75410AF677F0CE5D1F3105017BA61C2FBA41F22EA86399',
    'ma_bls_ina_se1_44_phase.questphase': '2FD3545F79449E3CA3BFCF887B485024C9681B37E68B53DEC70D94BA46FA352B',
    'ma_wat_lch_06_phase.questphase': '86721AA833945F5DA00D477F43575D5FA3286063D170E00CA3A397621980A8B7',
    'ma_wat_nid_03.questphase': 'AD58D5F6E57840B9F5FA14C57979824119273316BDE124154BE0239FAF7345B9',
    'ma_hey_spr_04_phase.questphase': '116765ABA34F8869BD1B67975676A620A202599A5E4B824ED414C7414A6A6D07',
    'may_hey_spr_04_01_exposition.scene': 'E6780B02633AF2F0D29C3930D0A71537892B04D62164222864B6062B31EF51F5',
    'sa_ep1_courier_outro_intro_scene.questphase': 'A0B8A3883B6D85300E57456ED890828645CDA84457300FCA4DAE9A00EF35B02C',
    'sa_ep1_courier_outro_muammar_dam.scene': '704BB383687039E5E2523428B231246197407336D94E86E6E536C112B03CB0D2',
    'yoko.scene': '0B888FB40D3CC63E8DF832A637298877E5291EB0C2D9962B20D4BAB86449F757',
}


class PhaseEdit(Edit):
    """Insert a Tower guard at an existing edge without moving its other sockets."""

    @staticmethod
    def key(handle):
        return str(handle.get('HandleId', handle.get('HandleRefId')))

    def guard(self, graph, guard_id, before, after, tower_outputs):
        source_id, source_port = before
        dest_id, dest_port = after
        source = self.node(graph, source_id)
        dest = self.node(graph, dest_id)
        source_handle, outgoing = self.socket(source, source_port)
        dest_handle, incoming = self.socket(dest, dest_port)
        matches = []
        for index, handle in enumerate(outgoing['connections']):
            edge = self.r.d(handle)
            if edge.get('source') and self.key(edge['source']) == source_handle:
                if edge.get('destination') and self.key(edge['destination']) == dest_handle:
                    matches.append((index, self.key(handle)))
        (out_index, edge_handle), = matches
        in_index, = [i for i, handle in enumerate(incoming['connections'])
                     if self.key(handle) == edge_handle]
        outgoing['connections'].pop(out_index)
        incoming['connections'].pop(in_index)

        assert guard_id not in {self.r.d(h)['id'] for h in graph['nodes']}
        guard = self.add(graph, {
            '$type': 'questConditionNodeDefinition', 'id': guard_id,
            'condition': self.fact(TOWER_FACT, 1),
        }, [('CutDestination', 'CutDestination'), ('In', 'Input'),
            ('True', 'Output'), ('False', 'Output')])
        self.link(source, source_port, guard, 'In')
        outgoing['connections'].insert(out_index, outgoing['connections'].pop())
        self.link(guard, 'False', dest, dest_port)
        incoming['connections'].insert(in_index, incoming['connections'].pop())
        for target, port in tower_outputs:
            self.link(guard, 'True', self.node(graph, target), port)

    def scene_copy(self, graph, original, new_id, depot):
        assert new_id not in {self.r.d(h)['id'] for h in graph['nodes']}
        node = self.node(graph, original)
        assert node['$type'] == 'questSceneNodeDefinition'
        ports = [(value(self.r.d(h)['name']), self.r.d(h)['type']) for h in node['sockets']]
        payload = self.clone(node, self.r, skip=('sockets',))
        payload['id'] = new_id
        path = payload['sceneFile']['DepotPath']
        assert path['$storage'] == 'string'
        path['$value'] = depot
        return self.add(graph, payload, ports)

    def finish(self):
        # A socket can be defined inline on an edge that was just removed.
        # Its surviving handles still need the original definition.
        return order_handles(self.doc, self.r.handles)


def vehicle(doc, immobilize, spawn, marker, bark, cleanup, poi):
    edit = PhaseEdit(doc)
    graph = edit.graph('root')
    assert edit.node(graph, bark)['$type'] == 'questVoicesetManagerNodeDefinition'
    # The vehicle remains immobilized for the normal investigation. Once the
    # player reaches the trigger, the native POI-to-objective handoff can run.
    edit.guard(graph, 65000, (immobilize, 'Out'), (spawn, 'In'), [(poi, 'Inactive')])
    # An older running phase can already be past the spawn. Its native
    # deactivation and journal handoff still run when the spawn wait releases.
    edit.guard(graph, 65001, (marker, 'Out'), (bark, 'In'),
               [(cleanup, 'In'), (poi, 'Inactive')])
    return edit.finish()


def clue(doc, graph_path, gate, scene_node, entry):
    edit = PhaseEdit(doc)
    graph = edit.graph(graph_path)
    edit.guard(graph, 65000, (gate, 'Out'), (scene_node, entry), [])
    return edit.finish()


def wellsprings_phase(doc):
    edit = PhaseEdit(doc)
    graph = edit.graph('root')
    edit.scene_copy(graph, 162, 65000, WELLSPRINGS)
    edit.scene_copy(graph, 207, 65001, WELLSPRINGS)
    edit.guard(graph, 65002, (163, 'Out'), (162, 'spawn_johnny_in'),
               [(65000, 'spawn_johnny_in')])
    edit.guard(graph, 65003, (164, 'Out1'), (162, 'lookats_in'), [(65000, 'lookats_in')])
    edit.guard(graph, 65004, (206, 'Out'), (207, 'knockback'), [(65001, 'knockback')])
    return edit.finish()


def dam_phase(doc):
    edit = PhaseEdit(doc)
    graph = edit.graph('root')
    dam = edit.scene_copy(graph, 6, 65000, DAM)
    interaction = edit.scene_copy(graph, 126, 65001, DAM)
    edit.guard(graph, 65002, (154, 'Out'), (6, 'Start 0'), [(65000, 'Start 0')])
    edit.guard(graph, 65003, (6, 'mummar_alldone'), (126, 'talk_interaction'),
               [(65001, 'talk_interaction')])
    edit.link(dam, 'mummar_alldone', interaction, 'talk_interaction')
    for target in (149, 174):
        edit.link(dam, 'mummar_alldone', edit.node(graph, target), 'In')
    edit.link(dam, 'police car leaves', edit.node(graph, 19), 'In')
    return edit.finish()


def selected_speech(scene, selection):
    """Bind each approved screenplay item to its single event on the pinned node."""
    selected = {}
    for node, items in selection.items():
        matched = set()
        for handle in scene.nodes[node]['events']:
            event = scene.r.d(handle)
            item = event.get('screenplayLineId', {}).get('id')
            if event['$type'] != 'scnDialogLineEvent' or item not in items:
                continue
            assert item not in matched, (node, item)
            matched.add(item)
            selected[str(event['id']['id'])] = {'node_id': node, 'speaker': items[item]}
        assert matched == items.keys(), (node, matched, items)
    return selected


def wellsprings_scene(doc, depot):
    scene = BatchScene(doc, 'may_hey_spr_04_01_exposition.scene')
    scene.remove_presentation({})
    scene.skip(6, [])
    scene.mute_dispatch(36, 'danger_cautious_var_1')
    scene.skip_actor_nodes()
    return finish_scene(scene, depot, WELLSPRINGS)


def dam_scene(doc, depot):
    scene = BatchScene(doc, 'sa_ep1_courier_outro_muammar_dam.scene')
    scene.remove_presentation(selected_speech(scene, {
        128: {2817: 'JOHNNY'},
        151: {5889: 'JOHNNY', 6401: 'JOHNNY'},
        585: {11009: 'JOHNNY', 11265: 'JOHNNY'},
    }))
    # The separate Johnny rant has its own presentation-only branch. The
    # parallel choice chain and Muamar's scene exits stay connected.
    scene.skip(565, [])
    scene.skip(585, [])
    scene.skip_actor_nodes()
    # The briefing option was paced around the last Johnny line. Preserve
    # every retained media interval and move only the late choice callback.
    briefing = scene.nodes[128]
    events = [scene.r.d(handle) for handle in briefing['events']]
    choice, = [event for event in events if event['$type'] == 'scneventsSocket'
               and stamp(event['osockStamp']) == (2, 1)]
    tail = max(event['startTime'] + event['duration'] for event in events if event is not choice)
    assert tail <= briefing['sectionDuration']['stu']
    before = briefing['sectionDuration']['stu']
    choice['startTime'] = min(choice['startTime'], tail)
    briefing['sectionDuration']['stu'] = max(tail, choice['startTime']) + 1
    assert briefing['sectionDuration']['stu'] <= before
    scene.timing[128] = {'before_ms': before, 'after_ms': briefing['sectionDuration']['stu']}
    return finish_scene(scene, depot, DAM)


def yoko_scene(doc, depot):
    scene = BatchScene(doc, 'yoko.scene')
    scene.remove_presentation(selected_speech(scene, {
        402: {23041: 'JOHNNY', 23297: 'V', 23553: 'JOHNNY'},
    }))
    # Rejoin the native completion and interrupt cleanup after leaving the
    # shop. The shard condition and its parallel journal path are retained.
    scene.set_out(584, [(526,), (764, 1)])
    scene.skip(400, [(526,)])
    scene.skip(448, [])  # Relic effect paired with the removed projection.
    scene.clear(402)
    scene.set_out(402, [(526,)], create=True)
    scene.shorten(402)
    scene.skip_actor_nodes()
    return finish_scene(scene, depot, depot)


def finish_scene(scene, original, target):
    edited, changes = scene.finish()
    remaps = 0
    if original != target:
        for item in walk(edited):
            if item.get('$type') == 'ResourcePath' and value(item) == original:
                item['$value'] = target
                remaps += 1
    return edited, {**changes, 'self_reference_remaps': remaps}


def plain(path):
    for component in (path, *path.parents):
        assert not component.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT, component


def inventory(root, separator='/'):
    plain(root)
    rows = {}
    for file in root.rglob('*'):
        assert not file.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT, file
        if file.is_file():
            rows[file.relative_to(root).as_posix().replace('/', separator)] = sha(file)
    return rows


def providers():
    for folder in (AUDIT / 'capture_01', AUDIT / 'capture_02'):
        for row in read(folder / 'providers.json')['providers']:
            filename = row['depot'].split('\\')[-1]
            if row['sha256'] != PINS.get(filename):
                continue
            raw, export = folder / row['raw'], folder / row['json']
            assert sha(raw) == row['sha256'] and not row['decode_error'], raw
            if 'json_sha256' in row:
                assert sha(export) == row['json_sha256'], export
            yield filename, {**row, 'raw': str(raw), 'json': str(export)}


def main():
    assert not OUT.exists() and not CANDIDATE.exists()
    assert sha(INSTALLED) == 'AF8F033C66A97CF6049FC018B923C04C3B29D799F7002E6A044898F298002931'
    assert sha(BASE / 'package_manifest.json') == 'DAB6CF45629FD2116C88E92857497CA3D702B9D3AF32BBE9927A966D6A274B19'
    installed = read(INSTALLED)
    game = Path(installed['game_root'])
    for row in installed['core_files'] + installed['required_files']:
        file = game / row['path']
        plain(file)
        assert file.resolve().is_relative_to(game) and sha(file) == row['sha256'], file
        assert file.stat().st_size == row['bytes'], file
    base_members = read(BASE / 'package_manifest.json')['source_resources']
    assert len(base_members) == 1729 and inventory(BASE / 'archive_source', '\\') == base_members
    sources = dict(providers())
    assert sources.keys() == PINS.keys()

    OUT.mkdir()
    edits = []
    operations = [
        ('ma_bls_ina_se1_40_phase.questphase', vehicle, (45, 67, 113, 69, 72, 112), None),
        ('ma_bls_ina_se1_44_phase.questphase', vehicle, (39, 43, 93, 45, 48, 92), None),
        ('ma_wat_lch_06_phase.questphase', clue, ('root/74', 17, 18, 'johnny_gate_in'), None),
        ('ma_wat_nid_03.questphase', clue, ('root/81', 17, 16, 'johnny_corpo_corpse_comment_in'), None),
        ('ma_hey_spr_04_phase.questphase', wellsprings_phase, (), None),
        ('sa_ep1_courier_outro_intro_scene.questphase', dam_phase, (), None),
        ('may_hey_spr_04_01_exposition.scene', wellsprings_scene, (), WELLSPRINGS),
        ('sa_ep1_courier_outro_muammar_dam.scene', dam_scene, (), DAM),
        ('yoko.scene', yoko_scene, (), None),
    ]
    for filename, operation, args, alias in operations:
        source = sources[filename]
        original = source['depot']
        doc = read(source['json'])
        if filename.endswith('.scene'):
            edited, changes = operation(doc, original)
        else:
            edited, changes = operation(doc, *args), {}
        target = alias or original
        path = OUT / (filename + '.json')
        write(path, edited)
        edits.append({'depot': target, 'source': source, 'json': str(path),
                      'json_sha256': sha(path), 'changes': changes})

    shutil.copytree(BASE / 'archive_source', CANDIDATE / 'archive_source')
    files = {r['path']: r['sha256'] for r in installed['core_files']}
    assert len(files) == 51
    for relative in files.keys() - {ARCHIVE}:
        dest = CANDIDATE / 'package' / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(game / relative, dest)
        assert sha(dest) == files[relative]
    write(OUT / 'plan.json', {
        'baseline': str(INSTALLED), 'game_root': str(game), 'files': files,
        'base_members': base_members, 'candidate': str(CANDIDATE), 'edits': edits,
        'game_writes': 0, 'save_writes': 0,
    })
    print(f'Authored {len(edits)} resources against {len(base_members)} baseline members.')


if __name__ == '__main__':
    main()
