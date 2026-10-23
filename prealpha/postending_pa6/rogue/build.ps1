param(
 [string]$WorkspaceRoot=(Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path,
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$BuildName='rogue_01'
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($BuildName -notmatch '^rogue_[0-9]{2}$'){throw 'Build name must be rogue_NN'}
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$out=Join-Path $PSScriptRoot ('build/'+$BuildName)
if(Test-Path -LiteralPath $out){throw 'Never overwrite an existing candidate'}
$depot='towercontinued\afterlife_interactions_r8\rogue.scene'
$source=Join-Path $WorkspaceRoot ('prealpha/build/20261013T021845834Z/source/'+$depot)
$originalSha='E408759C3B9B501D28AE397C485D739E665BEC5273E2DE54CF7FA7B6A2BD586D'
$mainSha='6B9AAE7DAE4AD9613A7F8ABA7FB3CB2B05D7CD85DAAA3A5FE82B198324316DE9'
$archiveName='0_TowerContinued_RogueLipsync_PA6.archive'
$mods=Join-Path $GameRoot 'archive/pc/mod'
if(Test-Path -LiteralPath (Join-Path $mods 'modlist.txt')){throw 'Explicit archive order needs separate audit; not changed here'}
if((Get-FileHash -LiteralPath $source).Hash -ne $originalSha){throw 'Pinned scene source changed'}
function Json($v){return [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($v,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())}
function WriteJson($v,[string]$p){[IO.File]::WriteAllText($p,($v|ConvertTo-Json -Depth 70),[Text.UTF8Encoding]::new($false))}
function Sha([byte[]]$b){return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($b))}
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load()
$reader=[WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
function Archive([string]$p){$a=$null;if($reader.ReadArchive($p,$hash,[ref]$a).ToString() -ne 'NoError'){throw "Archive decode $p"};return $a}
$main=Archive (Join-Path $mods 'TowerContinued_PreAlpha.archive')
$originalEntries=@($main.Files.Values|Where-Object {$_.Name -eq $depot})
if($originalEntries.Count -ne 1){throw 'Expected one named baseline member'}
$key=$originalEntries[0].Key
$collisions=[Collections.Generic.List[object]]::new();$hitsTotal=0
foreach($f in @(Get-ChildItem -LiteralPath $mods -File -Filter '*.archive')){
 $beforeSha=(Get-FileHash -LiteralPath $f.FullName).Hash
 $a=Archive $f.FullName;$hits=@($a.Files.Values|Where-Object {$_.Key -eq $key -or $_.Name -eq $depot})
 if((Get-FileHash -LiteralPath $f.FullName).Hash -ne $beforeSha){throw 'Archive changed during collision audit'}
 $collisions.Add([ordered]@{archive=$f.Name;sha256=$beforeSha;target_hits=$hits.Count;resource_count=$a.Files.Count})
 if($hits.Count -gt 0){
  $hitsTotal+=$hits.Count
  if($f.Name -cne 'TowerContinued_PreAlpha.archive' -or $beforeSha -ne $mainSha -or $hits.Count -ne 1){throw 'Unexpected overriding archive'}
  $m=[IO.MemoryStream]::new();try{$hits[0].Extract($m);if((Sha $m.ToArray()) -ne $originalSha){throw 'Installed original resource differs'}}finally{$m.Dispose()}
 }
}
if($hitsTotal -ne 1 -or [StringComparer]::Ordinal.Compare($archiveName,'TowerContinued_PreAlpha.archive') -ge 0){throw 'Expected exact baseline collision and earlier ASCII patch name'}
$file=Read-Cr2wFile $source;$r=$file.RootChunk;$refs=$r.ResouresReferences.LipsyncAnimSets
if($refs.Count -ne 3 -or (Json $refs[0]) -cne (Json $refs[1])){throw 'Expected duplicate unused Rogue references'}
if($r.Actors.Count -ne 1 -or $r.PlayerActors.Count -ne 1 -or $r.Actors[0].ActorId.Id.ToString() -ne '0' -or $r.PlayerActors[0].ActorId.Id.ToString() -ne '1'){throw 'Actor layout differs'}
if($r.Actors[0].LipsyncAnimSet.Id.ToString() -ne '0' -or $r.PlayerActors[0].LipsyncAnimSet.Id.ToString() -ne '2'){throw 'Unexpected lipsync users'}
if($r.SceneGraph.Chunk.Graph.Count -ne 47){throw 'Scene graph differs'}
if($refs[0].AsyncRefLipsyncAnimSet.DepotPath.ToString() -ne 'base\quest\secondary_characters\default_dialogues\lipsync\en\rogue_default\rogue.anims' -or $refs[2].AsyncRefLipsyncAnimSet.DepotPath.ToString() -ne 'base\quest\secondary_characters\default_dialogues\lipsync\en\rogue_default\v.anims'){throw 'Native resource paths differ'}
New-Item -ItemType Directory -Force -Path $out | Out-Null
Export-Cr2wJson $file (Join-Path $out 'original.json')
$preservedGraph=Json $r.SceneGraph.Chunk
# The removed actor was the hologram. Its identical lipsync ref was retained
# by R9/R11 even though only physical Rogue and V remain. The live table in the
# crash has two slots while V asks for slot2. Keep the same two unique resources.
$refs.RemoveAt(1)
$r.PlayerActors[0].LipsyncAnimSet.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]1)
$expected=Json $r
$patch=Join-Path $out ('source/'+$depot)
Write-Cr2wFile $file $patch
$rb=Read-Cr2wFile $patch
if((Json $rb.RootChunk) -cne $expected -or (Json $rb.RootChunk.SceneGraph.Chunk) -cne $preservedGraph){throw 'Serialization modified scene payload'}
Export-Cr2wJson $rb (Join-Path $out 'patched.json')
$archivePath=Join-Path $out $archiveName
$stream=[IO.File]::Create($archivePath)
try{$writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hash,[WolvenKit.SerilogWrapper]::new());if(-not $writer.WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=Archive $archivePath
if($packed.Files.Count -ne 1 -or $packed.Files.Values[0].Key -ne $key){throw 'Packed resource identity differs'}
$m=[IO.MemoryStream]::new()
try{
 $packed.Files.Values[0].Extract($m)
 if((Sha $m.ToArray()) -ne (Get-FileHash -LiteralPath $patch).Hash){throw 'Packed bytes differ'}
 $m.Position=0;$cr=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($m);$read=$null
 if($cr.ReadFile([ref]$read,$true).ToString() -ne 'NoError' -or (Json $read.RootChunk) -cne $expected){throw 'Packed semantic readback differs'}
}finally{$m.Dispose()}
if((Get-FileHash -LiteralPath $source).Hash -ne $originalSha){throw 'Source changed'}
WriteJson @($collisions) (Join-Path $out 'collision_audit.json')
WriteJson ([ordered]@{
 status='BUILT_PA6_ROGUE_CANDIDATE_NOT_LIVE';archive=$archiveName;archive_sha256=(Get-FileHash -LiteralPath $archivePath).Hash
 original_sha256=$originalSha;patched_sha256=(Get-FileHash -LiteralPath $patch).Hash;resource_count=1;depot=$depot;key=$key.ToString()
 source_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;baseline_archive_sha256=$mainSha;installed_archives_scanned=$collisions.Count
 expected_baseline_hits=1;explicit_modlist_absent=$true;patch_name_ascii_before_baseline=$true
 load_order_reference='https://github.com/CDPR-Modding-Documentation/Cyberpunk-Modding-Docs/blob/main/for-mod-users/users-modding-cyberpunk-2077/load-order.md'
 semantic_delta='Remove unused duplicate lipsync ref index1 (Rogue), rebase V player lipsync2->1. Same Rogue and V paths; all47nodes/choices/actors/events/owners unchanged.'
 limitation='Exact failing out-of-bounds index is addressed; live loaded resource selection, dialogue and stability require test. Duplicate compaction mechanism not independently instrumented.'
 runtime_save_settings_writes=$false
}) (Join-Path $out 'build.json')
Write-Output "BUILD_PASS $out"
