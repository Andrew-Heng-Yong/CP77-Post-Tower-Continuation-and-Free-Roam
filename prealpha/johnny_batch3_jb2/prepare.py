"""Plan the private Batch 3 build from the installed JB1 lineage."""

import collections
import shutil
from pathlib import Path

from resources import (ARCHIVE, BASE, HERE, REVIEW, WS, Edit, Resource, load, order_handles, read,
                       sha, source_rows, value, walk, write)
from scenes import prepare_scene

OUT = HERE / 'candidate_02'
INPUT = HERE / 'input_02'
INSTALLED = BASE.parent / 'deployment_01/installed_manifest_01.json'

# Alias only the resource chain between each installed owner and an edited
# scene. Preserve original relative asset bindings and root/instance prefabs.
CHAINS = {
    'mq003': ('towercontinued/sidejobs_s28/encounters/mq003_main.questphase',
              'mq003_homeless.questphase', 'mq003_enemy_intercept.questphase', 'mq003_02_corpse.scene'),
    'mq010': ('towercontinued/sidejobs_s24/base/mq010.questphase',
              'mq010.questphase', 'mq010_03_columbarium.questphase', 'mq010_03_columbarium.scene'),
    'mq015': ('towercontinued/sidejobs_s24/base/mq015.questphase',
              'mq015_wizardbook.questphase', 'mq015_03_stash.questphase', 'mq015_04_stash.scene'),
    'mq019': ('towercontinued/sidejobs_s24/base/mq019.questphase',
              'mq019_paparazzi.questphase', 'mq019_03_night_club.questphase', 'mq019_04_manager.scene'),
    'mq030': ('towercontinued/sidejobs_s23/base_b/mq030.questphase',
              'mq030.questphase', 'mq030_melisa.questphase', 'mq030_01_melisa.scene'),
    'mq032': ('towercontinued/sidejobs_s2/mq032_sacrum.questphase',
              'mq032_sacrum.questphase', 'mq032_01_hook.questphase', 'mq032_02_maelstrom.questphase',
              'mq032_03_epilogue.questphase', 'mq032_01_hook.scene', 'mq032_02_maelstrom.scene',
              'mq032_03_epilogue.scene'),
}
PROPHET = (
    'towercontinued\\sidejobs_s23\\base_b\\mq026.questphase',
    'towercontinued\\sidejobs_s25\\prophet\\mq026_fresh.questphase',
)
SPACE_POD_PHASE = 'towercontinued\\sidejobs_s28\\encounters\\mq003_pod_phase.questphase'
NATIVE_POD_SCENE = 'base\\quest\\minor_quests\\mq003\\scenes\\mq003_03_orbital_pod.scene'
PRIVATE_POD_SCENE = 'towercontinued\\sidejobs_s28\\encounters\\mq003_pod.scene'


def unlink(ed, g, source_id, source_port, dest_id, dest_port):
    source = ed.node(g, source_id)
    dest = ed.node(g, dest_id)
    source_key, source_socket = ed.socket(source, source_port)
    dest_key, dest_socket = ed.socket(dest, dest_port)
    connection, = [ed.r.hid(h) for h in source_socket['connections']
                   if ed.r.hid(ed.r.d(h)['destination']) == dest_key]
    for socket in (source_socket, dest_socket):
        matches = [h for h in socket['connections'] if ed.r.hid(h) == connection]
        assert len(matches) == 1, (source_key, dest_key, connection)
        socket['connections'].remove(matches[0])


def link(ed, g, source_id, source_port, dest_id, dest_port):
    ed.link(ed.node(g, source_id), source_port, ed.node(g, dest_id), dest_port)


def move(ed, g, source_id, source_port, old, new):
    unlink(ed, g, source_id, source_port, *old)
    link(ed, g, source_id, source_port, *new)


def cut_control(ed, g, node_id):
    assert node_id not in {ed.r.d(h)['id'] for h in g['nodes']}
    ed.add(g, {'$type': 'questCutControlNodeDefinition', 'id': node_id, 'permanent': 1},
           [('CutDestination', 'CutDestination'), ('In', 'Input'),
            ('Out', 'Output'), ('CutSource', 'CutSource')])


