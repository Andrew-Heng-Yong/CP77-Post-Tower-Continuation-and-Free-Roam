"""Independent Rogue restoration contract; never writes to the game directory."""
import copy
import itertools
import json
import re
from pathlib import Path
from audit_scene_actor_ids import audit_scene_actor_ids
from test_afterlife_booth_r6 import clean, read, sha, walk

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'research/afterlife_world'
OUT = BASE / 'interactions_r11/rogue'
PINNED = 'E408759C3B9B501D28AE397C485D739E665BEC5273E2DE54CF7FA7B6A2BD586D'
ROGUE_REF = '$/03_night_city/#PTFRAF1_RogueCommunity'
WORKSPOT_NODES = {140, 142, 144, 147, 154, 157}


def contract(scene):
    actor_audit = audit_scene_actor_ids(scene)
    assert actor_audit['actor_ids'] == [0, 1]
    assert len(scene['actors']) == len(scene['playerActors']) == 1
    actor = scene['actors'][0]
    assert actor['acquisitionPlan'] == 'community'
    assert actor['communityParams']['reference']['$value'] == ROGUE_REF
    assert actor['communityParams']['entryName']['$value'] == 'rogue'
    nodes = {n['nodeId']['id']: n for n in scene['sceneGraph']['graph']}
    assert len(nodes) == 47
    assert scene['entryPoints'][0]['name']['$value'] == 'in'
    assert scene['exitPoints'][0]['name']['$value'] == 'local_out'
    assert scene['entryPoints'][0]['nodeId']['id'] == 1
    assert scene['exitPoints'][0]['nodeId']['id'] == 2
    dests = lambda n: {d['nodeId']['id'] for s in n['outputSockets'] for d in s['destinations']}
    assert dests(nodes[1]) == {136, 235} and dests(nodes[235]) == {4}
    assert 268 in dests(nodes[4]) and 2 in dests(nodes[4])
    assert dests(nodes[276]) == {273}
    assert not ({228, 266, 271} & nodes.keys()), 'Phone branch leaked back'
    seen, pending = set(), [1]
    while pending:
        ident = pending.pop()
        if ident in seen:
            continue
        seen.add(ident)
        pending.extend(dests(nodes[ident]))
    assert seen == nodes.keys(), 'Dangling or unreachable local scene nodes'
    effects = [n for n in walk(scene) if n.get('$type') == 'scneventsVFXEvent']
    assert len(effects) == 2
    assert {e['action'] for e in effects} == {'Play', 'Break'}
    assert all(e['effectEntry']['effectName']['$value'] == 'eye_glow_gold' and
               e['performerId']['id'] == 1 for e in effects)
    assert any(n.get('$type') == 'scneventsVFXEvent' and n['action'] == 'Play' for n in walk(nodes[136]))
    assert any(n.get('$type') == 'scneventsVFXEvent' and n['action'] == 'Break' for n in walk(nodes[192]))
    allowed_quest_actions = {'questConditionNodeDefinition', 'questUseWorkspotNodeDefinition', 'questSceneManagerNodeDefinition'}
    quests = [n['questNode'] for n in nodes.values() if 'questNode' in n]
    assert {n['$type'] for n in quests} == allowed_quest_actions
    workspots = [n for n in quests if n['$type'] == 'questUseWorkspotNodeDefinition']
    assert {n['id'] for n in workspots} == WORKSPOT_NODES
    for n in workspots:
        assert n['entityReference']['reference']['$value'] == ROGUE_REF
        assert [v['$value'] for v in n['entityReference']['names']] == ['rogue']
        assert n['paramsV1']['playAtActorLocation'] == 1
        assert n['paramsV1']['isPlayer'] == 0
    animations = [e for n in nodes.values() for e in n.get('events', [])
                  if e['$type'] in ('scnPlaySkAnimEvent', 'scnChangeIdleAnimEvent')]
    assert len(animations) == 53
    assert all(e['performer']['id'] == 1 for e in animations), 'Only Rogue can receive local body/idle animations'
    assert all(n['mode'] == 'attachToActor' for n in nodes.values() if n['$type'] == 'scnChoiceNode')
    types = {n.get('$type') for n in walk(scene)}
    assert 'questSetVar_NodeType' not in types
    assert not any('Appearance' in t or 'Spawn' in t and t.startswith('quest') for t in types if t)
    for n in nodes.values():
        if n['$type'] == 'scnSectionNode':
            assert not any(e.get('executionTagFlags', 0) & 1 for e in n['events'])
    scenarios = scene['interruptionScenarios']
    assert len(scenarios) == 1 and scenarios[0]['id']['id'] == 0
    assert scenarios[0]['interruptConditions'][0]['params']['distance'] == 12
    assert scenarios[0]['returnConditions'][0]['params']['distance'] == 8
    return actor_audit


