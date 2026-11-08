"""GG1: bounded, external capture of existing game logs. No game API or source writes.

Run record once; stop signals only this workspace recorder. All source files are
opened rb, briefly, so the reader does not hold a game log open across polls.
"""
from __future__ import annotations
from pathlib import Path
from contextlib import contextmanager
import argparse, collections, datetime, hashlib, json, os, re, stat, sys, time, uuid

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
SOURCE_REL = {
    'game': 'bin/x64/plugins/cyber_engine_tweaks/gamelog.log',
    'script': 'bin/x64/plugins/cyber_engine_tweaks/scripting.log',
    'cet': 'bin/x64/plugins/cyber_engine_tweaks/cyber_engine_tweaks.log',
    'redscript': 'r6/logs/redscript_rCURRENT.log',
}
MAX_BYTES = 64 * 1024 * 1024
MAX_EVENTS = 4096
CHUNK = 256 * 1024
FACT = re.compile(r'\b([A-Za-z0-9_]+)\s*:\s*(-?\d+)\s*->\s*(-?\d+)\s*$')


class OutputSafetyError(RuntimeError):
    pass


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest().upper()


def no_links(path):
    for p in (Path(path), *Path(path).parents):
        try:
            s = p.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(s.st_mode) or getattr(s, 'st_file_attributes', 0) & 0x400:
            raise ValueError(f'Linked path refused: {p}')


def inside(root, path):
    root, path = Path(root).absolute(), Path(path).absolute()
    if not path.is_relative_to(root) or '..' in path.parts:
        raise ValueError(f'Path escaped intended root: {path}')
    no_links(path)
    return path


def read_json(path):
    no_links(path)
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def fresh_json(path, data):
    path = inside(HERE, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


def owned_json(path, data):
    path = inside(HERE, path)
    if path.exists():
        previous = read_json(path)
        if previous.get('schema') != 'GG1_CONTROL_V1':
            raise ValueError('Unknown control file; preserve it')
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    fresh_json(tmp, data)
    os.replace(tmp, path)


@contextmanager
def recorder_lock():
    import msvcrt
    p = inside(HERE, HERE / 'recorder.lock')
    with p.open('a+b') as f:
        if p.stat().st_size != 0:
            raise ValueError('Unexpected lock contents')
        f.seek(0)
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            yield
        finally:
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)


def catalogue():
    source = WORK / 'docs/whitelist_final_r6_catalogue.md'
    text = source.read_text(encoding='utf-8-sig')
    section = text.split('## Selected gigs', 1)[1].split('## Selected side jobs', 1)[0]
    entries = re.findall(r'^\|\s*(.*?)\s*\|\s*`(sts_[a-z0-9_]+)`\s*\|', section, re.M)
    assert entries and len({q for _, q in entries}) == len(entries)
    return {q: title for title, q in entries}, {'path': str(source), 'sha256': sha(source)}


