"""Build the provider inventory from the assessed entrances and their ownership paths."""
from capture import HERE, baseline, read, write
from verify_batch import readonly


def main():
    baseline()
    assessed = read(HERE / 'evidence_01/batch_assessment.json')
    resources = {r['rid'] for stage in assessed['stages'] for r in stage['source_resources']}
    resources.update(address[0] for stage in assessed['stages'] for owner in stage['source_owner_paths']
                     for address in owner['source_path'])
    resources.update((2840, 14739, 14760))  # Rite combat and credit, Treating Symptoms counterpart.
    with readonly('registry_02/registry.sqlite3') as db:
        rows = [dict(db.execute('SELECT * FROM resources WHERE rid=?', (rid,)).fetchone())
                for rid in sorted(resources)]
    out = HERE / 'evidence_02'
    out.mkdir()
    write(out / 'provider_inputs.json', {'resources': rows, 'existing_overlays': {}})


if __name__ == '__main__':
    main()