def permission_model(*, free_gameplay=True, healthy=True, exact=True, ready=True,
                     eligible=True, e_active=False, r_active=False, r_same=True,
                     npc_scene=False, player_scene=False, dialogue=False,
                     paired=False, distance=6.0, anchored=True, tokens_blocked=False,
                     rewind=False):
    """Contract model, not an engine simulation or replacement for native arbitration.

    player_scene is intentionally irrelevant: vanilla local owners can coexist.
    Actual dialogue is exclusive unless it is the already-owned exact Rogue pair.
    """
    qualified = healthy and exact and ready and eligible and anchored and distance <= 32
    actor_safe = (not r_active or r_same) and (not npc_scene or (r_active and r_same))
    dialogue_safe = not dialogue or (r_active and r_same and paired)
    tokens_safe = not tokens_blocked or (r_active and r_same)
    keep = free_gameplay and qualified and actor_safe and dialogue_safe and tokens_safe and not rewind and not e_active
    return dict(keep=keep, start=keep and not r_active and not dialogue and not tokens_blocked and distance <= 12)


def predicate_tests():
    cases = 0
    names = ('r_active', 'r_same', 'npc_scene', 'player_scene', 'dialogue', 'paired', 'e_active', 'tokens_blocked', 'rewind')
    for values in itertools.product((False, True), repeat=len(names)):
        state = dict(zip(names, values)); result = permission_model(**state)
        if state['dialogue']:
            assert not result['start']
            if not (state['r_active'] and state['r_same'] and state['paired']):
                assert not result['keep']
        if state['r_active']:
            assert not result['start']
            if not state['r_same']:
                assert not result['keep']
        if state['e_active']:
            assert not result['keep']
        if state['tokens_blocked']:
            assert not result['start']
            if not (state['r_active'] and state['r_same']):
                assert not result['keep']
        if state['rewind']:
            assert not result['keep']
        other = permission_model(**{**state, 'player_scene': not state['player_scene']})
        assert other == result, 'Passive scene presence is not exclusive ownership'
        cases += 1
    own = dict(r_active=True, r_same=True, npc_scene=True, player_scene=True,
               dialogue=True, paired=True)
    assert permission_model(**own)['keep'], 'Owned dialogue must not self-cancel'
    assert permission_model(**own, tokens_blocked=True)['keep'], 'Owned dialogue lock must not self-cancel'
    assert permission_model(player_scene=True)['start'], 'Passive scene must not deadlock start'
    for field in ('free_gameplay', 'healthy', 'exact', 'ready', 'eligible', 'anchored'):
        assert not permission_model(**{**own, field: False})['keep']; cases += 1
    # Existing game's PSM values: 1/2 are full/staged gameplay. Mounting,
    # workspots and rewind activity are unrelated player control and fail closed.
    for high, tier, mounted, workspot, rewind in itertools.product(range(7), range(7), (False, True), (False, True), (False, True)):
        free = high in (1, 2) and tier in (1, 2) and not mounted and not workspot and not rewind
        result = permission_model(**own, free_gameplay=free)
        assert result['keep'] == free
        assert not result['start']; cases += 1
    assert permission_model(distance=12)['start'] and not permission_model(distance=12.001)['start']
    assert permission_model(**own, distance=32)['keep'] and not permission_model(**own, distance=32.001)['keep']
    return cases + 4


