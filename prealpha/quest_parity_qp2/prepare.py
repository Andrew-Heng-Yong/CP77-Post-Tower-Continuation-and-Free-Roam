"""Compose the current Core package with the reviewed quest and rooftop fixes."""

from pathlib import Path
import importlib.util
import shutil
import sys

HERE = Path(__file__).resolve().parent
PRE = HERE.parent
WS = PRE.parent
JB3 = PRE / 'johnny_batch4_jb3/candidate_01'
JB4 = PRE / 'johnny_batch6_jb4'
ML1 = PRE / 'monk_lipsync_ml1_jb4'
INSTALLED = PRE / 'monk_lipsync_ml1_jb4_deploy_02/deployment_01/installed_manifest_01.json'
BASE = ML1 / 'candidate_01'
BASE_MANIFEST = BASE / 'package_manifest.json'
QP1 = PRE / 'quest_parity_qp1/candidate_01'
TH1 = PRE / 'tower_handoff_th1'
PS1 = PRE / 'profile_setup_ps1'
JUDY = PRE / 'judy_travel_sms_20261106_01'
AUDIT = WS / 'diagnostics/quest_animation_parity_20261110_01'
OUT = HERE / 'candidate_01'
BASELINE = HERE / 'baseline.json'
XL = 'archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
ENTRY = r'towercontinued\native_gigs_u9\sts_ep1_06_entry.questphase'
BLOCK = r'towercontinued\heavy_hearts_hh1\workspots.streamingblock'
AMBIENT = r'towercontinued\quest_parity_qp1\heavy_hearts_ambient.questphase'
TRUCK = r'towercontinued\sidejobs_s29\native\base\quest\minor_quests\mq017\scenes\mq017_streetkid_03_confront_thugs.scene'
LIPMAP = r'towercontinued\sidejob_repair_sr1\en-us.lipmap'
S29 = 'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds'
COVER = 'r6/scripts/PTFR_Consolidated/PTFR_LoadingCoverLC1.reds'
JUDY_ROOT = r'base\quest\side_quests\sq030\phases'
TH1_PROOF = TH1 / 'provenance.json'
QP1_PROOF = QP1 / 'verification.json'
JUDY_PROOF = JUDY / 'verification.json'

sys.path.insert(0, str(JB4))
from baseline import ARCHIVE, inventory, plain, read, sha, write


def checked(path, digest):
    path = Path(path)
    plain(path)
    assert sha(path) == digest, path
    return path


def module(name, path, digest):
    spec = importlib.util.spec_from_file_location(name, checked(path, digest))
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def baseline():
    installed = read(checked(INSTALLED, '41925025E0D648106445DEC7899269129FE487F1C9F9F47410A72FFE1507A02F'))
    assert installed['core_epoch'] == 'ML1' and Path(installed['source_candidate']) == BASE
    base = read(checked(BASE_MANIFEST, installed['package_manifest_sha256']))
    assert base['files'] == installed['core_files'] and base['archive_payloads'] == 1723
    game = Path(installed['game_root'])
    assert len(installed['core_files']) == 51 and len(installed['required_files']) == 26
    for row in installed['core_files'] + installed['required_files']:
        p = checked(game / row['path'], row['sha256'])
        assert p.resolve().is_relative_to(game) and p.stat().st_size == row['bytes'], p
    return installed, base


