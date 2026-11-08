"""Final read-only preservation and payload/pin validation. Fresh receipt only."""
from pathlib import Path
from prepare import H, meta, read, sha, write

def main():
    b = read(H / 'baseline.json'); m = read(H / 'core_manifest_02.json')
    game, save = Path(m['game_root']), Path(m['save_root'])
    checks = {}
    def ck(name, value):
        checks[name] = bool(value); assert value, name
    ck('installed_original60_sha256', all(sha(p) == s for p,s in b['installed_pins'].items()))
    ck('all310_save_file_sha256', all(sha(p) == s for p,s in b['save_sha256'].items()))
    ck('save_names_sizes_mtimes_reparse_metadata', meta(save) == b['save_metadata'])
    ck('game_names_sizes_mtimes_reparse_metadata', meta(game) == b['game_metadata'])
    ck('QR13_all_original_metadata', meta(H.parent / 'quest_restoration_qr13') == b['QR13_metadata'])
    original = read(H.parent / 'quest_restoration_qr13/baseline.json')
    ck('game_metadata_still_matches_QR13_provider_baseline', b['game_metadata'] == original['game_metadata'])
    ck('save_metadata_still_matches_QR13_baseline', b['save_metadata'] == original['save_metadata'])
    ck('all151_compile_prerequisites_unchanged', all(sha(p) == s for p,s in m['compile_inputs'].items()))
    ck('Core51_still_QR8', all(sha(game / r['path']) == r['before'] for r in m['files']))
    ck('26_protected_dependencies_exact', all(sha(game / r['path']) == r['sha256'] for r in m['required_files']))
    ck('QR13_package51_unchanged', all(sha(Path(m['package_root']) / r['path']) == r['after'] for r in m['files']))
    ck('QR13_staged_ZIP_unchanged', sha(m['zip']) == m['zip_sha256'])
    ck('all_pinned_source_and_review_proofs_unchanged', all(sha(r['path']) == r['sha256'] for r in m['proofs']))
    write(H / 'preservation.json', {'status': 'PASS_PREPARATION_PRESERVATION', 'checks': checks,
        'installed_core': 'QR8:02', 'diagnostics': 'QR10D01/D00E unchanged', 'candidate': 'QR13:02 staged only',
        'protected_installed_union': len(m['files']) + len(m['required_files']),
        'save_files': len(b['save_sha256']), 'game_writes': 0, 'installations': 0, 'game_launches': 0, 'save_or_fact_writes': 0,
        'limits': 'Unmanaged game files use complete names/size/mtime/non-followed-link metadata plus exact pins. This is not a SHA census of every game asset. No real replacement permissions or gameplay were exercised.'})
    print({'status': 'PASS_PREPARATION_PRESERVATION', 'checks': len(checks), 'installed_pins': 77, 'save_files': len(b['save_sha256'])})

if __name__ == '__main__':
    main()
