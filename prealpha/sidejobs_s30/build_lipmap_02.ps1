Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$base=Join-Path $ws 'prealpha/full_consolidation_v1/candidate_01/archive_source/towercontinued/sidejob_repair_sr1/en-us.lipmap'
$native=Join-Path $ws 'research/sidejobs_s29/stefan_lipmap_01/lang_en_voice/raw/base/localization/en-us.lipmap'
$existing=(Read-Cr2wFile $base).RootChunk
$official=(Read-Cr2wFile $native).RootChunk
if($existing.ScenePaths.Count -ne 44 -or $official.ScenePaths.Count -ne 3527){throw 'Lipmap baseline changed'}
$meta=Get-Content (Join-Path $PSScriptRoot 'prepared_02/manifest.json') -Raw|ConvertFrom-Json -Depth 100
$rows=[Collections.Generic.List[object]]::new()
foreach($r in $meta.resources){
 if(!$r.native.EndsWith('.scene')){continue}
 $donor=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($r.native)
 $private=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($r.private)
 $idx=-1
 for($i=0;$i -lt $official.ScenePaths.Count;$i++){if($official.ScenePaths[$i].ToString() -ceq $donor.ToString()){$idx=$i;break}}
 if($idx -lt 0){
  if($r.native -cne 'base\open_world\mini_world_stories\watson\mws_wat_08\scenes\mws_wat_08.scene'){throw ('Native donor missing '+$r.native)}
  continue
 }
 if(@($existing.ScenePaths|Where-Object {$_.ToString() -ceq $private.ToString()}).Count){throw ('Private scene already mapped '+$r.private)}
 $entry=$official.SceneEntries[$idx].DeepCopy()
 if($entry.ActorVoiceTags.Count -ne $entry.AnimSets.Count){throw ('Donor voice/set mismatch '+$r.native)}
 $existing.ScenePaths.Add([WolvenKit.RED4.Types.CUInt64]::op_Implicit([uint64]$private))
 $existing.SceneEntries.Add($entry)
 $rows.Add(@{native=$r.native;private=$r.private;native_hash=$donor.ToString();private_hash=$private.ToString();voices=@($entry.ActorVoiceTags|ForEach-Object {$_.ToString()})})
}
if($rows.Count -ne 4 -or $existing.ScenePaths.Count -ne 48){throw 'Expected four appended private scenes'}
$depot='towercontinued\sidejob_repair_sr1\en-us.lipmap'
$out=Join-Path $PSScriptRoot ('serialized_02/source/'+$depot)
if(Test-Path $out){throw 'Successor required'}
New-Item -ItemType Directory (Split-Path $out -Parent) -Force|Out-Null
$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$existing;Write-Cr2wFile $file $out
$rb=Join-Path $PSScriptRoot 'serialized_02/lipmap_readback.json';Export-Cr2wJson (Read-Cr2wFile $out) $rb
$test=Get-Content $rb -Raw|ConvertFrom-Json -Depth 100
if(@($test.Data.RootChunk.scenePaths).Count -ne 48){throw 'Lipmap readback mismatch'}
$proof=@{status='STAGED_NOT_INSTALLED';depot=$depot;raw_sha256=(Get-FileHash $out).Hash;source_sha256=(Get-FileHash $base).Hash;native_sha256=(Get-FileHash $native).Hash;rows=$rows.ToArray()}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'serialized_02/lipmap_manifest.json'),($proof|ConvertTo-Json -Depth 50),[Text.UTF8Encoding]::new($false))
@{entries=$existing.ScenePaths.Count;appended=$rows.Count;sha256=$proof.raw_sha256}|ConvertTo-Json
