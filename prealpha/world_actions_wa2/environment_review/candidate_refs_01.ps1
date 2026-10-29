$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$wk=Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package'
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot $wk
$inputPath=Join-Path $PSScriptRoot 'candidate_refs_input_01.json'
$inputData=Get-Content -LiteralPath $inputPath -Raw|ConvertFrom-Json -Depth 10
$hashes=@{};foreach($ref in $inputData.refs){$hashes[$ref]=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($ref).ToString()}
$out=Join-Path $PSScriptRoot 'candidate_refs_hashes_01.json';if(Test-Path -LiteralPath $out){throw 'Preserve proof'}
[IO.File]::WriteAllText($out,(@{status='CANDIDATE_NATIVE_ENGINE_NODEREF_HASHES';input_sha256=(Get-FileHash -LiteralPath $inputPath).Hash;hashes=$hashes;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 10)+"`n",[Text.UTF8Encoding]::new($false))
@{references=$hashes.Count}|ConvertTo-Json
