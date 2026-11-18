"""Pin the nine user-screened entries to the installed XL and packed resources."""
import binascii
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
IDS = ('mq003_orbitals', 'mq022_ezekiel', 'mq029_tourist', 'mq016_bartmoss',
       'mq036_overload', 'q305_postcontent', 'wst_ep1_09', 'sts_ep1_12_pickup', 'mws_se5_07')

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest().upper()

def main():
    output = HERE / 'sources_01'
    if output.exists():
        raise RuntimeError('Fresh output required')
    mp = ROOT / 'prealpha/mid_quest_resume_retire_20261115_01/stage_08/deployment_01/installed_manifest_01.json'
    rp = ROOT / 'prealpha/mid_quest_resume_retire_20261115_01/stage_03/pack/readback.json'
    manifest, readback = (json.loads(p.read_bytes()) for p in (mp, rp))
    pins = {r['path']: r['sha256'] for r in manifest['core_files']}
    game = Path(manifest['game_root'])
    xlrel = 'archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
    archive = game / 'archive/pc/mod/zzzz_PTFR_Combined.archive'
    assert sha(game / xlrel) == pins[xlrel]
    assert sha(archive) == manifest['archive_sha256'] == readback['archive_sha256']
    packed = {r['depot']: r['sha256'] for r in readback['members']}
    catalogue = json.loads((HERE / 'probe_01/catalogue.json').read_bytes())
    data = {r['id']: r for r in catalogue['entries']}
    blocks = re.split(r'(?m)^    - path:\s*', (game / xlrel).read_text(encoding='utf-8-sig'))[1:]
    rows = []
    for ident in IDS:
        found = []
        for block in blocks:
            depot = block.splitlines()[0].strip()
            if depot.rsplit('\\', 1)[-1] not in (ident + '.questphase', ident + '_entry.questphase'):
                continue
            parent = re.search(r'(?m)^      parent: (.+)$', block)[1].strip()
            input_node = re.search(r'(?m)^        node: \[(.+)\]', block)[1].strip()
            socket = re.search(r'(?m)^        socket: (.+)$', block)[1].strip()
            assert (parent, input_node, socket) == ('ep1\\quest\\ep1.quest', '1', 'Out')
            node = binascii.crc_hqx((depot + ':1').encode(), 65535)
            raw = Path(manifest['archive_source']) / depot
            assert sha(raw) == packed[depot]
            found.append({**data[ident], 'depot': depot, 'raw_path': str(raw),
                          'raw_sha256': packed[depot], 'generated_node': node,
                          'saved_prefix': f'1/{node}', 'parent': parent, 'input_node': [1], 'socket': socket})
        assert len(found) == 1, (ident, len(found))
        rows.extend(found)
    assert len({r['generated_node'] for r in rows}) == len(rows)
    output.mkdir()
    (output / 'inventory.json').write_text(json.dumps({
        'status': 'INSTALLED_SOURCE_PINNED', 'manifest_sha256': sha(mp), 'readback_sha256': sha(rp),
        'archive_sha256': sha(archive), 'xl_sha256': sha(game / xlrel), 'entries': rows,
        'limits': ['Nine live-screen candidates only; not a whole-mod coverage claim.',
                   'Generated-node mapping uses the reviewed ArchiveXL CRC for exact ep1 root input [1].']
    }, indent=2) + '\n', encoding='utf-8')
    print(json.dumps([{'id': r['id'], 'prefix': r['saved_prefix']} for r in rows]))

if __name__ == '__main__':
    main()