def compose_scripts(older, current, qp1):
    old_core = {r['path']: r['sha256'] for r in older['files']}
    now_core = {r['path']: r['sha256'] for r in current['files']}
    qp1_core = {r['path']: r['sha256'] for r in qp1['files']}
    th = module('th1_source_checks', TH1 / 'test_source.py',
                'A661023A0DAD12C2291A44FF7C3F190C8D253D6884AF14F42FC3A22501191B5F')
    ps = module('ps1_source_checks', PS1 / 'test_source.py',
                '3D3B8185CB0222233027FBB52C3A96B19B9A8A08F154186DBFF681DB85128B9F')
    th_pins = read(checked(TH1_PROOF, '5978368286501CCC3419A1866C0D31F38102D8EAFA3369C4DD9142A019606E5D'))
    ps_pins = read(checked(PS1 / 'provenance.json', '26697D92EE2F2770367A050EB3E589C58B8128FC1C0D8BD8D658C6A79360EFAA'))
    th_patch = ps.read_patch(checked(TH1 / 'source.patch', 'FA8E74A5A68BE8A51A06632F6E0B3D74E69C5843257D58734546B956B79A14C9'))
    ps_patch = ps.read_patch(checked(PS1 / 'source.patch', '3CAEDBDC09337AF19675EB21A856456720EBFCF1FF57B9ACC9F594C870FDE3A0'))
    assert th.PINS == th_pins
    assert set(th_patch) == th_pins['files'].keys() and len(th_patch) == 5
    assert set(ps_patch) == ps_pins['files'].keys() and len(ps_patch) == 3
    assert th_patch.keys() & ps_patch.keys() == {COVER}
    normalize = lambda data: data.decode().replace('\r\n', '\n')

    scripts, th_before, th_after, ps_before, ps_after = {}, {}, {}, {}, {}
    for path, hunks in th_patch.items():
        old = checked(JB3 / 'package' / path, old_core[path]).read_bytes()
        current_bytes = checked(BASE / 'package' / path, now_core[path]).read_bytes()
        assert old_core[path] == th_pins['files'][path]['before']
        delta = th.apply_in_memory(old, hunks)
        assert ps.sha(delta) == th_pins['files'][path]['after']
        if path == COVER:
            assert ps.apply(old, ps_patch[path]) == current_bytes
            delta = ps.apply(delta, ps_patch[path], exact=False)
        else:
            assert current_bytes == old
        scripts[path] = delta
        th_before[Path(path).name] = normalize(current_bytes)
        th_after[Path(path).name] = normalize(delta)
    for path, hunks in ps_patch.items():
        old = checked(JB3 / 'package' / path, ps_pins['files'][path]['before']).read_bytes()
        existing = checked(BASE / 'package' / path, ps_pins['files'][path]['after']).read_bytes()
        assert ps.apply(old, hunks) == existing
        ps_before[Path(path).name] = normalize(old)
        ps_after[Path(path).name] = normalize(scripts.get(path, existing))
    th.test_gate(th_after['PTFR_RestrictionsR1.reds'])
    th.test_preservation(th_before, th_after)
    th.test_recovery(th_after['PTFR_HistorySnapshotHS1.reds'])
    ps.source_checks(ps_before, ps_after)

    assert now_core[S29] == old_core[S29]
    old = normalize(checked(BASE / 'package' / S29, now_core[S29]).read_bytes())
    scripts[S29] = checked(QP1 / 'package' / S29, qp1_core[S29]).read_bytes()
    new = normalize(scripts[S29])
    start = new.index('  private func RestoreMQ018MessageContact() -> Void {')
    end = new.index('  private func Unclaimed(i: Int32) -> Bool {', start)
    call = '    this.RestoreMQ018MessageContact();\n'
    assert new.count(call) == 1 and (new[:start] + new[end:]).replace(call, '', 1) == old
    return scripts


def inputs():
    installed, base = baseline()
    old = read(checked(JB3 / 'package_manifest.json', '2CCDB16A29B7EBE3AC43193D360839BF5543EC34677179D9B7921DD91C7CEBDF'))
    qp1 = read(checked(QP1 / 'package_manifest.json', '69A61611FC9B5B04B7FC78EC38530E381CFA0626F628C373F90BD44CBE644FD8'))
    assert qp1['status'] == 'STAGED_QP1_READBACK_VERIFIED'
    qp_proof = read(checked(QP1_PROOF, qp1['verification_sha256']))
    assert qp_proof['registration']['phase_node_id'] == 60197
    qread = read(checked(QP1 / 'archive_readback.json', qp1['archive_readback_sha256']))
    assert len(qread['members']) == qp1['archive_payloads'] == 1639
    hh = read(checked(QP1 / 'heavy_hearts/resources.json', 'D93C6ECFC964EDBB84DF88DF96EA59B44072DE6D70348642E1E29549CD839C63'))
    assert set(qp1['changed_depots']) == {ENTRY, BLOCK, TRUCK, LIPMAP}
    assert set(qp1['new_depots']) == set(hh['new_depots']) and len(qp1['new_depots']) == 3 and AMBIENT in qp1['new_depots']

    judy = read(checked(JUDY / 'candidate_01/package_manifest.json', 'F91945EE5AEAF30D9591D882ED30C9AEC947AD7EE6F57043BFBEBD4C9E977B59'))
    assert judy['status'] == 'STAGED_JUDY_TRAVEL_SMS_READBACK_VERIFIED'
    jproof = read(checked(JUDY_PROOF, '7FCE3EA7BD375B298C5E8E843D6CDCE4922B5EA87AA7F3AAE9076C4BBAC0F127'))
    jc = read(checked(JUDY / 'serialized_01/manifest.json', '39D4B82A240F3140E6071B59D8325EC295C3A06EF89C88E068079A78EB483A02'))
    assert jproof['status'] == 'PASS_TYPED_JUDY_TRAVEL_GUARDS'
    jchanges = {r['depot']: r['sha256'] for r in jproof['resources']}
    assert len(jchanges) == 3 and set(jchanges) == set(judy['added_official_depot_overrides'])
    assert jchanges == {r['depot']: r['sha256'] for r in jc['resources']}
    assert all(judy['source_resources'][depot] == digest for depot, digest in jchanges.items())

    current = base['source_resources']
    before = old['source_resources']
    assert current[LIPMAP] == qread['members'][LIPMAP]
    assert current[ENTRY] != before[ENTRY] != qread['members'][ENTRY]
    assert all(current[d] == before[d] for d in (BLOCK, TRUCK))
    new = set(qp1['new_depots']) | jchanges.keys()
    assert len(new) == 6 and not new.intersection(current)
    copies = {d: checked(QP1 / 'archive_source' / d, qread['members'][d])
              for d in [BLOCK, TRUCK, *qp1['new_depots']]}
    for d, digest in jchanges.items():
        copies[d] = checked(JUDY / 'serialized_01' / Path(d).name, digest)
    donor = checked(QP1 / 'archive_source' / ENTRY, qread['members'][ENTRY])

    rows = {}
    def pin(depot, archive, digest):
        paths = rows.setdefault(depot, {})
        assert paths.get(archive, digest) == digest
        paths[archive] = digest
    for d, r in hh['providers'].items():
        digest = current[d] if d == ENTRY else r['sha256']
        if Path(r['archive']).name == Path(ARCHIVE).name:
            assert current[d] == digest
        pin(d, r['archive'], digest)
    for name, r in jc['providers'].items():
        pin(JUDY_ROOT + '\\' + name + '.questphase', r['archive'], r['sha256'])
    truck = read(checked(QP1 / 'inputs.json', '34CAE8A460CDEC9678E5639CDCB3FA498BD5A5500474A172DC7635E2B930F12A'))
    for r in truck['truck'].values():
        pin(r['depot'], r['archive'], r['sha256'])
    garage = read(checked(QP1 / 'truck/area_inputs.json', '903B9C7E9C2F5A200338D39EA12128F6098BD216B4812E7F280243307D8D3342'))
    pin(garage['depot'], garage['sector']['archive'], garage['sector']['sha256'])
    for r in garage['blocks']:
        pin(r'base\worlds\03_night_city\_compiled\default\blocks\all.streamingblock', r['archive'], r['sha256'])
    for d in qp1['new_depots']:
        assert d not in rows
        rows[d] = {}
    assert set(copies) | {ENTRY} <= rows.keys()
    providers = [{'depot': d, 'archives': dict(sorted(archives.items()))} for d, archives in sorted(rows.items())]
    return installed, base, old, qp1, copies, donor, providers, sorted(new), sorted(jchanges)


