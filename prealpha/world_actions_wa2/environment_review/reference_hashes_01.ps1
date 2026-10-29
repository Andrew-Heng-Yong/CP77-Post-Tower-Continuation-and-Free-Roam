$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$inputs=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'inputs_01.json') -Raw|ConvertFrom-Json -Depth 30
$hashes=@{}
foreach($g in $inputs.groups){foreach($ref in @($g.context_refs)+@($g.community_refs)){
 $hashes[$ref]=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($ref).ToString()
 if($g.id -eq 289){$actual=$ref.Replace('/rancho_coronado/','/#rancho_coronado/');$hashes[$actual]=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($actual).ToString()}
}}
$out=Join-Path $PSScriptRoot 'reference_hashes_01.json';if(Test-Path -LiteralPath $out){throw 'Preserve evidence'}
[IO.File]::WriteAllText($out,(@{status='NATIVE_NODEREF_HASH_CALCULATION';hashes=$hashes;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 6)+"`n",[Text.UTF8Encoding]::new($false))
@{refs=$hashes.Count}|ConvertTo-Json