def columbarium_phase(ed, g):
    # Keep genuine plaque focus and the native walk-away outcome. Cancel the
    # other path on arrival and put the single discovery award after a latch.
    for edge in [(0, 'Out', 70, 'In'), (17, 'False', 63, 'In1'), (3, 'Out', 63, 'In1'),
                 (72, 'Out', 63, 'In1'), (72, 'Out', 70, 'In'), (63, 'Out1', 8, 'johnny')]:
        unlink(ed, g, *edge)
    cut_control(ed, g, 100)
    cut_control(ed, g, 101)
    assert 102 not in {ed.r.d(h)['id'] for h in g['nodes']}
    latch = ed.r.clean(ed.node(g, 26))
    latch['id'] = 102
    ed.add(g, latch, [('CutDestination', 'CutDestination'), ('In1', 'Input'),
                      ('In2', 'Input'), ('Out1', 'Output')])
    move(ed, g, 8, 'End 0', (52, 'In'), (100, 'In'))
    link(ed, g, 100, 'CutSource', 21, 'CutDestination')
    link(ed, g, 100, 'Out', 52, 'In')
    move(ed, g, 21, 'Out', (23, 'Failed'), (101, 'In'))
    link(ed, g, 101, 'CutSource', 8, 'CutDestination')
    link(ed, g, 101, 'Out', 51, 'In')
    move(ed, g, 51, 'Out', (24, 'In'), (23, 'Failed'))
    move(ed, g, 11, 'Out', (9, 'In'), (102, 'In1'))
    move(ed, g, 23, 'Out', (22, 'In'), (102, 'In2'))
    link(ed, g, 102, 'Out1', 9, 'In')
    scene = ed.node(g, 8)
    for item in walk(scene['interruptionOperations']):
        if item.get('$type') == 'NodeRef' and value(item) == '#mq010_tr_johnny_spawn':
            item['$value'] = '#mq010_andrews_plaque'
        if item.get('$type') == 'scnOverrideTalkOnReturn_InterruptionScenarioOperation':
            item['talkOnReturn'] = 0


def phase_edits(doc, source):
    ed = Edit(doc)
    g = ed.graph('root')
    basename = source.split('\\')[-1]
    if source in PROPHET:
        # A saved Permit=1 cannot launch a new owner before REDscript polls.
        # Existing issued nodes and all of their downstream paths stay intact.
        unlink(ed, g, 1004, 'True', 1005, 'In')
    elif source == SPACE_POD_PHASE:
        move(ed, g, 78, 'Out', (79, 'Active'), (75, 'retrieve_pod_reaction'))
        unlink(ed, g, 79, 'Out', 75, 'retrieve_pod_reaction')
    elif basename == 'mq010_03_columbarium.questphase':
        columbarium_phase(ed, g)
    elif basename == 'mq019_03_night_club.questphase':
        # These two optional inner-dialogue dispatches target the actual
        # #johnny spawnset. Their sibling camera/computer signals stay intact.
        security = ed.graph('root/108')
        for src, target in ((11, 12), (29, 15)):
            node = ed.r.clean(ed.node(security, target))
            assert node['$type'] == 'questVoicesetManagerNodeDefinition'
            params, = node['type']['params']
            assert params['isPlayer'] == 0 and value(params['puppetRef']['reference']) == '#johnny'
            unlink(ed, security, src, 'Out', target, 'In')
    elif basename == 'mq032_01_hook.questphase':
        move(ed, g, 24, 'True', (19, 'Active'), (10, 'Active'))
    elif basename == 'mq032_02_maelstrom.questphase':
        move(ed, g, 127, 'True', (128, 'Active'), (131, 'Active'))
        journal = ed.r.d(ed.r.d(ed.node(g, 83)['type'])['path'])
        assert journal['realPath'].endswith('/description_johnny')
        journal['realPath'] = journal['realPath'].removesuffix('_johnny')
    return order_handles(doc, ed.r.handles)