def main():
    assert not OUT.exists() and not BASELINE.exists()
    installed, base, old, qp1, copies, donor, providers, new, judy_depots = inputs()
    scripts = compose_scripts(old, base, qp1)
    old_core = {r['path']: r['sha256'] for r in base['files']}
    assert inventory(BASE / 'package') == old_core
    assert inventory(BASE / 'archive_source', '\\') == base['source_resources']
    xl = next(r['sha256'] for r in qp1['files'] if r['path'] == XL)
    assert old_core[XL] == next(r['sha256'] for r in old['files'] if r['path'] == XL)
    xl_donor = checked(QP1 / 'package' / XL, xl)

    shutil.copytree(BASE / 'archive_source', OUT / 'archive_source')
    for d, origin in copies.items():
        target = OUT / 'archive_source' / d
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origin, target)
    for path in old_core.keys() - {ARCHIVE}:
        target = OUT / 'package' / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if path in scripts:
            target.write_bytes(scripts[path])
        else:
            shutil.copyfile(xl_donor if path == XL else BASE / 'package' / path, target)
    (OUT / 'package' / ARCHIVE).parent.mkdir(parents=True, exist_ok=True)
    changes = [{'path': p, 'before': old_core[p], 'after': sha(OUT / 'package' / p)} for p in sorted(scripts)]
    assert len(changes) == 6 and all(r['before'] != r['after'] for r in changes)
    write(BASELINE, {
        'game_root': installed['game_root'], 'installed_manifest_sha256': sha(INSTALLED),
        'baseline_package_sha256': sha(BASE_MANIFEST), 'before_archive': installed['archive_sha256'],
        'scripts': changes, 'xl_after': xl,
        'entry': {'depot': ENTRY, 'before': base['source_resources'][ENTRY], 'donor': str(donor), 'donor_sha256': sha(donor)},
        'copied_resources': {d: sha(p) for d, p in copies.items()}, 'new_depots': new,
        'native_overrides': judy_depots, 'providers': providers,
        'proofs': {str(p): sha(p) for p in (QP1_PROOF, JUDY_PROOF, TH1_PROOF, PS1 / 'provenance.json')},
        'script_checks': ['TH1 direct and rooftop routes', 'TH1 recovery and saved fields', 'PS1 combined cover and setup', 'QR20 exact method and tick'],
    })
    template = checked(JB4 / 'compile_setup.py', 'F098A69520E2F3876E902DB8B388B4E49CA62CA80BCE21E3C34B8C5BCAD615D6')
    source = template.read_text(encoding='utf-8')
    assert source.count('from baseline import ') == 1 and source.count('PASS_JB4_COMPLETE_SOURCE_COMPILE') == 1
    source = source.replace('from baseline import ', 'from prepare import ').replace('PASS_JB4_COMPLETE_SOURCE_COMPILE', 'PASS_QP2_COMPLETE_SOURCE_COMPILE')
    with (HERE / 'compile.py').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(source)
    print('Prepared the reviewed quest resources and six scripts. TH1 and PS1 source checks passed.')


if __name__ == '__main__':
    main()
