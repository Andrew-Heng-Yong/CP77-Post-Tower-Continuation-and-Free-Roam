"""Controls for the prepared-entry model, with no game or save fixtures."""
from copy import deepcopy
from dataclasses import replace

from prototype import Fixture, bind_seam, enclosure, plan, run_trace


def check_cases(models, volumes):
    checks = []

    def check(name, passed):
        if not passed:
            raise AssertionError(name)
        checks.append(name)

    complete = Fixture(same_instance=True, retired_original_owner=True, support_verified=True,
                       approach_pending=True, other_startup_state_verified=True, car='applied', courier='consumed')
    complete_plan = plan(complete)
    complete_trace = run_trace(complete_plan['cursors'],
                               ['courier_inside', 'vehicle_spawned', 'approach_qualified_call'], 1)
    check('Completed setup keeps only the approach wait', complete_plan['cursors'] == ['openworld/root/2:3.In'])
    check('Completed courier is not incremented twice', complete_trace['force_after'] == 1)
    check('Completed vehicle setup has no new dispatch', not any('dispatch' in item for item in complete_trace['ordered_trace']))
    check('Native prebrief scene input reached after discovery', complete_trace['ordered_trace'] == [
        'root/2:3.Out', 'root/2:4.DiscoveredPhase', 'root/2:1.Terminating', 'root:2.Out1',
        'root:3.In1', 'root:4.In1', 'root/4:153', 'root/4:154.True', 'root/4:129.Start 0',
    ])

    pending_plan = plan(replace(complete, courier='pending', car='waiting_at_102'))
    pending_trace = run_trace(pending_plan['cursors'], ['courier_inside', 'courier_inside',
                              'vehicle_spawned', 'vehicle_spawned', 'approach_qualified_message'], 0)
    trace = pending_trace['ordered_trace']
    check('Pending courier increments exactly once before briefing', pending_trace['force_after'] == 1 and
          trace.index('root/2:15.increment') < trace.index('root/2:4.DiscoveredPhase') and trace.count('root/2:15.increment') == 1)
    check('Pending vehicle wait emits both authored commands once',
          [i for i in trace if 'dispatch' in i] == ['gameplay/root/1:103.dispatch', 'gameplay/root/1:104.dispatch'])
    check('Blocked phone route retains native message', trace[-2:] == ['root/4:154.False', 'root/4:45.Active'])
    late = run_trace(pending_plan['cursors'], ['approach_qualified_call', 'courier_inside'], 0)
    check('Terminating approach closes the courier window', late['force_after'] == 0 and not late['courier_wait_remaining'])
    check('Approach does not terminate the parallel car wait', late['car_wait_remaining'])
    check('Prior submission with unknown application defers', plan(replace(complete, car='dispatched_unknown'))['status'] == 'DEFERRED')
    for evidence in ('same_instance', 'retired_original_owner', 'support_verified', 'approach_pending', 'other_startup_state_verified'):
        denied = plan(replace(complete, **{evidence: False}))
        check(f'Missing {evidence} prevents any cursor plan', denied['missing'] == [evidence] and denied['cursors'] == [])
    check('Unknown courier history prevents any cursor plan', plan(replace(complete, courier='unknown'))['cursors'] == [])
    check('Prepared scalar projection alone has no cursor plan', plan(Fixture())['cursors'] == [])

    # These mutants produce concrete wrong outcomes on the same ordered inputs.
    courier_cursor = 'openworld/root/2:14.In'
    skipped = run_trace([i for i in pending_plan['cursors'] if i != courier_cursor], ['courier_inside'], 0)
    repeated = run_trace([*complete_plan['cursors'], courier_cursor], ['courier_inside'], 1)
    check('Blanket courier skip loses a pending native increment', skipped['force_after'] == 0 and pending_trace['force_after'] == 1)
    check('Blanket courier rearm duplicates a consumed increment', repeated['force_after'] == 2 and complete_trace['force_after'] == 1)

    for mutation in ('drop_courier_edge', 'nonterminating_output', 'exact_courier_write', 'relaxed_approach_predicate'):
        changed = deepcopy(models)
        start = changed['openworld']['graphs']['root/2']
        if mutation == 'drop_courier_edge':
            start['edges'].remove(['14', 'Out', '15', 'In'])
        elif mutation == 'nonterminating_output':
            start['nodes']['1']['payload']['type'] = 'NonTerminating'
        elif mutation == 'exact_courier_write':
            start['nodes']['15']['writes'][0]['setExactValue'] = 1
        else:
            start['nodes']['3']['payload']['condition']['operation'] = 'OR'
        try:
            bind_seam(changed)
        except ValueError:
            checks.append(f'Reject altered source: {mutation}')
        else:
            raise AssertionError(f'Accepted altered source: {mutation}')
    shifted = deepcopy(volumes)
    x, y, z = shifted['approach']['position']
    shifted['approach']['position'] = (x + 100, y, z)
    check('A moved approach trigger invalidates geometric containment', not enclosure(shifted)['strict_enclosure'])
    return checks, {'completed': complete_trace, 'pending': pending_trace, 'approach_before_courier_callback': late,
                    'incorrect_skip': skipped, 'incorrect_rearm': repeated}
