"""Bounded native-signal fixtures for the cooked JB1 quest edits.

This models authored sections, timers, socket cancellation, branch conditions
and explicit human actions. Other native quest commands acknowledge immediately;
it does not simulate devices, inventory, actors, AI or the game scheduler.
Unknown conditions and player interactions HOLD rather than auto-succeed.
"""
import collections
import heapq
import json
from verify import HERE, read, sha, write, normal, johnny


class Signals:
    def __init__(self, model, *, choices=None, conditions=None, acknowledgements=(), facts=None, stop=()):
        self.model = model
        self.g = model['graphs']['scene']
        self.choices = choices or {}
        self.conditions = conditions or {}
        self.ack = set(map(str, acknowledgements))
        self.facts = dict(facts or {})
        self.stop = set(map(str, stop))
        self.queue, self.trace, self.ends, self.held, self.stopped, self.writes = [], [], [], [], [], []
        self.serial = 0
        self.generations = collections.Counter()
        self.and_inputs = collections.defaultdict(set)
        self.xor = set()
        self.choice_active = set()
        self.journal = {}
        self.aids = {a['actorId']['id'] for a in model['metadata']['actors'] if 'johnny' in a['actorName'].lower()}

    def push(self, time, kind, data, owner=None):
        self.serial += 1
        generation = self.generations[owner] if owner else None
        heapq.heappush(self.queue, (time, self.serial, kind, data, owner, generation))

    def start(self, nid, ordinal=0, time=0):
        self.push(time, 'input', (str(nid), 0, ordinal))
        return self

    def emit(self, time, nid, stamp=(0, 0)):
        p = self.g['nodes'][str(nid)]['payload']
        for s in p['outputSockets']:
            if (s['stamp']['name'], s['stamp']['ordinal']) == stamp:
                for d in s['destinations']:
                    i = d['isockStamp']
                    self.push(time, 'input', (str(d['nodeId']['id']), i['name'], i['ordinal']))

    def condition(self, nid, condition):
        if nid in self.conditions:
            return self.conditions[nid]
        q = condition.get('type', {})
        if not isinstance(q, dict):
            return None
        if q.get('$type') == 'questVarComparison_ConditionType' and q['factName'] in self.facts:
            v = self.facts[q['factName']]
            return {'Equal': v == q['value'], 'NotEqual': v != q['value'], 'Greater': v > q['value'],
                    'Less': v < q['value'], 'GreaterOrEqual': v >= q['value'], 'LessOrEqual': v <= q['value']}[q['comparisonType']]
        return None

    def run(self, until=None):
        while self.queue and (until is None or self.queue[0][0] <= until):
            assert len(self.trace) < 600, 'Fixture signal bound exceeded'
            time, _, kind, data, owner, generation = heapq.heappop(self.queue)
            if owner and self.generations[owner] != generation:
                continue
            if kind == 'emit':
                self.emit(time, *data)
                continue
            nid, name, ordinal = data
            p = self.g['nodes'][nid]['payload']
            typ = p['$type']
            if typ == 'scnQuestNode':
                mapping = p['isockMappings'][ordinal]['$value']
                if name == 1026 or mapping == 'CutDestination':
                    self.generations[nid] += 1
                    continue
            elif typ == 'scnChoiceNode' and (name, ordinal) != (0, 0):
                self.choice_active.discard(nid)
                self.generations[nid] += 1
                continue
            elif typ == 'scnSectionNode' and (name, ordinal) != (0, 0):
                # Native section cancel/hide inputs do not fire its callbacks.
                self.generations[nid] += 1
                continue
            self.trace.append([time, nid, name, ordinal])
            if nid in self.stop:
                self.stopped.append([time, nid, name, ordinal])
                continue
            if typ == 'scnEndNode':
                self.ends.append([time, nid, p['type']])
                if p['type'] == 'Terminating':
                    self.queue.clear()
            elif typ == 'scnChoiceNode':
                assert not johnny(p, self.aids), 'Johnny menu reachable'
                self.choice_active.add(nid)
                if nid in self.choices:
                    option = self.choices[nid]
                    assert option < len(p['options'])
                    self.push(time, 'emit', (nid, (0, option)), nid)
                else:
                    self.held.append([time, nid, 'PLAYER_CHOICE'])
            elif typ == 'scnSectionNode':
                for e in p['events']:
                    if e['$type'] == 'scneventsSocket':
                        s = e['osockStamp']
                        self.push(time + e['startTime'], 'emit', (nid, (s['name'], s['ordinal'])), nid)
                self.push(time + p['sectionDuration']['stu'], 'emit', (nid, (0, 0)), nid)
            elif typ == 'scnQuestNode':
                q = p['questNode']
                assert not johnny(q, self.aids), 'Johnny quest command reachable'
                qt = q['$type']
                if qt == 'questConditionNodeDefinition':
                    result = self.condition(nid, q['condition'])
                    if result is None:
                        self.held.append([time, nid, 'UNKNOWN_CONDITION'])
                    else:
                        self.emit(time, nid, (0, 0 if result else 1))
                    continue
                if qt == 'questPauseConditionNodeDefinition':
                    c = q['condition'].get('type', {})
                    if not isinstance(c, dict):
                        c = {}
                    if c.get('$type') == 'questRealtimeDelay_ConditionType':
                        delay = ((c['hours'] * 60 + c['minutes']) * 60 + c['seconds']) * 1000 + c['miliseconds']
                        self.push(time + delay, 'emit', (nid, (0, 0)), nid)
                    elif nid in self.ack:
                        self.emit(time, nid)
                    else:
                        self.held.append([time, nid, 'NATIVE_CONDITION_ACK_REQUIRED'])
                    continue
                if qt == 'questFactsDBManagerNodeDefinition':
                    t = q['type']
                    if t['$type'] == 'questSetVar_NodeType':
                        self.facts[t['factName']] = t['value'] if t['setExactValue'] else self.facts.get(t['factName'], 0) + t['value']
                        self.writes.append([time, t['factName'], self.facts[t['factName']]])
                if qt == 'questJournalNodeDefinition':
                    self.journal[q['type']['path']['realPath']] = mapping
                # Connected command acknowledgements are assumed in this model.
                for s in p['outputSockets']:
                    if s['destinations'] and p['osockMappings'][s['stamp']['ordinal']]['$value'] != 'CutSource':
                        self.emit(time, nid, (s['stamp']['name'], s['stamp']['ordinal']))
            elif typ == 'scnAndNode':
                self.and_inputs[nid].add(ordinal)
                if len(self.and_inputs[nid]) == p['numInSockets']:
                    self.emit(time, nid)
            elif typ == 'scnXorNode':
                if nid not in self.xor:
                    self.xor.add(nid)
                    self.emit(time, nid)
            elif typ in ('scnStartNode', 'scnHubNode', 'scnCutControlNode', 'scnDeletionMarkerNode', 'scnInterruptManagerNode'):
                for s in p['outputSockets']:
                    self.emit(time, nid, (s['stamp']['name'], s['stamp']['ordinal']))
            else:
                self.held.append([time, nid, 'UNMODELLED_' + typ])
        return self

    def result(self):
        return {'trace': self.trace, 'ends': self.ends, 'held': self.held, 'stopped': self.stopped,
                'facts': self.facts, 'writes': self.writes, 'journal': self.journal,
                'remaining_signals': len(self.queue)}