class Recorder:
    def __init__(self, output, sources, *, source_root, limit=MAX_BYTES, context=32768):
        self.output = inside(HERE, output)
        assert not self.output.exists(), 'Fresh capture directory required'
        self.output.mkdir(parents=True)
        self.source_root = Path(source_root).absolute()
        self.sources = {k: Path(v).absolute() for k, v in sources.items()}
        assert all(re.fullmatch('[a-z]+', k) for k in self.sources)
        assert all(p.is_relative_to(self.source_root) for p in self.sources.values())
        self.limit, self.context, self.total = limit, context, 0
        self.cursors, self.source_states, self.counts = {}, {}, collections.Counter()
        self.gaps, self.events = [], []
        self.limit_hit = False
        for p in ['stream', 'context']:
            (self.output / p).mkdir()
        for key in self.sources:
            (self.output / 'stream' / (key + '.log')).touch(exist_ok=False)
        self.event('START', {'sources': {k: str(p) for k, p in self.sources.items()},
            'mode': 'external existing-log byte capture; no additional game polling',
            'game_API_calls': 0, 'game_source_writes': 0})
        for key in self.sources:
            self.initial(key)

    def event(self, kind, data):
        if len(self.events) >= MAX_EVENTS:
            self.limit_hit = True
            return
        row = {'seq': len(self.events) + 1, 'utc': utc(), 'kind': kind, 'data': data}
        self.events.append(row)
        with inside(HERE, self.output / 'events.jsonl').open('a', encoding='utf-8') as f:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')

    def _state(self, key, value):
        if self.source_states.get(key) != value:
            self.source_states[key] = value
            self.event('SOURCE_STATE', {'source': key, 'state': value})

    def _open(self, path):
        inside(self.source_root, path)
        s = path.stat()
        if not stat.S_ISREG(s.st_mode):
            raise ValueError('Source is not a regular file')
        return path.open('rb')

    @staticmethod
    def _identity(s):
        return (s.st_dev, s.st_ino)

    def _cursor(self, f, s, offset):
        start = max(0, offset - 64)
        f.seek(start)
        return {'identity': self._identity(s), 'offset': offset,
                'anchor_start': start, 'anchor': f.read(offset - start)}

    def initial(self, key):
        path = self.sources[key]
        try:
            with self._open(path) as f:
                s = os.fstat(f.fileno())
                f.seek(max(0, s.st_size - self.context))
                data = f.read(min(self.context, s.st_size))
                (self.output / 'context' / (key + '.before.log')).write_bytes(data)
                self.cursors[key] = self._cursor(f, s, s.st_size)
            self._state(key, 'READABLE')
            self.event('SOURCE_BASELINE', {'source': key, 'offset': s.st_size,
                'identity': list(self._identity(s)), 'context_bytes': len(data),
                'context_is_preexisting_not_new_gameplay': True})
        except (OSError, ValueError) as e:
            self._state(key, type(e).__name__ + ':' + str(e)[:160])

    def _append(self, key, data):
        allowed = max(0, self.limit - self.total)
        data = data[:allowed]
        if data:
            try:
                target = inside(HERE, self.output / 'stream' / (key + '.log'))
            except ValueError as e:
                raise OutputSafetyError(str(e)) from e
            with target.open('ab') as f:
                f.write(data)
                f.flush()
            self.total += len(data)
            self.counts[key] += len(data)
        if self.total >= self.limit:
            self.limit_hit = True
        return len(data)

    def _drain_rotated(self, key, old):
        # Recover a renamed old file only within the same source directory and
        # only by its exact observed file identity. Never recursively search.
        for i, candidate in enumerate(self.sources[key].parent.iterdir()):
            if i >= 256:
                break
            try:
                no_links(candidate)
                s = candidate.stat()
                if not stat.S_ISREG(s.st_mode) or self._identity(s) != old['identity']:
                    continue
                with self._open(candidate) as f:
                    f.seek(old['anchor_start'])
                    if f.read(len(old['anchor'])) != old['anchor']:
                        return False
                    f.seek(old['offset'])
                    while not self.limit_hit:
                        block = f.read(CHUNK)
                        if not block:
                            break
                        self._append(key, block)
                return True
            except (OSError, ValueError):
                continue
        return False

    def poll(self):
        before = self.total
        for key, path in self.sources.items():
            if self.limit_hit:
                break
            try:
                with self._open(path) as f:
                    s = os.fstat(f.fileno())
                    old = self.cursors.get(key)
                    reset = old is None
                    reason = 'SOURCE_APPEARED'
                    recovered = False
                    if old:
                        f.seek(old['anchor_start'])
                        anchor = f.read(len(old['anchor']))
                        if self._identity(s) != old['identity']:
                            reset, reason = True, 'SOURCE_REPLACED'
                            recovered = self._drain_rotated(key, old)
                        elif s.st_size < old['offset'] or anchor != old['anchor']:
                            reset, reason = True, 'SOURCE_TRUNCATED_OR_REWRITTEN'
                    if reset:
                        if old:
                            gap = {'source': key, 'reason': reason, 'old_offset': old['offset'],
                                'old_renamed_suffix_recovered': recovered,
                                'possible_unread_gap': not recovered}
                            self.gaps.append(gap)
                        self.event(reason, {'source': key, 'old_suffix_recovered': recovered,
                            'interpretation': 'new source epoch; no gameplay-session continuity inferred'})
                        offset = 0
                    else:
                        offset = old['offset']
                    f.seek(offset)
                    while not self.limit_hit:
                        block = f.read(CHUNK)
                        if not block:
                            break
                        n = self._append(key, block)
                        offset += n
                        if n != len(block):
                            break
                    self.cursors[key] = self._cursor(f, os.fstat(f.fileno()), offset)
                self._state(key, 'READABLE')
            except (OSError, ValueError) as e:
                self._state(key, type(e).__name__ + ':' + str(e)[:160])
        return self.total - before

    def summary(self, titles):
        found = collections.Counter()
        fact_changes = []
        error_candidates, session_markers = [], []
        aliases = {}
        for qid in titles:
            parts = qid.split('_')
            names = [qid, qid.removeprefix('sts_')]
            if len(parts) == 4:
                names.append('_'.join(parts[2:]))
            aliases[qid] = names
        for key in self.sources:
            p = inside(HERE, self.output / 'stream' / (key + '.log'))
            with p.open('r', encoding='utf-8-sig', errors='replace') as f:
                for number, line in enumerate(f, 1):
                    match = FACT.search(line)
                    if match:
                        name, old, new = match.groups()
                        if len(fact_changes) < 10000:
                            fact_changes.append({'source': key, 'line': number, 'fact': name,
                                'previous_logged_value': int(old), 'current_logged_value': int(new)})
                        for qid, aa in aliases.items():
                            if any(name == a or name.startswith(a + '_') for a in aa):
                                found[qid] += 1
                    if len(error_candidates) < 40 and re.search(r'\b(error|exception)\b', line, re.I):
                        error_candidates.append({'source': key, 'line': number, 'text': line.strip()[:700]})
                    if len(session_markers) < 100 and ('[PTFR_W2] attached' in line or 'stage=Preparing Tower continuation' in line):
                        session_markers.append({'source': key, 'line': number, 'text': line.strip()[:350],
                            'interpretation': 'possible loading/attachment boundary, not exact saved-owner identity'})
        streams = {k: {'path': str(self.output / 'stream' / (k + '.log')),
            'bytes': (self.output / 'stream' / (k + '.log')).stat().st_size,
            'sha256': sha(self.output / 'stream' / (k + '.log'))} for k in self.sources}
        return {'status': 'CAPTURE_COMPLETE_AWAITING_HUMAN_GIG_CORRELATION',
            'bytes': self.total, 'streams': streams, 'source_states': self.source_states,
            'source_epoch_gaps': self.gaps, 'limit_hit': self.limit_hit,
            'gig_fact_candidates': [{'id': q, 'title': titles[q], 'matching_log_notices': n}
                for q, n in found.most_common()],
            'logged_fact_notices': fact_changes, 'error_like_lines_not_automatic_failures': error_candidates,
            'possible_session_boundaries': session_markers,
            'coverage': 'Appended existing logs across the bounded interval; pre-existing context is separate. No independent journal, phone, inventory or engine-owner API sampling.',
            'limits': ['FactFinder supplies batched getter-difference notices, not native callbacks or exact write time/order.',
                'Installed FactFinder defaults to at most3 reports per fact per game session; current settings may differ and were not changed.',
                'Missing/unlisted/suppressed/transient notices remain unknown; absence is not gameplay failure.',
                'Candidate gig mentions are not proof of quest entry, completion, reward idempotence or controller cleanup.',
                'Possible source gaps/loading boundaries are explicit. Human gig name/outcome are required.'],
            'game_API_calls': 0, 'game_or_save_writes': 0}


