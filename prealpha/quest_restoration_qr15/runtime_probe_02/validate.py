"""Offline controls for the one-shot absolute-car getter; never calls the game."""
from pathlib import Path
import hashlib, json, re, sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
sys.path.insert(0, str(WORK / 'prealpha/quest_restoration_qr9/worker_b/tooling'))
from lupa.luajit21 import LuaRuntime


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


MOCK = r'''
lines={}; calls={world=0,spawner=0,arrays=0,writes=0}; lastref=nil
print=function(s) lines[#lines+1]=tostring(s) end
local function deny(_,k) calls.writes=calls.writes+1; error("UNEXPECTED_API:"..tostring(k)) end
local function ro(t) return setmetatable(t,{__index=deny}) end
local p=ro({IsAttached=function()return not cfg.detached end})
local function arr(n) calls.arrays=calls.arrays+1; local a={}; for i=1,n do a[i]=i end; return a end
local s=ro({IsInitialized=function()return cfg.initialized==true end,IsActive=function()return cfg.active==true end,GetSpawnedEntityIDs=function()return arr(cfg.spawned or 0)end,GetRestoredEntityIDs=function()return arr(cfg.restored or 0)end,GetReservedEntityIDs=function()if cfg.arrayerror then error("ARRAY_READ_FAILED")end;return arr(cfg.reserved or 0)end})
local w=ro({IsReady=function()return not cfg.notready end,GetPopulationSpawner=function(_,r)calls.spawner=calls.spawner+1;lastref=r;if cfg.lookup_error then error("LOOKUP_FAILED")end;if cfg.unresolved then return nil end;return s end})
Game=ro({GetPlayer=function()if cfg.noplayer then return nil end;return p end,GetWorldStateSystem=function()calls.world=calls.world+1;if cfg.noapi then error("NO_WORLD_API")end;return w end,CreateNodeRef=function(r)return r end})
'''


def run(chunk, cfg):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().cfg = lua.table_from(cfg)
    lua.execute(MOCK)
    lua.execute(chunk)
    return list(lua.globals().lines.values()), dict(lua.globals().calls.items()), lua.globals().lastref


def main():
    output = HERE / 'validation_01.json'
    assert not output.exists(), 'Fresh output required'
    chunk = (HERE / 'car.lua').read_text()
    command = (HERE / 'car.command.txt').read_text().strip()
    binding_file = HERE.parent / 'runtime_probe_01/car_binding_review_01/binding_02/result.json'
    binding = read(binding_file)
    checks = []

    def ck(name, condition):
        checks.append({'name': name, 'pass': bool(condition)})
        assert condition, name

    allowed = {'GetPlayer', 'IsAttached', 'GetWorldStateSystem', 'IsReady', 'GetPopulationSpawner', 'CreateNodeRef',
               'IsInitialized', 'IsActive', 'GetSpawnedEntityIDs', 'GetRestoredEntityIDs', 'GetReservedEntityIDs'}
    used = set(re.findall(r'(?:Game\.|:)([A-Za-z_][A-Za-z_0-9]*)\s*\(', chunk))
    ck('strict_readonly_api_allowlist', used <= allowed)
    ck('no_writer_timer_hook_or_file_io', not re.search(r'\b(SetFact|Request|ExecuteNode|register|Observe|Override|io\.|os\.|dofile|loadfile|loadstring)\b', chunk))
    ck('single_line_copy_command', len(command.splitlines()) == 1)
    ck('typed_vehicle_binding', binding['car_binding']['type'] == 'worldPopulationSpawnerNode' and binding['car_definition']['isVehicle'] == 1)
    ck('pinned_native_sector', sha(binding['source']['raw']) == binding['source']['sha256'])
    ck('pinned_sector_export', sha(binding['source']['json']) == binding['source']['json_sha256'])
    ck('pinned_current_setup_layout', sha(binding['layout_source']['path']) == binding['layout_source']['sha256'])
    expected_ref = binding['car_binding']['full_ref']
    ck('absolute_reference_not_original_short_reference', expected_ref.startswith('$/') and expected_ref != '#sts_ep1_03_gunfight_broken_car')
    lines, calls, ref = run(command, {'initialized': True, 'active': True, 'spawned': 1, 'restored': 2, 'reserved': 3})
    ck('exact_extracted_node_reference_used', ref == expected_ref)
    ck('distinct_independent_array_counts', lines == ['[JF02] car initialized=true active=true spawned=1 restored=2 reserved=3'] and calls['arrays'] == 3 and calls['spawner'] == 1)
    ck('multiline_and_copy_command_match', run(chunk, {'spawned': 4}) == run(command, {'spawned': 4}))
    for cfg in [{'noplayer': True}, {'detached': True}]:
        lines, calls, _ = run(command, cfg)
        ck('unattached_player_does_not_touch_world_' + next(iter(cfg)), calls['world'] == calls['spawner'] == calls['arrays'] == 0 and lines == ['[JF02] LOAD_SAVE_FIRST'])
    lines, calls, _ = run(command, {'notready': True})
    ck('detached_world_does_not_touch_spawner', calls['spawner'] == calls['arrays'] == 0 and lines == ['[JF02] WORLD_NOT_READY'])
    lines, calls, _ = run(command, {'unresolved': True})
    ck('unresolved_not_reported_as_zero_inactive_or_missing_actor', lines == ['[JF02] ABSOLUTE_CAR_UNRESOLVED'] and calls['arrays'] == 0)
    for error in ['noapi', 'lookup_error', 'arrayerror']:
        lines, calls, _ = run(command, {error: True})
        ck(error + '_visible_without_fabricated_result', len(lines) == 1 and lines[0].startswith('[JF02] ERROR:') and not any('spawned=0' in x for x in lines))
    lines, calls, _ = run(command, {})
    ck('real_false_and_empty_values_are_retained', lines == ['[JF02] car initialized=false active=false spawned=0 restored=0 reserved=0'] and calls['writes'] == 0)

    game = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
    glob = game / 'red4ext/plugins/Codeware/Scripts/Codeware.Global.reds'
    script = glob.read_text(encoding='utf-8-sig')
    ck('installed_native_array_getter_declarations', all(re.search(r'func\s+' + n + r'\(', script) for n in ['GetSpawnedEntityIDs', 'GetRestoredEntityIDs', 'GetReservedEntityIDs']))
    wrapper = WORK / 'research/framework_pr63_01/codeware/src/App/World/PopulationSpawnerWrapper.cpp'
    wrapper_source = wrapper.read_text()
    ck('array_getters_match_local_readonly_implementation', all('PopulationSpawnerWrapper::' + n + '() const' in wrapper_source for n in ['GetSpawnedEntityIDs', 'GetRestoredEntityIDs', 'GetReservedEntityIDs']))
    result = {
        'status': 'OFFLINE_CONTROLS_PASS_NOT_LIVE_DELIVERY', 'checks': checks,
        'inputs': [{'path': str(p), 'sha256': sha(p)} for p in [HERE/'car.lua', HERE/'car.command.txt', binding_file, glob, wrapper]],
        'command_bytes': len(command.encode()), 'game_calls': 0, 'save_writes': 0, 'runtime_installation_changes': 0,
        'limits': 'Mocks verify Lua control flow, refusal/error paths and reader allowlist; they do not validate native delivery, spawner liveness, visual destruction, door state or native-owner retirement.'
    }
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'checks': len(checks), 'command_bytes': result['command_bytes']}))


if __name__ == '__main__':
    main()
