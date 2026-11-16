"""Stage the reviewed private resource changes on the pinned JB2 package."""

from collections import Counter, defaultdict
import importlib.util
from pathlib import Path
import shutil
import stat
import sys

HERE = Path(__file__).resolve().parent
PRE = HERE.parent
WS = PRE.parent
JB2 = PRE / 'johnny_batch3_jb2'
BASE = JB2 / 'candidate_02'
INSTALLED = PRE / 'johnny_batch2_jb1/deployment_01/installed_manifest_01.json'
BATCH = PRE / 'johnny_video_review_20261109_01'
ANALYSIS = HERE / 'analysis_01'
INPUT = HERE / 'input_01'
OUT = HERE / 'candidate_01'

sys.path.append(str(JB2))
from resources import ARCHIVE, Edit, Resource, load, order_handles, read, sha, value, walk, write
from edit_scenes import SCENES, prepare_scene
from selection import select

spec = importlib.util.spec_from_file_location('jb2_phase_helpers', JB2 / 'prepare.py')
phase_helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(phase_helpers)

XL = ARCHIVE + '.xl'
ARCHIVE_PIN = 'AAC96111EF0D6ED2DA80DB0A5FF87482131C59993CCA863F9C5F4FD9D77DC37B'
BASE_PIN = '8893447F7F13F91A74D9872D0D988F65494E739C44FF25DA23A1C00F1FBE44E9'
REVIEW_PIN = '03E07EE82A1C469ECA6E11347AF4D57035E6198E16E2AA45FF93AD0C5602BE51'
FINDINGS_PIN = '9D585400DBB2D30D836E678C4D4C59863B6E9E0287428D5D24465B8175A61D76'
SUPPORT_PIN = 'F0FA7DB51FE6F215CD86F8FCC2083D04FADD5F9FAB6437B208F387609C67B862'
NOTE_PIN = '1C9029DA2FC00AAA8DBD07A363EBAD785C4841FE819F2DF820EF15B7773E259B'
RESUME = r'towercontinued\sidejobs_s23\ep1\mq306_boot.questphase'
RESUME_PINS = {
    'mq306_owner.questphase': 'BBA2D30ECAE14DAB596AFA298E09292D1DD0004DADE6DCB60B047E520362B25D',
    'mq306_aaron.questphase': '77F1BC732C33CC48288A5A2740EA3E85CBB5C72A364F4E9DF97FE22B491A646D',
}
BUNKER = 'mq305_04_bunker_confrontation.questphase'


def name(depot):
    return depot.rsplit('\\', 1)[-1]


def refs(doc):
    return {value(p) for p in walk(doc) if p.get('$type') == 'ResourcePath' and
            str(value(p)).endswith(('.questphase', '.scene'))}


def closure(root, dependencies):
    reached = {root}
    pending = [root]
    while pending:
        for child in dependencies.get(pending.pop(), set()) - reached:
            reached.add(child)
            pending.append(child)
    return reached


def remap(doc, aliases):
    changed = Counter()
    for p in walk(doc):
        if p.get('$type') == 'ResourcePath' and value(p) in aliases:
            changed[value(p)] += 1
            p['$value'] = aliases[value(p)]
    return dict(changed)


def bunker_phase(doc):
    ed = Edit(doc)
    root = ed.graph('root')
    for start, port, end, input_port in ((240, 'False', 138, 'in_johnny_max_jones'),
                                         (217, 'Out1', 215, 'in_johnny_all_dead')):
        assert ed.node(root, end)['$type'] == 'questSceneNodeDefinition'
        phase_helpers.unlink(ed, root, start, port, end, input_port)
    combat = ed.graph('root/238')
    # All three native combat paths already converge on node 5. The original
    # terminating output now follows that gate without the ghost-only scene.
    phase_helpers.move(ed, combat, 5, 'Out1', (15, 'In'), (1, 'In'))
    return order_handles(doc, ed.r.handles)