def stage_sources():
    installed = read(INSTALLED)
    assert installed['core_epoch'] == 'JB1'
    game = Path(installed['game_root'])
    old = read(BASE / 'package_manifest.json')
    assert {p['path']: p['sha256'] for p in old['files']} == {
        p['path']: p['sha256'] for p in installed['core_files']}
    for row in installed['core_files'] + installed['required_files']:
        assert sha(game / row['path']) == row['sha256'], row['path']
    for row in old['files']:
        assert sha(BASE / 'package' / row['path']) == row['sha256'], row['path']
    src = BASE / 'archive_source'
    assert {p.relative_to(src).as_posix().replace('/', '\\'): sha(p)
            for p in src.rglob('*') if p.is_file()} == old['source_resources']
    shutil.copytree(src, OUT / 'archive_source')
    shutil.copytree(BASE / 'package', OUT / 'package',
                    ignore=lambda directory, names: ['zzzz_PTFR_Combined.archive']
                    if Path(directory).relative_to(BASE / 'package').as_posix() == 'archive/pc/mod' else [])
    scripts = []
    for owner in ('S23', 'S25'):
        path = f'r6/scripts/PTFR_Consolidated/PTFR_SideJobs{owner}.reds'
        p = OUT / 'package' / path
        before = sha(p)
        raw = p.read_bytes()
        signature = b'  private func Ready(i: Int32) -> Bool {'
        newline = b'\r\n' if b'\r\n' in raw else b'\n'
        assert raw.count(signature + newline) == 1
        line = f'    if Equals(SideJobData{owner}.ID(i), "mq026_conspiracy") {{ return false; }}'.encode()
        p.write_bytes(raw.replace(signature + newline, signature + newline + line + newline))
        scripts.append({'path': path, 'before': before, 'after': sha(p)})
    return installed, old, scripts


def main():
    assert not INPUT.exists() and not OUT.exists(), 'Fresh plan and candidate required'
    rows = source_rows()
    sel_path = REVIEW / 'selection_02.json'
    sel = read(sel_path)
    assert sel['status'] == 'BATCH3_AUDIT_CUT_DECISIONS_RECORDED'
    selected = collections.defaultdict(list)
    for event in sel['exact_speech_targets']:
        selected[event['depot']].append(event)
        assert event['source_sha256'] == rows[event['depot']]['sha256']
    assert collections.Counter(e['speaker_role'] for group in selected.values() for e in group) == {
        'JOHNNY': 46, 'V': 8}
    aliases = {}
    wrappers = set()
    for quest, (wrapper, *names) in CHAINS.items():
        wrappers.add(wrapper.replace('/', '\\'))
        for name in names:
            source, = [p for p in rows if p.startswith(f'base\\quest\\minor_quests\\{quest}\\')
                       and p.endswith('\\' + name)]
            aliases[source] = f'towercontinued\\johnny_batch3\\{quest}\\{name}'

    edits = []
    for source in sorted(set(aliases) | wrappers | set(selected) | set(PROPHET) | {SPACE_POD_PHASE}):
        row = rows[source]
        doc = load(row)
        depot = aliases.get(source, source)
        reference_changes = collections.Counter()
        references = dict(aliases)
        if source.endswith('mq003_enemy_intercept.questphase'):
            references[NATIVE_POD_SCENE] = PRIVATE_POD_SCENE
        for item in walk(doc):
            old = value(item)
            if item.get('$type') == 'ResourcePath' and old in references:
                item['$value'] = references[old]
                reference_changes[old] += 1
        evidence = None
        if source.endswith('.scene'):
            doc, evidence = prepare_scene(doc, source.split('\\')[-1], selected.get(source, []))
        else:
            try:
                doc = phase_edits(doc, source)
            except (AssertionError, KeyError) as error:
                raise ValueError(f'Unable to author {source}') from error
        r = Resource(doc)
        r.normalize()
        assert not r.errors, (source, r.errors)
        edits.append((doc, {'depot': depot, 'source': row, 'is_new': source in aliases,
                            'reference_changes': dict(reference_changes), 'scene_evidence': evidence}))
    installed, baseline, scripts = stage_sources()
    INPUT.mkdir()
    for doc, row in edits:
        p = INPUT / (row['depot'] + '.json')
        assert not p.exists()
        p.parent.mkdir(parents=True, exist_ok=True)
        write(p, doc)
        row['edited_json'] = str(p)
        row['edited_json_sha256'] = sha(p)
    plan = {'epoch': 'JB2', 'predecessor': 'JB1', 'candidate': str(OUT),
            'installed_baseline': str(INSTALLED), 'installed_baseline_sha256': sha(INSTALLED),
            'baseline_package': str(BASE / 'package_manifest.json'),
            'baseline_package_sha256': sha(BASE / 'package_manifest.json'),
            'game_root': installed['game_root'], 'selection': str(sel_path),
            'selection_sha256': sha(sel_path), 'edits': [row for _, row in edits],
            'aliases': aliases, 'scripts': scripts, 'old_archive_count': len(baseline['source_resources']),
            'game_writes': 0, 'save_writes': 0}
    write(INPUT / 'plan.json', plan)
    print(f"Staged {len(edits)} resource edits, including {len(aliases)} private aliases, and {len(scripts)} script gates.")


if __name__ == '__main__':
    main()