def load():
    rb = read(HERE / 'readback_04/manifest.json')
    return {r['depot'].split('\\')[-1]: normal(r['json']) for r in rb['resources']}


def main():
    target = HERE / 'flow_fixtures_04.json'
    assert not target.exists()
    models = load()
    fixtures = []
    checks = []
    def check(name, passed):
        assert passed, name
        checks.append({'name': name, 'pass': True})
    def record(name, signal):
        fixtures.append({'name': name, **signal.result()})

    garage = models['mq029_01a_garage.scene']
    s = Signals(garage).start('1').run()
    check('Garage inspection stays a player interaction', not s.ends and s.held == [[0, '14', 'PLAYER_CHOICE']])
    record('highwayman_inspect_requires_choice', s)
    s = Signals(garage, choices={'14': 0}).start('1').run()
    check('Bike clue inspected and tokens unblocked before terminating callback',
          [x[1] for x in s.trace][-4:] == ['25', '62', '32', '2'] and s.ends == [[2050, '2', 'Terminating']])
    record('highwayman_native_clue_and_cleanup', s)
    s = Signals(garage).start('48').run()
    check('Photo pickup retains native player section and callback', any(x[1] == '51' for x in s.trace)
          and s.ends == [[5333, '49', 'Terminating']])
    record('highwayman_photo_physical_sequence', s)
    body = models['mq029_01b_josie_body.scene']
    s = Signals(body).start('1').run()
    check('Body comment skipped to original nonterminating exit', s.ends == [[0, '2', 'NonTerminating']])
    record('highwayman_body_comment_skip', s)
    for chosen in (False, True):
        s = Signals(body, choices={'11': 0} if chosen else {}).start('9').run()
        check('Phone note player read ' + str(chosen), bool(s.ends) == chosen and
              (not chosen or [x[1] for x in s.trace] == ['9', '11', '16', '10']))
        record('highwayman_read_note_' + str(chosen), s)

    early = models['mq017_streetkid_01a_johnny.scene']
    for entry, nid in early['graphs']['scene']['entries'].items():
        s = Signals(early).start(nid).run()
        check('Small Man early entry skips whole exchange ' + entry, s.ends == [[0, '2', 'NonTerminating']]
              and len(s.trace) == 2)
        record('small_man_early_' + entry, s)
    small = models['mq017_streetkid_03_confront_thugs.scene']
    s = Signals(small, stop=['618']).start('205', 3).run()
    check('Opened truck retains V situation remark then Return to Kirk', s.stopped == [[4378, '618', 0, 1]]
          and not s.held and not s.writes and any(x[1] == '184' for x in s.trace))
    record('small_man_truck_to_return_to_kirk', s)
    s = Signals(small).start('1284', 1).run()
    check('Post-fight native callback reaches original successful quest completion', s.ends == [[0, '2', 'NonTerminating']]
          and list(s.journal.values()) == ['Succeeded'])
    record('small_man_post_fight_completion', s)
    for previous_comment in (0, 1):
        s = Signals(small, facts={'mq017_johnny_say_havefun': previous_comment}, stop=['248']).start('1927', 1).run()
        check('Native thugs handoff still needs return acknowledgement ' + str(previous_comment), not s.stopped)
        record('small_man_return_barrier_waits_' + str(previous_comment), s)
        s.emit(10, '638')
        s.run(until=100)
        check('Old Johnny presentation receipt cannot block native thugs handoff ' + str(previous_comment), s.stopped == [[10, '248', 0, 0]])
        record('small_man_return_barrier_ack_' + str(previous_comment), s)

    car = models['mq042_nomad_02_car_found.scene']
    s = Signals(car).start('99', 1).run()
    check('Car ending cannot auto-complete before driver mounts', not s.ends and s.held == [[0, '99', 'NATIVE_CONDITION_ACK_REQUIRED']])
    record('nomad_driver_mount_required', s)
    s = Signals(car, acknowledgements=['99'], stop=['104']).start('99', 1).run()
    check('Driver entry retains native two-second settle/UI/restriction setup', s.stopped == [[2000, '104', 0, 0]])
    record('nomad_driver_native_entry_ack', s)
    for taken in (0, 1):
        s = Signals(car, facts={'mq042_car_taken': taken}).start('104').run()
        check('Car buy/take ending skips Johnny and releases FPP restriction ' + str(taken),
              s.ends == [[100, '2', 'NonTerminating']] and any(x[1] == '1055' for x in s.trace)
              and not s.writes and not s.held)
        record('nomad_bought_or_taken_' + str(taken), s)
    s = Signals(car).start('992').run(until=6000)
    check('Leave car ending waits through V physical exit', not s.ends and bool(s.queue))
    record('nomad_leave_car_exit_not_finished', s)
    s.run(until=7000)
    check('Leave car completes after unmount/control transition and native Lana actions',
          s.ends == [[6544, '2', 'NonTerminating']] and all(any(x[1] == n for x in s.trace) for n in ['998', '930', '1000']))
    record('nomad_leave_car_exit_finished', s)

    for base, start, opts, expected_ms in [
        ('mq018_05_brooklyn.scene', '429', {}, 51),
        ('mq018_06_solar.scene', '25', {}, 1),
        ('mq018_07_protein.scene', '24', {'facts': {'mq018_debug': 0}}, 51),
    ]:
        s = Signals(models[base], **opts).start(start).run()
        check(base + ' no Johnny menu/wait before native stage exit', s.ends == [[expected_ms, '5', 'NonTerminating']] and not s.held)
        record(base + '_post_hack_comment_skip', s)
    # Device interactions remain explicit; no automatic hack on entering a scene.
    for base, choice in [('mq018_05_brooklyn.scene', '458'), ('mq018_06_solar.scene', '405'), ('mq018_07_protein.scene', '1479')]:
        s = Signals(models[base]).start(choice).run()
        check(base + ' physical router interaction still required', not s.ends and not s.writes and s.held == [[0, choice, 'PLAYER_CHOICE']])
        record(base + '_router_no_automatic_hack', s)

    fortune = models['mq018_02_fortuneteller.scene']
    s = Signals(fortune, stop=['64', '967']).start('1279').run()
    check('Before personal-link connection no manipulate menu or Call Nancy', not s.stopped
          and not s.writes and any(h[1] == '938' for h in s.held) and any(h[1] == '809' for h in s.held))
    record('fortune_personal_link_and_player_choice_required', s)
    for name, choice, option, ack, outcome in [
        ('leave_connected', '809', 0, '761', 'mq018_swedenborg_unchanged'),
        ('disable', '64', 0, '754', 'mq018_swedenborg_disabled'),
        ('troll', '64', 1, '757', 'mq018_swedenborg_trolled'),
    ]:
        s = Signals(fortune, choices={choice: option}, stop=['967']).start(choice).run(until=30000)
        check('Fortune ' + name + ' waits for bot native loop acknowledgement', not s.stopped
              and s.facts.get(outcome) == 1 and any(h[1] == ack for h in s.held))
        record('fortune_' + name + '_native_bot_ack_required', s)
        s = Signals(fortune, choices={choice: option}, acknowledgements=[ack], stop=['967']).start(choice).run(until=30000)
        check('Fortune ' + name + ' reaches Call Nancy through native outcome', len(s.stopped) == 1 and s.stopped[0][1] == '967'
              and s.facts.get(outcome) == 1 and sum(s.facts.get(n, 0) for n in
                  ['mq018_swedenborg_unchanged', 'mq018_swedenborg_disabled', 'mq018_swedenborg_trolled']) == 1)
        check('Fortune ' + name + ' has no Talk to Johnny journal writes',
              not any('johnny' in p or 'jonny' in p for p in s.journal))
        record('fortune_' + name + '_call_nancy', s)
    # Bot speech on the troll route is intentionally still about twenty seconds;
    # only Johnny's time is removed. Nancy's genuine completion is unchanged.
    call = models['mq018_03_call02.scene']['graphs']['scene']
    check('Nancy call choice and native successful objective/quest completion retained',
          call['nodes']['21']['type'] == 'scnChoiceNode' and ['7', '0:0', '43', '0:3'] in call['edges'])

    plan = read(HERE / 'input_04/plan.json')
    for base in ['mq040_02_trail_wife.scene', 'mq040_03_ripperdoc.scene']:
        edit = next(e for e in plan['edits'] if e['depot'].endswith(base))
        old = normal(edit['source']['json'])
        new = models[base]
        check(base + ' original investigation timing and interruption scenarios retained',
              old['metadata']['interruptionScenarios'] == new['metadata']['interruptionScenarios']
              and {n: x['payload']['sectionDuration'] for n, x in old['graphs']['scene']['nodes'].items() if x['type'] == 'scnSectionNode'}
              == {n: x['payload']['sectionDuration'] for n, x in new['graphs']['scene']['nodes'].items() if x['type'] == 'scnSectionNode'})
        fixtures.append({'name': base + '_native_pacing_and_interruptions', 'kind': 'SOURCE_CONTRACT', 'pass': True})
    cleanup = models['mq017_streetkid_00_main.questphase']['graphs']['root/4']
    check('Small Man cleanup retains both native AND barriers', cleanup['nodes']['7']['payload']['inputSocketCount'] ==
          cleanup['nodes']['17']['payload']['inputSocketCount'] == 2 and ['12', 'Out', '7', 'In1'] in cleanup['edges']
          and ['17', 'Out1', '7', 'In2'] in cleanup['edges'])
    check('Small Man cleanup still waits for both vehicles before native checkpoint',
          all(cleanup['nodes'][n]['type'] == 'questPauseConditionNodeDefinition' for n in ['2', '14'])
          and ['7', 'Out1', '8', 'In'] in cleanup['edges'] and ['8', 'Out', '1', 'In'] in cleanup['edges'])
    fixtures.append({'name': 'small_man_cleanup_native_barriers_and_checkpoint', 'kind': 'SOURCE_CONTRACT', 'pass': True})
    write(target, {'status': 'PASS_JB1_BOUNDED_FLOW_AND_NATIVE_GUARD_FIXTURES', 'plan_sha256': sha(HERE / 'input_04/plan.json'),
          'readback_sha256': sha(HERE / 'readback_04/manifest.json'), 'checks': checks, 'fixtures': fixtures,
          'fixture_count': len(fixtures), 'check_count': len(checks),
          'limits': 'Bounded authored-signal model. Explicit condition acknowledgements are fixture inputs, not simulated device/actor execution. Native quest commands acknowledge immediately. No in-game or saved-scene migration proof.',
          'game_writes': 0, 'save_writes': 0})
    print(json.dumps({'status': 'PASS', 'flow_and_source_fixtures': len(fixtures), 'checks': len(checks)}))


if __name__ == '__main__':
    main()
