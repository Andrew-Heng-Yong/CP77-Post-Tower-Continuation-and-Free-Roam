param([string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$val = Join-Path $WorkspaceRoot 'research\b0_afterlife_mirror\validation_v7'
$ownerText = Get-Content -LiteralPath (Join-Path $val 'afterlife_mirror_owner.questphase.json') -Raw
$sceneText = Get-Content -LiteralPath (Join-Path $val 'afterlife_mirror_scene.scene.json') -Raw
$owner = $ownerText | ConvertFrom-Json -Depth 100
$scene = $sceneText | ConvertFrom-Json -Depth 100
$fullRef = '$/03_night_city/c_watson/little_china/#loc_q103_afterlife/#loc_q103_afterlife_openworld/#mirror_scene_afterlife/#mirror_tr_afterlife'

$nodes = $owner.Data.RootChunk.graph.Data.nodes
if (@($nodes).Count -ne 10) { throw 'Owner node count changed' }
$wait = @($nodes | Where-Object { $_.Data.id -eq 2 })
if ($wait.Count -ne 1) { throw 'Owner wait node missing' }
$entry = @($wait[0].Data.condition.Data.conditions | Where-Object { $_.Data.'$type' -eq 'questTriggerCondition' })
if ($entry.Count -ne 1 -or $entry[0].Data.type -ne 'IsInside' -or
    $entry[0].Data.triggerAreaRef.'$value' -ne $fullRef) {
    throw 'Entry is not the full native Afterlife trigger'
}
if ($ownerText.Contains('PTFRB0ALM_Near') -or $sceneText.Contains('PTFRB0ALM_Near')) {
    throw 'Native trigger candidate still depends on the proximity fact'
}

$sceneNode = @($nodes | Where-Object { $_.Data.id -eq 4 })
if ($sceneNode.Count -ne 1 -or
    $sceneNode[0].Data.sceneFile.DepotPath.'$value' -ne 'towercontinued\b0_afterlife_mirror\afterlife_mirror_scene.scene' -or
    $sceneNode[0].Data.sceneLocation.nodeRef.'$value' -ne '#mirror_sm_scene_afterlife') {
    throw 'Expected single mod-owned Afterlife scene missing'
}
$exit = @($scene.Data.RootChunk.sceneGraph.Data.graph | Where-Object { $_.Data.nodeId.id -eq 4398 })
if ($exit.Count -ne 1 -or $exit[0].Data.questNode.Data.condition.Data.type -ne 'IsOutside' -or
    $exit[0].Data.questNode.Data.condition.Data.triggerAreaRef.'$value' -ne $fullRef) {
    throw 'Scene does not exit through the full native Afterlife trigger'
}
$delay = @($nodes | Where-Object { $_.Data.id -eq 7 })
if ($delay.Count -ne 1 -or $delay[0].Data.condition.Data.type.Data.seconds -ne 1) {
    throw 'Vanilla one-second rearm missing'
}
$manifest = Get-Content -LiteralPath (Join-Path $val 'build_manifest.json') -Raw | ConvertFrom-Json
if (@($manifest.resources).Count -ne 2 -or @($manifest.vanilla_replacements).Count -ne 0) {
    throw 'Package scope is not exactly two additive resources'
}
Write-Output 'Afterlife v7 static checks passed: absolute native entry/exit trigger, one scene, 1s rearm, no Near fact or vanilla replacement.'
