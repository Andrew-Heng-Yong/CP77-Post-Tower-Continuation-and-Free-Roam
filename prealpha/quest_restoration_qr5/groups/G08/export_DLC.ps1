param([Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$workspace=(Get-Location).Path
if(Test-Path -LiteralPath $Output){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $Output|Out-Null
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$inputs=@(
 @{raw='research/gig_restoration/rollout_r2/native_sources/raw/base/open_world/street_stories/street_stories_dlc.questphase';hash='6B1595A14CD24F4C6191C3641A72F1C069EB528C38DA96B0DE0A5A2EA2BC7D75'}
)
$rows=@();$idx=0
foreach($row in $inputs){
 $raw=Join-Path $workspace $row.raw
 if((Get-FileHash -LiteralPath $raw).Hash -cne $row.hash){throw 'Pinned vanilla raw changed'}
 $json=Join-Path $Output ('district_'+$idx+'.json')
 Export-Cr2wJson (Read-Cr2wFile $raw) $json
 $rows+=@{raw=$row.raw;raw_sha256=$row.hash;json=(Join-Path $workspace $json);json_sha256=(Get-FileHash -LiteralPath $json).Hash;scope='Read existing raw, export fresh JSON only; no game, resource, build, or serialization writes'}
 $idx+=1
}
$rows|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $Output 'manifest.json') -Encoding utf8
Write-Output ('Exported '+$rows.Count+' pinned vanilla district resources')