def main():
    manifest = read(OUT / 'manifest.json')
    assert sha(manifest['source']) == sha(manifest['path']) == PINNED
    scene = clean(OUT / 'rogue.scene.json')
    prior = clean(BASE / 'interactions_r9/rogue.scene.json')
    assert scene == prior, 'Only reviewed R9 fixed local scene may be restored'
    audit = contract(scene)
    policy_cases = predicate_tests()
    runtime_path = ROOT / 'redscript/PTFR_Afterlife_Interactions_R8/AfterlifeInteractionsR8.reds'
    runtime = runtime_path.read_text(encoding='utf-8-sig')
    shared = runtime.split('private func PlayerGameplay(', 1)[1].split('public func Poll(', 1)[0]
    assert 'IsEntityInScene' not in shared and 'IsEntityInDialogue' not in shared
    assert all(token in shared for token in ('SceneTier', 'HighLevel', 'IsActorInWorkspot(player)', 'mount.parentId',
                                            '(high == 1 || high == 2)', '(tier == 1 || tier == 2)'))
    assert 'let playerFree = gameplay && !playerDialogue && !tokensBlocked && !rewind;' in runtime
    assert 'if rActive && rSame { ownDialogue = scene.AreEntitiesInDialogue(player.GetEntityID(), r.GetEntityID()); }' in runtime
    assert 'gameplay && (!playerDialogue || ownDialogue) && (!tokensBlocked || (rActive && rSame)) && !rewind' in runtime
    assert 'let rewind = scene.IsRewindableSectionActive();' in runtime
    assert shared.split('return ')[-1].strip().startswith('(high == 1 || high == 2) && (tier == 1 || tier == 2) && !inWorkspot && !mounted;')
    assert 'rStart = rAllowed && !rActive && playerFree && distance <= 144.0;' in runtime
    assert 'rActive && rSame && scene.IsEntityInScene(r.GetEntityID())' in runtime
    assert 'this.Set(q, n"PTFRAL8_RContinue", rAllowed);' in runtime
    assert 'this.Set(q, n"PTFRAL8_RAvailable", rStart);' in runtime
    assert 'if !rAllowed { this.ReleaseGlow(); }' in runtime
    assert 'if active { return true; }' in runtime
    assert '!scene.IsEntityInScene(npc.GetEntityID())' in runtime
    assert '(!inScene || (rActive' not in runtime
    assert not any(token in runtime for token in ('ScheduleAppearanceChange', 'ChangeAppearance', 'StartEffectEvent(', 'Spawn(', 'QueueEvent(', 'SendCommand('))
    # Source contract: only mod-owned permission writes; no forced story unlocks.
    assert all(name.startswith(('PTFRAL8_', 'PTFRAL10_')) for name in re.findall(r'this\.Set\(q, n"([^"]+)"', runtime))
    vanilla = clean(BASE / 'rogue_sources/json/base/quest/secondary_characters/default_dialogues/rogue_default.scene.json')
    vanilla_nodes = {n['nodeId']['id']: n for n in vanilla['sceneGraph']['graph']}
    comparisons = 0
    # Topic eligibility/history and localized dialog identifiers are copied,
    # not rewritten to force all topics regardless of the player's progress.
    for n in scene['sceneGraph']['graph']:
        original = vanilla_nodes[n['nodeId']['id']]
        if n['$type'] == 'scnChoiceNode':
            assert n['options'] == original['options']
            comparisons += len(n['options'])
        for ev in [e for e in n.get('events', []) if e['$type'] == 'scnDialogLineEvent']:
            source = next(e for e in original['events'] if e.get('id') == ev['id'])
            expected = copy.deepcopy(source)
            for item in walk(expected):
                if 'additionalSpeakers' in item:
                    item['additionalSpeakers']['speakers'] = [s for s in item['additionalSpeakers']['speakers'] if s['actorId']['id'] != 1]
                if item.get('$type') == 'scnActorId' and item['id'] == 2:
                    item['id'] = 1
                if item.get('$type') == 'scnPerformerId' and item['id'] == 513:
                    item['id'] = 257
            assert ev == expected
    # These retired candidate defects must fail this functionality gate.
    mutants = [('actual R8 sparse cast', clean(BASE / 'interactions_r8/rogue.scene.json')),
               ('actual R10 empty quarantine', clean(BASE / 'interactions_r10/scene_review/rogue_quarantine.scene.json'))]
    for kind, value in (('scnActorId', 2), ('scnPerformerId', 513), ('scnPerformerId', 769)):
        bad = copy.deepcopy(scene); bad['regressionProbe'] = {'$type': kind, 'id': value}
        mutants.append((f'stale {kind}={value}', bad))
    no_glow = copy.deepcopy(scene)
    for n in no_glow['sceneGraph']['graph']:
        if 'events' in n:
            n['events'] = [e for e in n['events'] if e['$type'] != 'scneventsVFXEvent']
    mutants.append(('missing glow', no_glow))
    wrong_actor = copy.deepcopy(scene)
    wrong_actor['actors'][0]['communityParams']['reference']['$value'] = '$/SpawnSet/#rogue'
    mutants.append(('original actor rebound', wrong_actor))
    for label, bad in mutants:
        try:
            contract(bad)
        except (AssertionError, ValueError, KeyError):
            continue
        raise AssertionError(f'Accepted unsafe/empty mutation: {label}')
    result = dict(status='PASS_R11_ROGUE_OFFLINE_NOT_LIVE', scene_sha256=PINNED,
                  actor_audit=audit, local_nodes=47, vanilla_topic_options_preserved=comparisons,
                  dialog_events_preserved=68, effect_events_preserved=2,
                  player_body_or_workspot_commands=0, runtime_predicate_model_cases=policy_cases,
                  integrated_runtime_sha256=sha(runtime_path), integrated_runtime_static_contract='PASS',
                  native_source_evidence={
                      'Rogue_local_owner': 'research/afterlife_world/interactions_r8/rogue_owner.json: root/node3/node14/node4, node6 <=32m (no global player-scene exclusion)',
                      'Claire_local_owner': 'research/b0_claire/validation/claire_service.questphase.json: #tr_claire_default plus <=10m, independent player acquisition',
                      'native_dialogue_API': 'research/finalboards_dismissal/decompiled/orphans.script:32248-32252 (pair dialogue vs entity dialogue vs entity scene)',
                      'gameplay_tiers': 'research/finalboards_dismissal/decompiled/orphans.script:3107-3108,6685-6694 (full/staged tiers1/2)',
                      'exact_runtime_proposal': 'research/afterlife_world/interactions_r11/rogue/runtime_policy.md'
                  },
                  unsafe_mutants_rejected=[label for label, _ in mutants],
                  appearance_changes=0, new_actor_identities=0, story_fact_writes=0,
                  limits=['No live dialogue, visual glow, release, reload or crash-stability proof.',
                          'Prior crowd attachment crash has no established corrupting writer.'])
    (OUT / 'tests.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
