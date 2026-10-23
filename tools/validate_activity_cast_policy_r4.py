"""Offline candidate policy validation only; never an engine admission adapter."""
import json
from catalog_gig_rollout_r2 import ROOT, read, sha, normalize

PATH = ROOT / 'research/gig_restoration/lore_whitelists_v4_cast.json'
VARIANTS = ('two_year_aware', 'ignore_two_year_gap')
LIVE = {'live_scene', 'live_call', 'live_message',
        'optional_scene', 'optional_call', 'optional_message'}
ARCHIVAL = {'historical_mention', 'archival_recording', 'prerequisite_only'}
BLOCKED = {'panam', 'panampalmer', 'kerry', 'kerryeurodyne', 'judy', 'judyalvarez'}
JOHNNY = {'johnny', 'johnnysilverhand'}


def cast_verdict(participants, johnny_role, coverage_complete):
    """Classify supplied audit evidence, not infer absence from titles/substrings.

    Callers must supply actual participation and reviewed narrative centrality.
    No verdict here authorizes runtime restoration or proves invisible actors work.
    """
    if type(coverage_complete) is not bool or type(participants) is not list:
        return 'DEFER_UNKNOWN'
    if not isinstance(johnny_role, str) or johnny_role not in ('none', 'supporting', 'central', 'unknown'):
        return 'DEFER_UNKNOWN'
    saw_johnny = False
    malformed = False
    for entry in participants:
        if (not isinstance(entry, dict) or
                not isinstance(entry.get('character'), str) or
                not entry['character'].strip() or
                not isinstance(entry.get('kind'), str) or
                entry.get('kind') not in LIVE | ARCHIVAL):
            malformed = True
            continue
        actor = normalize(entry['character'])
        if entry['kind'] in LIVE:
            if actor in BLOCKED:
                return 'EXCLUDED_PARTICIPANT'
            saw_johnny |= actor in JOHNNY
    if johnny_role == 'central':
        return 'EXCLUDED_JOHNNY_CENTRAL'
    if malformed or not coverage_complete or johnny_role == 'unknown':
        return 'DEFER_UNKNOWN'
    if saw_johnny and johnny_role == 'none':
        return 'DEFER_CONTRADICTORY_AUDIT'
    if johnny_role == 'supporting':
        return 'CANDIDATE_VOICE_ONLY_ADAPTATION_REQUIRED'
    return 'CANDIDATE_CAST_COMPATIBLE_NOT_RUNTIME_ADMISSION'


def validate(data):
    assert data['schema'] == 4
    policy = data['cast_policy']
    assert policy['id'] == 'tower_supporting_johnny_voice_only'
    assert policy['revision'] == 1
    assert policy['johnny_voice'] is True
    assert policy['johnny_visible_appearance'] is False
    assert policy['johnny_central_jobs'] is False
    assert policy['johnny_takeover_or_relic_abilities'] is False
    assert policy['excluded_live_characters'] == ['Panam Palmer', 'Kerry Eurodyne', 'Judy Alvarez']
    assert set(policy['participating_kinds']) == LIVE
    assert set(policy['nonparticipating_kinds']) == ARCHIVAL
    assert policy['unknown_cast'] == 'DEFER_NOT_ADMIT'
    assert data['supersedes'] == 'research/gig_restoration/lore_whitelists_v3_broad.json'
    old = read(ROOT / data['supersedes'])
    changes = data['changes_from_v3']
    assert changes['gigs_added_to_both'] == ['Playing for Keeps']
    assert changes['side_jobs_added_to_both'] == ['No Easy Way Out', 'Spellbound', "The Prophet's Song"]
    assert changes['side_jobs_removed_from_both_if_present'] == ['Dazed and Confused', "I'll Fly Away"]
    excluded = {e['title'] for e in data['still_excluded_examples']}
    assert {'Dazed and Confused', "I'll Fly Away", 'Balls to the Wall', "Chippin' In",
            'Blistering Love', 'Fool on the Hill', 'The Gift', 'Motorbreath',
            'I Really Want to Stay at Your House'} <= excluded
    for variant in VARIANTS:
        gigs = data[variant]['gigs']
        sides = data[variant]['side_and_minor_jobs']
        assert gigs == old[variant]['gigs'] + changes['gigs_added_to_both']
        assert sides == [t for t in old[variant]['side_and_minor_jobs']
                         if t not in changes['side_jobs_removed_from_both_if_present']] + changes['side_jobs_added_to_both']
        assert len(gigs) == len(set(gigs))
        assert len(sides) == len(set(sides))
        assert not (set(gigs + sides) & excluded)
        assert data['counts'][variant] == {
            'gigs': len(gigs), 'side_and_minor_jobs': len(sides), 'total': len(gigs) + len(sides)}
    for category in ('gigs', 'side_and_minor_jobs'):
        assert set(data['two_year_aware'][category]) <= set(data['ignore_two_year_gap'][category])
    runtime = data['runtime_status']
    assert runtime['voice_only_adapter_implemented'] is False
    assert runtime['completed_replay_implemented'] is False
    assert all(runtime[k] == 0 for k in ('new_adapters', 'installed_changes', 'game_writes', 'save_writes'))
    assert runtime['installed_history_definition'] == 'UNCHANGED_V3_71_GIGS_57_SIDE_JOBS'
    assert len(data['protected_inputs']) == 8
    for pin in data['protected_inputs']:
        path = (ROOT / pin['path']).resolve()
        assert path.is_relative_to(ROOT.resolve())
        assert sha(path) == pin['sha256'], (pin['path'], 'protected historical/runtime source changed')
    return data['counts']


def main():
    data = read(PATH)
    print(json.dumps({'status': 'OFFLINE_POLICY_VALIDATION_PASS_NOT_RUNTIME_PROOF',
                      'counts': validate(data), 'new_adapters': 0, 'installed_changes': 0}))


if __name__ == '__main__':
    main()