def source_rows(review):
    findings = BATCH / 'review_01/findings.json'
    assert sha(findings) == FINDINGS_PIN
    manifests = {BATCH / 'review_01' / m['path']: m['sha256']
                 for m in read(findings)['source_manifests']}
    manifests[ANALYSIS / 'source_support/manifest.json'] = SUPPORT_PIN
    rows = {}
    for path, digest in manifests.items():
        assert sha(path) == digest, path
        manifest = read(path)
        assert manifest['status'] == 'PASS_BATCH4_CURRENT_PROVIDER_PINS' and not manifest['issues']
        for row in manifest['resources']:
            assert row['depot'] not in rows and not row['decode_error'], row['depot']
            rows[row['depot']] = row
    assert len(rows) == 56
    for quest in review['quests']:
        assert quest['registry_decision'] == 'INCLUDE'
        for depot, digest in quest['current_private_resource_pins'].items():
            assert rows[depot]['sha256'] == digest, depot
    return rows, {str(p): h for p, h in manifests.items()}


def aliases_for(review, docs, targets):
    dependencies = {p: refs(d) for p, d in docs.items() if p.endswith('.questphase')}
    aliases, wrappers, routes = {}, set(), {}
    handled = set()
    for quest in review['quests']:
        for root in quest['registered_entries']:
            reach = closure(root, dependencies)
            leaves = reach & targets
            routes[root] = sorted(leaves)
            assert leaves or root == RESUME, root
            handled.update(leaves)
            # Work back from the changed depots. An in-place private scene
            # never requires its parent reference to change.
            needed = {p for p in leaves if not p.startswith('towercontinued\\')}
            while True:
                parents = {p for p in reach & dependencies.keys() if dependencies[p] & needed}
                native = {p for p in parents if not p.startswith('towercontinued\\')}
                if native <= needed:
                    wrappers.update(parents - native)
                    break
                needed.update(native)
            for source in needed:
                alias = f"towercontinued\\johnny_batch4\\{quest['id']}\\{name(source)}"
                assert aliases.get(source, alias) == alias, source
                aliases[source] = alias
    assert handled == targets and len(set(aliases.values())) == len(aliases)
    assert wrappers <= set(routes) and len(wrappers) == 9
    return aliases, wrappers, routes


def assert_plain(path):
    assert not path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT, path


def inventory(root, depot_names=False):
    for p in (root, *root.parents):
        assert_plain(p)
    files = {}
    for p in root.rglob('*'):
        assert_plain(p)
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            files[rel.replace('/', '\\') if depot_names else rel] = sha(p)
    return files


def verify_base():
    assert sha(BASE / 'package_manifest.json') == BASE_PIN
    manifest = read(BASE / 'package_manifest.json')
    assert manifest['epoch'] == 'JB2' and manifest['archive_payloads'] == 1603
    expected = {p['path']: p['sha256'] for p in manifest['files']}
    assert len(expected) == 51 and expected[ARCHIVE] == ARCHIVE_PIN
    assert inventory(BASE / 'package') == expected
    assert inventory(BASE / 'archive_source', depot_names=True) == manifest['source_resources']
    installed = read(INSTALLED)
    assert installed['core_epoch'] == 'JB1'
    game = Path(installed['game_root'])
    assert len(installed['core_files']) == 51 and len(installed['required_files']) == 26
    for row in installed['core_files'] + installed['required_files']:
        path = game / row['path']
        assert path.resolve().is_relative_to(game), path
        assert sha(path) == row['sha256'], path
    assert {row['path']: row['sha256'] for row in installed['core_files']}[XL] == expected[XL]
    return manifest, installed


def resume_proof(docs, baseline):
    current = refs(docs[RESUME])
    decoded = {}
    for filename, digest in RESUME_PINS.items():
        depot, = current
        assert name(depot) == filename and baseline['source_resources'][depot] == digest
        assert sha(BASE / 'archive_source' / depot) == digest
        path = ANALYSIS / (filename + '.json')
        model = Resource(read(path)).normalize()
        assert not model['errors'], model['errors']
        current = refs(read(path))
        decoded[depot] = {'sha256': digest, 'json': str(path), 'json_sha256': sha(path),
                          'scene_or_phase_references': sorted(current)}
    assert not current
    return decoded


