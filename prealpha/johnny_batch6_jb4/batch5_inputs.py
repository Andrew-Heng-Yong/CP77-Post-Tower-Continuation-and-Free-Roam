"""Bind the previously reviewed Batch 5 JSON to the new cumulative build."""

from baseline import BATCH5, BASE, HERE, PRE, read, sha, write


def main():
    path = BATCH5 / 'source_manifest.json'
    assert sha(path) == '683D0D2AD38FDE6132E3EDAF438BE1673E4D67ADEE92BA4ED399114726CCB8E5'
    manifest = read(path)
    assert manifest['status'] == 'BATCH5_EDITED_SOURCE_ONLY' and manifest['baseline'] == 'JB3'
    assert sha(BATCH5 / 'checks.json') == manifest['checks_sha256']
    previous = read(BASE / 'package_manifest.json')['source_resources']
    edits = []
    for row in manifest['files']:
        edited = BATCH5 / row['output']
        assert sha(edited) == row['output_sha256'], edited
        target = row['private_depot']
        if target in previous:
            assert previous[target] == row['source_sha256']
        edits.append({
            'depot': target, 'source_depot': row['source_depot'], 'source_sha256': row['source_sha256'],
            'edited_json': str(edited), 'edited_json_sha256': row['output_sha256'], 'is_new': target not in previous,
        })
    review = PRE / 'johnny_video_review_20261110_01/review_01'
    providers = {}
    for m in read(review / 'findings.json')['source_manifests']:
        capture = review / m['path']
        assert sha(capture) == m['sha256']
        for row in read(capture)['resources']:
            providers[row['depot']] = {'depot': row['depot'], 'archive': row['archive'], 'sha256': row['sha256']}
    assert len(edits) == 42 and sum(r['is_new'] for r in edits) == 32
    assert {r['source_depot'] for r in edits} <= providers.keys()
    out = HERE / 'input_01'
    out.mkdir(exist_ok=True)
    target = out / 'batch5.json'
    assert not target.exists()
    write(target, {'edits': edits, 'providers': list(providers.values()), 'source_manifest_sha256': sha(path)})


if __name__ == '__main__':
    main()
