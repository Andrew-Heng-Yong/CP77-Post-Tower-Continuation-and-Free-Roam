Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$rows=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'prefab_hashes_01.json') -Raw|ConvertFrom-Json
$r=@($rows|Where-Object id -eq 1246)[0]
$short=$r.ref.Split(';')[0]
$a=[WolvenKit.RED4.Types.NodeRef]::CalculateHash([string]$r.ref)
$b=[WolvenKit.RED4.Types.NodeRef]::CalculateHash([string]$short)
$proof=@{status=$(if($a -eq $b){'PASS_EXACT_ENGINE_HASH_ALIAS'}else{'FAIL_DIFFERENT_ENGINE_HASH'});id=1246;authored=$r.ref;canonical=$short;authored_hash=$a.ToString();canonical_hash=$b.ToString();resource=$r.resource}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'alias1246_01.json'),($proof|ConvertTo-Json -Depth 10)+"`n",[Text.UTF8Encoding]::new($false))
$proof|ConvertTo-Json
