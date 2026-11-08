"""Independent byte fixtures for GG1. No game data/API/process access."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess, sys
import probe


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', required=True); args = ap.parse_args()
    assert args.run.replace('_','').isalnum()
    root = probe.HERE / 'fixtures' / args.run
    assert not root.exists(); root.mkdir(parents=True)
    checks = []
    def ck(name, value):
        assert value, name
        checks.append(name)
    def make(name, initial=b'OLD_BYTES\n', **kwargs):
        folder = root / name; folder.mkdir(); source = folder / 'source'; source.mkdir()
        log = source / 'game.log'; log.write_bytes(initial)
        rec = probe.Recorder(folder / 'capture', {'game': log}, source_root=source, **kwargs)
        return folder, log, rec
    def append(p, data):
        with p.open('ab') as f: f.write(data)
    def captured(r): return (r.output / 'stream/game.log').read_bytes()

    folder, log, r = make('normal')
    initial_hash = probe.sha(log)
    ck('baseline preserves source and keeps old bytes out of new stream', captured(r) == b'' and probe.sha(log) == initial_hash)
    append(log, b'FIRST\n'); r.poll(); r.poll()
    ck('append captured once, no duplicate on idle poll', captured(r) == b'FIRST\n')
    append(log, b'SECOND\n'); r.poll()
    ck('multiple polls preserve exact appended bytes', captured(r) == b'FIRST\nSECOND\n')
    ck('context explicitly separate', (r.output / 'context/game.before.log').read_bytes() == b'OLD_BYTES\n')
    ck('reader never writes the source', log.read_bytes() == b'OLD_BYTES\nFIRST\nSECOND\n')

    folder, log, r = make('truncate', b'x' * 300)
    append(log, b'BEFORE\n'); r.poll(); log.write_bytes(b'NEW\n'); r.poll()
    ck('truncate captures new epoch from0 without old-stream loss', captured(r) == b'BEFORE\nNEW\n')
    ck('truncate gap remains visible', r.gaps and r.gaps[-1]['possible_unread_gap'])

    folder, log, r = make('same_size_rewrite', b'OLD\n')
    log.write_bytes(b'NEW\n'); r.poll()
    ck('same-inode same-size rewrite detected by anchor', captured(r) == b'NEW\n' and r.gaps)

    folder, log, r = make('rotate')
    append(log, b'UNREAD_BEFORE_ROTATION\n')
    rotated = log.with_name('game.log.1')
    assert log.resolve().is_relative_to(root.resolve()) and rotated.absolute().is_relative_to(root.absolute())
    log.rename(rotated); log.write_bytes(b'NEW_EPOCH\n'); r.poll()
    ck('renamed unread suffix recovered by file identity', captured(r) == b'UNREAD_BEFORE_ROTATION\nNEW_EPOCH\n')
    ck('rotation recovery still declares epoch change', r.gaps[-1]['old_renamed_suffix_recovered'] is True)

    folder, log, r = make('missing')
    log.unlink(); r.poll(); log.write_bytes(b'AFTER_MISSING\n'); r.poll()
    ck('source disappearance/reappearance retained and explicitly recorded', b'AFTER_MISSING\n' in captured(r) and any('FileNotFoundError' in str(e) for e in r.events))

    folder = root / 'new_source'; folder.mkdir(); source = folder / 'source'; source.mkdir(); log = source / 'later.log'
    r = probe.Recorder(folder / 'capture', {'game': log}, source_root=source)
    log.write_bytes(b'FIRST_NEW_SOURCE\n'); r.poll()
    ck('source first appearing after start begins at0', captured(r) == b'FIRST_NEW_SOURCE\n')

    folder, log, r = make('cap', limit=7)
    append(log, b'123456789'); r.poll()
    ck('byte cap is exact and explicitly hit', captured(r) == b'1234567' and r.total == 7 and r.limit_hit)

    folder, log, r = make('utf8', b'')
    encoded = 'Quest 日本\n'.encode(); append(log, encoded[:8]); r.poll(); append(log, encoded[8:]); r.poll()
    ck('split multibyte text is preserved byte-for-byte', captured(r) == encoded)

    folder, log, r = make('source_link')
    other = folder / 'external.txt'; other.write_bytes(b'KEEP_SOURCE_LINK_TARGET')
    log.unlink(); log.symlink_to(other); r.poll()
    ck('source symlink never read or changed', captured(r) == b'' and other.read_bytes() == b'KEEP_SOURCE_LINK_TARGET' and any('Linked path refused' in str(e) for e in r.events))

    folder, log, r = make('output_link')
    target = r.output / 'stream/game.log'; other = folder / 'external.txt'; other.write_bytes(b'KEEP_TARGET')
    assert target.absolute().is_relative_to(root.absolute()); target.unlink(); target.symlink_to(other)
    append(log, b'NEW_DATA'); refused = False
    try: r.poll()
    except probe.OutputSafetyError: refused = True
    ck('output symlink refuses mutation outside owned stream', refused and other.read_bytes() == b'KEEP_TARGET')

    try:
        probe.Recorder(probe.HERE.parent / 'escaped_output', {'game': root / 'missing'}, source_root=root)
        refused = False
    except ValueError: refused = True
    ck('escaped output refused before creation', refused and not (probe.HERE.parent / 'escaped_output').exists())
    try:
        probe.Recorder(root / 'source_escape_capture', {'game': root.parent / 'outside.log'}, source_root=root)
        refused = False
    except AssertionError: refused = True
    ck('arbitrary source outside allowed read root refused', refused)

    folder, log, r = make('summary')
    data = (b'[DEBUG] Day1 : sts_ep1_03_done : 0 -> 1\n'
        b'[DEBUG] kab_05_finished : 0 -> 1\n'
        b'[PTFR_W2] attached groups=534\n'
        b'[ERROR] example diagnostic message\n')
    append(log, data); r.poll(); result = r.summary({'sts_ep1_03': 'Jason', 'sts_wat_kab_05': 'Last Login'})
    ck('canonical and source-style alias fact candidates identified', {x['id'] for x in result['gig_fact_candidates']} == {'sts_ep1_03','sts_wat_kab_05'})
    ck('candidate notices are never automatic gameplayPASS', result['status'] == 'CAPTURE_COMPLETE_AWAITING_HUMAN_GIG_CORRELATION')
    ck('possible load and error-like notices remain distinct', len(result['possible_session_boundaries']) == 1 and len(result['error_like_lines_not_automatic_failures']) == 1)
    ck('source sampler limitations explicit', any('at most3' in x for x in result['limits']))

    folder = root / 'unknown_control'; folder.mkdir(); control = folder / 'status.json'; control.write_text('{"unknown":true}')
    before = control.read_bytes()
    try: probe.owned_json(control, {'schema':'GG1_CONTROL_V1'}); refused = False
    except ValueError: refused = True
    ck('unknown control bytes are preserved', refused and control.read_bytes() == before)

    # Actual OS lock across two processes, no game access and no worker started.
    code = ('import sys;sys.path.insert(0,' + repr(str(probe.HERE)) + ');'
        'import probe;\nwith probe.recorder_lock(): print("UNEXPECTED_LOCK_ACQUIRED")')
    with probe.recorder_lock():
        child = subprocess.run([sys.executable, '-X', 'utf8', '-B', '-c', code],
            capture_output=True, text=True, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
    ck('second recorder excluded by OS lock', child.returncode != 0 and 'UNEXPECTED_LOCK_ACQUIRED' not in child.stdout)
    titles, pin = probe.catalogue()
    ck('real catalogue parsed without hardcoded historical count', bool(titles) and titles.get('sts_ep1_03') == 'The Man Who Killed Jason Foreman')
    result = {'status':'PASS_GG1_EXTERNAL_CAPTURE_FIXTURES','checks':checks,
        'probe_sha256':probe.sha(probe.HERE/'probe.py'), 'test_sha256':probe.sha(__file__),
        'catalogue':pin,'catalogued_gigs':len(titles),'scope':str(root),
        'game_API_calls':0,'real_game_or_save_writes':0}
    output = probe.HERE / (args.run + '_results.json')
    probe.fresh_json(output, result)
    print(json.dumps({'status':result['status'],'checks':len(checks),'gigs':len(titles),'output':str(output)}))


if __name__ == '__main__':
    main()
