"""Reuse BA1's independently verified lifecycle for exact native sibling loops."""
from pathlib import Path

H = Path(__file__).resolve().parent
W = H.parents[1]
s = (W / 'prealpha/bottle_actions_ba1/build_owner_01.ps1').read_text(encoding='utf-8-sig')
s = "param([Parameter(Mandatory=$true)][ValidateSet(172,173)][int]$Group)\n" + s
s = s.replace("$out=Join-Path $PSScriptRoot 'candidate_01'", """$out=Join-Path $PSScriptRoot 'candidate_01'
$config=@{172=@{owner=7;controller=64;ready=65;alias='#ce_pac_cvi_105_com'};173=@{owner=8;controller=61;ready=62;alias='#ce_pac_cvi_106_com'}}[$Group]
$manifest=Get-Content -LiteralPath (Join-Path $ws 'prealpha/world_workspots_w2/manifest_03.json') -Raw|ConvertFrom-Json -Depth 80
$record=@($manifest.groups|Where-Object id -eq $Group)
if($record.Count -ne 1 -or $record[0].community_refs.Count -ne 1){throw 'Exact W3 identity missing'}
$prefix="PTFRWA2_${Group}_";$support="PTFRWW2_${Group}_"
$resource="towercontinued/world_actions_wa2/group_${Group}_action.questphase"
"""
)
s = s.replace("$dest=Join-Path $out 'source/towercontinued/bottle_actions_ba1/bottle_action_owner.questphase'", "$dest=Join-Path $out ('source/'+$resource)")
s = s.replace('Get-QuestNode $district.PhaseGraph.Chunk 14', 'Get-QuestNode $district.PhaseGraph.Chunk $config.owner')
s = s.replace('Get-QuestNode $original.PhaseGraph.Chunk 61', 'Get-QuestNode $original.PhaseGraph.Chunk $config.controller')
s = s.replace('Get-QuestNode $original.PhaseGraph.Chunk 62', 'Get-QuestNode $original.PhaseGraph.Chunk $config.ready')
start = s.index("$community='")
end = s.index('\n', start)
s = s[:start] + '$community=[string]$record[0].community_refs[0]' + s[end:]
s = s.replace("'#ce_pac_cvi_112_com'", '$config.alias')
for suffix in ['Claimed','Ready','Entered','Active','Suspended']:
    s = s.replace("'PTFRBA1_" + suffix + "'", "($prefix+'" + suffix + "')")
for suffix in ['Claimed','Entered','Hold']:
    s = s.replace('PTFRWW2_179_' + suffix + '=', "($support+'" + suffix + "')=")
s = s.replace('Link $loop 3 Out 61 In1', 'Link $loop 3 Out $config.controller In1')
s = s.replace('Link $loop 61 Out1 4', 'Link $loop $config.controller Out1 4')
s = s.replace('.PhaseGraph.Chunk 61).PhaseGraph.Chunk', '.PhaseGraph.Chunk $config.controller).PhaseGraph.Chunk')
s = s.replace("'owner_readback_01.json'", '"owner_${Group}_readback_01.json"')
s = s.replace("'owner_proof_01.json'", '"owner_${Group}_proof_01.json"')
s = s.replace("status='BA1_OWNER_SERIALIZED';resource='towercontinued/bottle_actions_ba1/bottle_action_owner.questphase'", "status='WA2_OWNER_SERIALIZED';group=$Group;resource=$resource")
s = s.replace("scope='Exact group179 action controller; no prefab/spawn/native-fact writes'", "scope='Exact W3 sibling shooting controller; no prefab/spawn/native-fact writes'")
assert 'PTFRBA1' not in s and 'PTFRWW2_179' not in s
assert s.count('$config.controller') == 4
dest = H / 'build_nested_shooting_01.ps1'
assert not dest.exists(), 'Preserve existing builder'
dest.write_text(s, encoding='utf-8')
print(dest)
