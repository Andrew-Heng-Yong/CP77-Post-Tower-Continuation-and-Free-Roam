Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$plan=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'lipmap_plan_01.json') -Raw|ConvertFrom-Json -Depth 20
if($plan.status -cne '44_PRIVATE_SCENE_NATIVE_ENGLISH_LIPMAP_DONORS_PINNED' -or @($plan.rows).Count -ne 44){throw 'Wrong donor plan'}
$source=Join-Path $ws $plan.native_map_raw;if((Get-FileHash -LiteralPath $source).Hash -cne $plan.native_map_raw_sha256){throw 'Native map changed'}
$map=(Read-Cr2wFile $source).RootChunk
if($map.ScenePaths.Count -ne 3527 -or $map.SceneEntries.Count -ne 3527){throw 'Native map shape changed'}
$out=Join-Path $PSScriptRoot 'candidate_02';$depot='towercontinued\sidejob_repair_sr1\en-us.lipmap';$raw=Join-Path $out ('lipmap_source/'+$depot)
if(Test-Path -LiteralPath $raw){throw 'Use successor lipmap output'}
$private=[WolvenKit.RED4.Types.animLipsyncMapping]::new();$private.LanguageCodeName='en-us'
$covered=[Collections.Generic.List[object]]::new()
foreach($r in $plan.rows){
 $index=[int]$r.native_entry_index
 if($map.ScenePaths[$index].ToString() -cne $r.donor_hash.ToString()){throw ('Map donor index changed: '+$r.private)}
 $entry=$map.SceneEntries[$index].DeepCopy()
 $voices=@($entry.ActorVoiceTags|ForEach-Object {$_.ToString()})
 foreach($v in $r.required_voice_tags){if($v -cnotin $voices){throw ('Missing required voice: '+$r.private)}}
 if($entry.ActorVoiceTags.Count -ne $entry.AnimSets.Count){throw ('Voice/set count mismatch: '+$r.private)}
 $private.ScenePaths.Add([WolvenKit.RED4.Types.CUInt64]::op_Implicit([uint64]$r.private_hash))
 $private.SceneEntries.Add($entry)
 $covered.Add(@{scene=$r.private;hash=$r.private_hash;donor=$r.donor;voice_tags=$r.required_voice_tags})
}
if($private.ScenePaths.Count -ne 44 -or @($private.ScenePaths|ForEach-Object {$_.ToString()}|Sort-Object -Unique).Count -ne 44){throw 'Duplicate private scene hash'}
$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$private
Write-Cr2wFile $file $raw;$json=Join-Path $out 'lipmap_readback_01.json';Export-Cr2wJson (Read-Cr2wFile $raw) $json
$rb=Get-Content -LiteralPath $json -Raw|ConvertFrom-Json -Depth 100
if(@($rb.Data.RootChunk.scenePaths).Count -ne 44 -or @($rb.Data.RootChunk.sceneEntries).Count -ne 44){throw 'Readback count mismatch'}
$proof=[ordered]@{status='STAGED_ENGLISH_LIPMAP_44_NOT_INSTALLED';depot=$depot;source=$plan.native_map_raw;source_sha256=$plan.native_map_raw_sha256;raw=$raw;raw_sha256=(Get-FileHash -LiteralPath $raw).Hash;json_sha256=(Get-FileHash -LiteralPath $json).Hash;registrations=44;covered=$covered.ToArray();plan_sha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'lipmap_plan_01.json')).Hash;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'build_lipmap_01.json'),($proof|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
@{status=$proof.status;registrations=44;sha256=$proof.raw_sha256}|ConvertTo-Json
