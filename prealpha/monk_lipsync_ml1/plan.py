"""Pin the original lip-sync rows for the first monk's two private scenes."""

import hashlib
import json
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
WS = HERE.parents[1]
BASE_MAP = r'base\localization\en-us.lipmap'
PRIVATE_MAP = r'towercontinued\sidejob_repair_sr1\en-us.lipmap'
NATIVE_DIR = r'base\quest\minor_quests\mq032\scenes'
PRIVATE_DIR = r'towercontinued\johnny_batch3\mq032'
STEMS = ('mq032_01_hook', 'mq032_03_epilogue')
MONK_VOICE = '1624173162010259604'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest().upper()


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


def key(depot):
    digest = 14695981039346656037
    for byte in depot.lower().replace('/', '\\').encode('utf-8'):
        digest = ((digest ^ byte) * 1099511628211) & ((1 << 64) - 1)
    return str(digest)


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def root(row):
    assert sha(row['raw']) == row['sha256'] and sha(row['json']) == row['json_sha256'], row['depot']
    return read(row['json'])['Data']['RootChunk']


def english_configs(rows):
    result = []
    for row in rows:
        assert sha(row['path']) == sha(row['copy']) == row['sha256']
        text = Path(row['copy']).read_text(encoding='utf-8-sig')
        blocks = re.findall(r'(?m)^  lipmaps:\s*\n((?:^    [^\n]*\n?)+)', text)
        assert len(blocks) == 1, row['path']
        paths = re.findall(r'(?m)^    en-us: +([^\n]+)$', blocks[0])
        assert len(paths) == 1 and paths[0].endswith('.lipmap'), row['path']
        result.append({'config': row['path'], 'sha256': row['sha256'], 'depot': paths[0]})
    assert sum(row['depot'] == PRIVATE_MAP for row in result) == 1
    return result


def main():
    capture_path = HERE / 'capture_01/providers.json'
    capture = read(capture_path)
    assert capture['epoch'] == 'JB3' and capture['core_and_dependency_hashes'] == 77
    manifest = read(capture['installed_manifest'])
    assert sha(capture['installed_manifest']) == capture['installed_manifest_sha256']
    settings = Path(manifest['save_root']).parents[2] / 'AppData/Local/CD Projekt Red/Cyberpunk 2077/UserSettings.json'
    languages = {row.get('value') for row in walk(read(settings)) if row.get('name') == 'VoiceOver'}
    assert languages == {'en-us'}, languages

    providers = {row['depot']: row for row in capture['providers']}
    assert len(providers) == len(capture['providers']), 'Conflicting scene or map provider'
    native = root(providers[BASE_MAP])
    original = root(providers[PRIVATE_MAP])
    for mapping in (native, original):
        assert mapping['$type'] == 'animLipsyncMapping'
        assert mapping['languageCodeName']['$value'] == 'en-us'
        assert len(mapping['scenePaths']) == len(mapping['sceneEntries']) == len(set(mapping['scenePaths']))
    assert len(original['scenePaths']) == 48
    assert Path(providers[BASE_MAP]['archive']).name == 'lang_en_voice.archive'
    assert Path(providers[PRIVATE_MAP]['archive']).name == 'zzzz_PTFR_Combined.archive'

    prior_audit = WS / 'diagnostics/quest_animation_parity_20261110_01/scene_audit/scene_route_results.json'
    route_evidence = read(prior_audit)
    assert route_evidence['archive_sha256'] == capture['archive_sha256']
    additions = []
    for stem in STEMS:
        native_scene = NATIVE_DIR + '\\' + stem + '.scene'
        private_scene = PRIVATE_DIR + '\\' + stem + '.scene'
        native_row, private_row = providers[native_scene], providers[private_scene]
        native_key, private_key = key(native_scene), key(private_scene)
        assert native_row['key'] == native_key and private_row['key'] == private_key
        assert private_key not in {str(n) for n in native['scenePaths'] + original['scenePaths']}
        index, = (i for i, scene_key in enumerate(native['scenePaths']) if str(scene_key) == native_key)
        donor = native['sceneEntries'][index]
        voice_index, = (i for i, voice in enumerate(donor['actorVoiceTags']) if str(voice) == MONK_VOICE)
        assert len(donor['actorVoiceTags']) == len(donor['animSets']) == len(set(donor['actorVoiceTags']))
        old_scene, new_scene = root(native_row), root(private_row)
        actor, = (a for a in new_scene['actors'] if str(a['voicetagId']['id']) == MONK_VOICE)
        stock_actor, = (a for a in old_scene['actors'] if str(a['voicetagId']['id']) == MONK_VOICE)
        assert actor == stock_actor, 'First monk actor binding differs from stock'
        assert actor['communityParams']['reference']['$value'] == '#mq032_com_monk_cyberware'
        used = {event['screenplayLineId']['id'] for event in walk(new_scene['sceneGraph']) if event.get('$type') == 'scnDialogLineEvent'}
        lines = [line for line in new_scene['screenplayStore']['lines']
                 if line['speaker']['id'] == actor['actorId']['id'] and line['itemId']['id'] in used]
        stock_lines = {line['itemId']['id']: line for line in old_scene['screenplayStore']['lines']}
        assert lines and all(line == stock_lines[line['itemId']['id']] for line in lines)
        refs = [asset['DepotPath']['$value'] for asset in donor['animSets']]
        assert all(path.startswith(r'base\localization\en-us\lipsync\base\quest\minor_quests\mq032\scenes' + '\\') for path in refs)
        callers = [r for r in route_evidence['direct_callers'] if r['scene'] == private_scene]
        assert callers and route_evidence['scene_results'][private_scene]['installed']['sha256'] == private_row['sha256']
        additions.append({'native': native_row, 'private': private_row, 'native_map_index': index,
                          'donor': donor, 'monk_actor_name': actor['actorName'], 'monk_voice_tag': MONK_VOICE,
                          'monk_anim_set': refs[voice_index], 'donor_asset_depots': refs,
                          'retained_monologue_lines': [{'line': line['itemId']['id'],
                              'locstring': line['locstringId']['ruid'],
                              'male_clip': line['maleLipsyncAnimationName']['$value'],
                              'female_clip': line['femaleLipsyncAnimationName']['$value']} for line in lines],
                          'caller_sites': callers})

    configs = english_configs(capture['localization_configs'])
    result = {'epoch': 'ML1', 'baseline': 'JB3', 'installed_manifest': capture['installed_manifest'],
              'installed_manifest_sha256': capture['installed_manifest_sha256'], 'archive_sha256': capture['archive_sha256'],
              'capture': str(capture_path), 'capture_sha256': sha(capture_path),
              'voice_over': 'en-us', 'english_configs': configs, 'existing_map': providers[PRIVATE_MAP],
              'native_map': providers[BASE_MAP], 'additions': additions,
              'asset_depots': sorted({p for row in additions for p in row['donor_asset_depots']}),
              'other_custom_maps': sorted({r['depot'] for r in configs if r['depot'] != PRIVATE_MAP}),
              'route_evidence': str(prior_audit), 'route_evidence_sha256': sha(prior_audit)}
    write_new(HERE / 'plan.json', result)
    print(json.dumps({'scene_rows': len(additions), 'retained_monk_lines': [len(row['retained_monologue_lines']) for row in additions],
                      'asset_depots': len(result['asset_depots']), 'other_english_maps': len(result['other_custom_maps'])}))


if __name__ == '__main__':
    main()