def active_pointer():
    p = HERE / 'active.json'
    if not p.exists():
        raise ValueError('No GG1 capture has been started')
    d = read_json(p)
    assert d.get('schema') == 'GG1_CONTROL_V1'
    output = inside(HERE / 'captures', Path(d['output']))
    assert read_json(output / 'identity.json')['run_id'] == d['run_id']
    return d, output


def record(seconds):
    assert 1 <= seconds <= 7200
    with recorder_lock():
        titles, source = catalogue()
        run = datetime.datetime.now(datetime.timezone.utc).strftime('GG1_%Y%m%dT%H%M%SZ_') + uuid.uuid4().hex[:8]
        output = HERE / 'captures' / run
        sources = {k: GAME / v for k, v in SOURCE_REL.items()}
        observer = Recorder(output, sources, source_root=GAME)
        fresh_json(output / 'identity.json', {'schema': 'GG1_CAPTURE_V1', 'run_id': run,
            'started_utc': utc(), 'seconds_limit': seconds, 'byte_limit': MAX_BYTES,
            'catalogue': source, 'title_count': len(titles), 'probe_sha256': sha(__file__),
            'sources': {k: str(p) for k,p in sources.items()},
            'authorization': 'User requested a general gig logger probe; external capture only.'})
        protection = {}
        current = read_json(WORK / 'prealpha/quest_restoration_qr14/deployment_01/installed_manifest_01.json')
        for row in current['core_files'] + current['required_files']:
            if row['path'] in {'archive/pc/mod/zzzz_PTFR_Combined.archive',
                'r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds',
                'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds',
                'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/init.lua',
                'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/watch.json'}:
                p = GAME / row['path']; no_links(p)
                assert sha(p) == row['sha256'], 'Current protected input drift: ' + str(p)
                protection[str(p)] = row['sha256']
        finder = GAME / 'r6/scripts/FactFinder/FactFinder.reds'
        no_links(finder)
        protection[str(finder)] = sha(finder)
        fresh_json(output / 'protected_inputs.json', protection)
        active = {'schema': 'GG1_CONTROL_V1', 'run_id': run, 'output': str(output), 'state': 'RECORDING'}
        if (HERE / 'active.json').exists():
            fresh_json(output / 'previous_active_pointer.json', read_json(HERE / 'active.json'))
        owned_json(HERE / 'active.json', active)
        started = time.monotonic(); last_status = 0.0; reason = 'DURATION_LIMIT'; failure = None
        print(json.dumps({'status': 'RECORDING', 'run_id': run, 'output': str(output),
            'max_minutes': seconds / 60, 'game_installation_changes': 0}), flush=True)
        try:
            while time.monotonic() - started < seconds:
                observer.poll()
                if (output / 'stop.request.json').exists():
                    request = read_json(output / 'stop.request.json')
                    assert request['run_id'] == run
                    reason = 'USER_STOP'; break
                if observer.limit_hit:
                    reason = 'BYTE_OR_EVENT_LIMIT'; break
                if time.monotonic() - last_status >= 3:
                    owned_json(output / 'status.json', {**active, 'utc': utc(),
                        'elapsed_s': round(time.monotonic() - started, 1), 'bytes': observer.total,
                        'source_states': observer.source_states, 'gaps': len(observer.gaps)})
                    last_status = time.monotonic()
                time.sleep(.5)
        except Exception as e:
            reason = 'RECORDER_ERROR'; failure = type(e).__name__ + ': ' + str(e)
        finally:
            # Brief drain after a normal stop/timeout; the user exits normally
            # before reporting done so buffered game logging can flush itself.
            if reason != 'BYTE_OR_EVENT_LIMIT':
                for _ in range(4):
                    try:
                        observer.poll()
                    except Exception as e:
                        failure = failure or str(e)
                    time.sleep(.5)
            observer.event('STOP', {'reason': reason, 'error': failure, 'bytes': observer.total,
                'elapsed_s': round(time.monotonic() - started, 1)})
            summary = observer.summary(titles)
            protected_after = {}
            for p,s in protection.items():
                try:
                    no_links(p)
                    current_sha = sha(p)
                    protected_after[p] = {'unchanged': current_sha == s, 'sha256': current_sha}
                except (OSError, ValueError) as e:
                    protected_after[p] = {'unchanged': False, 'error': str(e)}
            summary.update({'run_id': run, 'stop_reason': reason, 'recorder_error': failure,
                'protected_inputs': protected_after})
            fresh_json(output / 'summary.json', summary)
            final = {**active, 'state': 'STOPPED', 'utc': utc(), 'reason': reason,
                'bytes': observer.total, 'summary': str(output / 'summary.json')}
            owned_json(output / 'status.json', final)
            owned_json(HERE / 'active.json', final)
            print(json.dumps(final), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action', required=True)
    rec = sub.add_parser('record'); rec.add_argument('--seconds', type=int, default=5400)
    sub.add_parser('status'); sub.add_parser('stop')
    args = p.parse_args()
    if args.action == 'record':
        record(args.seconds)
    else:
        active, output = active_pointer()
        if args.action == 'stop' and active['state'] == 'RECORDING':
            request = output / 'stop.request.json'
            if not request.exists():
                fresh_json(request, {'run_id': active['run_id'], 'utc': utc(), 'reason': 'USER_STOP'})
            else:
                assert read_json(request)['run_id'] == active['run_id'], 'Stop request belongs to another run'
            print(json.dumps({'status': 'STOP_REQUESTED', 'output': str(output)}))
        else:
            status = output / 'status.json'
            print(json.dumps(read_json(status) if status.exists() else active))


if __name__ == '__main__':
    main()
