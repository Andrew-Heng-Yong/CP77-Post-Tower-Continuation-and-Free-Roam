$ErrorActionPreference='Stop'
$workspace=(Get-Location).Path
$out=Join-Path $PSScriptRoot 'verification_01/raw_02'
if(Test-Path -LiteralPath $out){throw 'Fresh raw-export directory required'}
New-Item -ItemType Directory -Path $out | Out-Null
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$inputs=@(
 @{key='before';path='prealpha/quest_restoration_qr5/candidate_01/archive_source/towercontinued/native_gigs_u9/sts_wat_nid_02_entry.questphase';hash='8FD5E94E8F0BBC5A815B24377101B7EEE176462E0E126D5179FAE79A23F1C636'},
 @{key='after';path='prealpha/quest_restoration_qr5/candidate_02/archive_source/towercontinued/native_gigs_u9/sts_wat_nid_02_entry.questphase';hash='AFB055A4E79D14472F29EC1883B9607FE1F18347F853EE4A482CAF483C7B4F87'},
 @{key='native';path='diagnostics/vanilla_parity_20261029_01/pass_02/raw/basegame_4_gamedata/base/open_world/street_stories/watson/northside_industrial_district/sts_wat_nid_02/phases/sts_wat_nid_02_bugfixing.questphase';hash='26361051DF260683A63E0096C42ACB405B2BCCC1770D5169DF664652B4E82D93'}
)
$rows=@()
foreach($item in $inputs){
 $raw=Join-Path $workspace $item.path
 if((Get-FileHash -LiteralPath $raw).Hash -cne $item.hash){throw ('Raw source hash changed: '+$item.key)}
 $json=Join-Path $out ($item.key+'.json')
 Export-Cr2wJson (Read-Cr2wFile $raw) $json
 if((Get-FileHash -LiteralPath $raw).Hash -cne $item.hash){throw 'Read-only raw hash drift'}
 $rows+=@{key=$item.key;raw=[IO.Path]::GetFullPath($raw);raw_sha256=$item.hash;json=[IO.Path]::GetFullPath($json);json_sha256=(Get-FileHash -LiteralPath $json).Hash;scope='Fresh read-only deserialize/export of existing raw; no serialization/build/game/save writes'}
}
$rows|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8
Write-Output ('Independently exported '+$rows.Count+' pinned raw resources')