def main():
    assert not INPUT.exists() and not OUT.exists(), 'Fresh plan and candidate required'
    assert HERE.resolve() == HERE and HERE.is_relative_to(WS)
    review_path = BATCH / 'review_manifest.json'
    assert sha(review_path) == REVIEW_PIN
    review = read(review_path)
    assert sha(INSTALLED) == review['input_pins'][str(INSTALLED)]
    notes = BATCH / 'output_01/Ten_quest_removal_and_rewire_notes.txt'
    assert sha(notes) == NOTE_PIN, 'The reviewed worksheet has changed'
    selection = select(BATCH, notes.read_bytes())
    rows, manifests = source_rows(review)
    selected = defaultdict(dict)
    for event in selection['events']:
        assert rows[event['depot']]['sha256'] == event['source_sha256']
        selected[event['depot']][str(event['event_id'])] = event
    targets = {p for p in rows if name(p) in SCENES}
    assert len(targets) == len(SCENES) and selected.keys() <= targets
    docs = {p: load(r) for p, r in rows.items() if p.endswith('.questphase') or p in targets}
    aliases, wrappers, routes = aliases_for(review, docs, targets)
    edits = []
    for source in sorted(targets | aliases.keys() | wrappers):
        doc = docs[source]
        depot = aliases.get(source, source)
        changed_refs = remap(doc, aliases)
        evidence = None
        if source in targets:
            doc, evidence = prepare_scene(doc, name(source), selected[source])
        else:
            assert changed_refs, source
            if name(source) == BUNKER:
                doc = bunker_phase(doc)
        model = Resource(doc).normalize()
        assert not model['errors'], (source, model['errors'])
        edits.append((doc, {'depot': depot, 'source': rows[source], 'is_new': source in aliases,
                            'reference_changes': changed_refs, 'scene_evidence': evidence}))

    baseline, installed = verify_base()
    resume = resume_proof(docs, baseline)
    for _, row in edits:
        source, depot = row['source'], row['depot']
        if row['is_new']:
            assert depot not in baseline['source_resources'] and not source['depot'].startswith('towercontinued\\')
        else:
            assert baseline['source_resources'][depot] == source['sha256'], depot

    shutil.copytree(BASE / 'archive_source', OUT / 'archive_source')
    shutil.copytree(BASE / 'package', OUT / 'package', ignore=shutil.ignore_patterns(name(ARCHIVE.replace('/', '\\'))))
    INPUT.mkdir()
    for doc, row in edits:
        p = INPUT / (row['depot'] + '.json')
        p.parent.mkdir(parents=True, exist_ok=True)
        write(p, doc)
        row.update(edited_json=str(p), edited_json_sha256=sha(p))
    shutil.copyfile(notes, INPUT / 'received_notes.txt')
    selection_path = INPUT / 'selection.json'
    write(selection_path, selection)
    write(INPUT / 'plan.json', {
        'epoch': 'JB3', 'predecessor': 'JB2', 'candidate': str(OUT),
        'installed_baseline': str(INSTALLED), 'installed_baseline_sha256': sha(INSTALLED),
        'baseline_package': str(BASE / 'package_manifest.json'), 'baseline_package_sha256': BASE_PIN,
        'game_root': installed['game_root'], 'old_archive_count': baseline['archive_payloads'],
        'notes_sha256': NOTE_PIN, 'selection': str(selection_path), 'selection_sha256': sha(selection_path),
        'source_manifests': manifests, 'providers': list(rows.values()),
        'aliases': aliases, 'registered_routes': routes, 's23_resume': resume,
        'edits': [row for _, row in edits], 'game_writes': 0, 'save_writes': 0,
    })
    print(f'Staged {len(edits)} resources with {len(aliases)} new private depot paths.')


if __name__ == '__main__':
    main()
