param([Parameter(Mandatory=$true)][string]$CandidateRoot,[Parameter(Mandatory=$true)][string]$OutputName)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
if($OutputName -notmatch '^[a-zA-Z0-9_]+$'){throw 'OutputName must be a simple validation subdirectory name'}
$candidate=[IO.Path]::GetFullPath($CandidateRoot)
$out=Join-Path $PSScriptRoot $OutputName
if(Test-Path -LiteralPath $out){throw 'Readback output exists; use successor'}
$c=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'checks_contract_01.json') -Raw|ConvertFrom-Json -Depth 50
foreach($p in $c.sources.PSObject.Properties){if((Get-FileHash -LiteralPath (Join-Path $ws $p.Name)).Hash -cne $p.Value){throw ('Independent input drift '+$p.Name)}}
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
New-Item -ItemType Directory -Path $out|Out-Null
$rows=[Collections.Generic.List[object]]::new()
foreach($depot in $c.depots){
 $raw=Join-Path (Join-Path $candidate 'archive_source') $depot
 if(!(Test-Path -LiteralPath $raw)){throw ('Missing candidate resource '+$depot)}
 $json=Join-Path $out ($depot+'.json');New-Item -ItemType Directory -Path (Split-Path $json -Parent) -Force|Out-Null
 Export-Cr2wJson (Read-Cr2wFile $raw) $json
 $rows.Add(@{depot=$depot;raw=$raw;raw_sha256=(Get-FileHash -LiteralPath $raw).Hash;json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash})
}
[IO.File]::WriteAllText((Join-Path $out 'inventory.json'),(@{candidate=$candidate;resources=$rows.ToArray()}|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
@{candidate=$candidate;decoded_resources=$rows.Count;game_writes=0}|ConvertTo-Json
