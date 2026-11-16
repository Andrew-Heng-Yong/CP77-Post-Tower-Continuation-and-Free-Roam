"""Reconcile installed activity families outside the 160 selected job roster."""
import json
import sqlite3
from collections import Counter, defaultdict
from prepare import HERE, read, sha, write


def main():
    out = HERE / 'activities_01'
    assert not out.exists(), 'Fresh output required'
    db = sqlite3.connect((HERE / 'registry_02/registry.sqlite3').resolve().as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    source = read(HERE / 'report_01/coverage.json')['additional_installed_and_prerequisite_roots']
    records, prerequisites = [], []
    for row in source:
        if row['family'] == 'PREREQUISITE_REFERENCE':
            prerequisites.append(row)
            continue
        family = row['family']
        paths = [r['depot'] for r in row['registered_owners']]
        if paths and all('\\ncpd_scanner_n1\\' in p or '\\ncpd_scanners_n2\\' in p for p in paths):
            family = 'INSTALLED_NCPD_SCANNER_FAMILY'
        jp = row['journal_root']
        sites = [dict(r) for r in db.execute('SELECT * FROM journals WHERE path=? OR (path>=? AND path<?)', (jp, jp+'/', jp+'0'))]
        stages = defaultdict(list)
        for site in sites:
            if site['class'] in ('gameJournalQuestPhase', 'gameJournalQuestObjective'):
                stages[site['path']].append(site)
        defs = defaultdict(list)
        for r in db.execute('SELECT * FROM journal_definitions WHERE path=? OR (path>=? AND path<?)', (jp, jp+'/', jp+'0')):
            if r['class'] in ('gameJournalQuestPhase', 'gameJournalQuestObjective'):
                defs[r['path']].append(dict(r)); stages[r['path']]
        rids = sorted({s['rid'] for s in sites})
        providers = [dict(db.execute('SELECT rid,depot,role,sha256,status FROM resources WHERE rid=?', (rid,)).fetchone()) for rid in rids]
        record = {**row, 'family': family, 'all_root_and_child_source_sites': sites,
                  'stage_paths': [{'path': p, 'sites': ss, 'definitions': defs[p],
                                   'resume_status': 'NOT_QUALIFIED'} for p, ss in sorted(stages.items())],
                  'providers': providers, 'admission_change_authorized': False,
                  'boundaries': ['Source handlers are not saved executing-owner evidence.',
                                 'Zero phase/objective references must not be treated as a single-stage job; base journal definitions are opaque.',
                                 'These activity families retain their own existing admission policies.']}
        records.append(record)
    assert len(records) == 43 and len(prerequisites) == 11
    assert Counter(r['family'] for r in records) == {'INSTALLED_NCPD_SCANNER_FAMILY': 26, 'INSTALLED_CYBERPSYCHO_FAMILY': 17}
    out.mkdir()
    write(out / 'registry.json', {'rows': records, 'prerequisite_only_roots': prerequisites})
    summary = {'status': 'INSTALLED_ACTIVITY_SOURCE_CENSUS', 'families': dict(Counter(r['family'] for r in records)),
               'phase_objective_paths': sum(len(r['stage_paths']) for r in records),
               'without_phase_objective_references': [r['journal_root'] for r in records if not r['stage_paths']],
               'prerequisite_only_roots': len(prerequisites), 'source_registry_sha256': sha(HERE / 'registry_02/registry.sqlite3'),
               'correction': 'The singular ncpd_scanner_n1 registration for ma_wat_lch_03 is an installed scanner owner, accounted separately from ncpd_scanners_n2.',
               'limits': 'No new activity admission or resume support; stage and lifecycle qualification remains open.'}
    write(out / 'summary.json', summary)
    write(out / 'manifest.json', {'files': {p.name: sha(p) for p in out.iterdir() if p.is_file()}, 'tool_sha256': sha(__file__)})
    db.close(); print(json.dumps(summary))


if __name__ == '__main__':
    main()
