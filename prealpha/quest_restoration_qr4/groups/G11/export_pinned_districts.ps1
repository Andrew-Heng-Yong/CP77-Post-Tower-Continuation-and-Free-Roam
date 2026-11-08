param([Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$workspace=(Get-Location).Path
if(Test-Path -LiteralPath $Output){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $Output|Out-Null
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$inputs=@(
 @{raw='research/gig_restoration/expanded_sources/raw/base/open_world/street_stories/city_center/downtown/sts_cct_downtown.questphase';hash='4E9EA778A2F972B9C2CE16B7929736EB12876020FCA3749F196DD1530A64753C'},
 @{raw='research/gig_restoration/fresh_candidates/local_sources/raw/base/open_world/street_stories/city_center/corpo_plaza/sts_cct_corpo_plaza.questphase';hash='622EF36D30D8B9FB44C739E742E9C4807E06EEC264B138F708797A04ECD93559'}
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
