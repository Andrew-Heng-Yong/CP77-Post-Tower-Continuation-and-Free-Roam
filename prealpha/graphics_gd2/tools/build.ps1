param(
 [string]$WorkspaceRoot=(Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path,
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$BuildName='gd2_01'
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($BuildName -notmatch '^gd2_[0-9]{2}$'){throw 'BuildName must be gd2_NN'}
# Import definitions only. Never invoke an old installed builder main.
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$out=Join-Path $WorkspaceRoot "prealpha/graphics_gd2/build/$BuildName"
if(Test-Path -LiteralPath $out){throw 'Refusing to overwrite an existing/pinned GD2 candidate'}
$depot='ep1\fx\quest\q307\q307_falling_down_stairs.effect'
$originalPath=Join-Path $WorkspaceRoot ('research/graphics_investigation_20261013/gd2_stairs_effect/raw/'+$depot)
$originalHash='80F6C46772AAF07223EC4A26C2E9E873047CA927FB9466A86C778B740B61E03B'
$loopRuid='3485649208182173696'
function Json($value){return [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($value,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())}
function WriteJson($value,[string]$path){[IO.File]::WriteAllText($path,($value|ConvertTo-Json -Depth 40),[Text.UTF8Encoding]::new($false))}
function Sha([byte[]]$bytes){return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))}
$hashService=[WolvenKit.Common.Services.HashService]::new();$hashService.Load()
$reader=[WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
function Archive([string]$path){$a=$null;if($reader.ReadArchive($path,$hashService,[ref]$a).ToString() -ne 'NoError'){throw "Archive decode failed $path"};return $a}
if((Get-FileHash -LiteralPath $originalPath).Hash -ne $originalHash){throw 'Pinned original effect hash differs'}
$nativePath=Join-Path $GameRoot 'archive/pc/ep1/ep1_2_gamedata.archive'
$native=Archive $nativePath
$entry=@($native.Files.Values|Where-Object Name -eq $depot)
if($entry.Count -ne 1){throw 'Original native target not unique'}
$resourceKey=$entry[0].Key
$memory=[IO.MemoryStream]::new()
try{$entry[0].Extract($memory);if((Sha $memory.ToArray()) -ne $originalHash){throw 'Current native bytes differ from pinned original'}}finally{$memory.Dispose()}
$collisions=[Collections.Generic.List[object]]::new()
foreach($mod in @(Get-ChildItem -LiteralPath (Join-Path $GameRoot 'archive/pc/mod') -File -Filter '*.archive'|Sort-Object FullName)){
 $a=Archive $mod.FullName;$hits=@($a.Files.Values|Where-Object {$_.Key -eq $resourceKey -or $_.Name -eq $depot})
 $collisions.Add([ordered]@{name=$mod.Name;length=$mod.Length;resource_count=$a.Files.Count;target_hits=$hits.Count})
 if($hits.Count -ne 0){throw "Existing target override prevents isolated GD2 candidate: $($mod.Name)"}
}
$fx=Read-Cr2wFile $originalPath;$r=$fx.RootChunk
if($r.GetType().Name -ne 'worldEffect' -or $r.Length.ToString() -ne '20' -or $r.InputParameterNames.Count -ne 0){throw 'Native root identity changed'}
if($r.EffectLoops.Count -ne 1 -or $r.EffectLoops[0].StartTime.ToString() -ne '5' -or $r.EffectLoops[0].EndTime.ToString() -ne '5.5'){throw 'Expected one native5->5.5 loop'}
$types=@($r.Events|ForEach-Object {$_.Chunk.GetType().Name})
if(($types -join '|') -ne 'effectTrackItemVignette|effectTrackItemLoopMarker|effectTrackItemMotionBlurScale|effectTrackItemColorGrade|effectTrackItemChromaticAberration'){throw 'Native event set changed'}
if($r.Events[1].Chunk.Ruid.ToString() -ne $loopRuid -or $r.Events[1].Chunk.TimeBegin.ToString() -ne '5' -or $r.Events[1].Chunk.TimeDuration.ToString() -ne '0.5'){throw 'Loop marker identity changed'}
if($r.TrackRoot.Chunk.Tracks.Count -ne 5 -or (@($r.TrackRoot.Chunk.Tracks|ForEach-Object {$_.Chunk.Items.Count}) -join ',') -ne '1,1,1,1,1'){throw 'Five native track shells changed'}
foreach($pair in @(@(0,1),@(1,0),@(2,2),@(3,3),@(4,4))){if(-not [object]::ReferenceEquals($r.TrackRoot.Chunk.Tracks[$pair[0]].Chunk.Items[0].Chunk,$r.Events[$pair[1]].Chunk)){throw 'Native event/track handle mapping changed'}}
$visuals=@{};foreach($i in @(0,2,3,4)){$visuals[$r.Events[$i].Chunk.Ruid.ToString()]=Json $r.Events[$i].Chunk}
$source=Join-Path $out 'source';$originalCopy=Join-Path $out ('original/'+$depot);$patched=Join-Path $source $depot
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $originalCopy)|Out-Null
Copy-Item -LiteralPath $originalPath -Destination $originalCopy
Export-Cr2wJson $fx (Join-Path $out 'original.json')
# The only allowed semantic delta removes the hold-loop scheduler, not the
# authored visual recovery curves, duration, scene events or compiled binding.
$r.EffectLoops.Clear()
$r.TrackRoot.Chunk.Tracks[0].Chunk.Items.Clear()
$r.Events.RemoveAt(1)
$expected=Json $r
Write-Cr2wFile $fx $patched
$rb=Read-Cr2wFile $patched
if((Json $rb.RootChunk) -cne $expected){throw 'CR2W readback differs from expected bounded candidate'}
if($rb.RootChunk.EffectLoops.Count -ne 0 -or $rb.RootChunk.Events.Count -ne 4 -or $rb.RootChunk.TrackRoot.Chunk.Tracks.Count -ne 5){throw 'Candidate root counts changed'}
if((@($rb.RootChunk.TrackRoot.Chunk.Tracks|ForEach-Object {$_.Chunk.Items.Count}) -join ',') -ne '0,1,1,1,1'){throw 'Candidate native track mapping changed'}
for($i=0;$i -lt 4;$i++){
 $event=$rb.RootChunk.Events[$i].Chunk;$ruid=$event.Ruid.ToString()
 if(-not $visuals.ContainsKey($ruid) -or (Json $event) -cne $visuals[$ruid]){throw 'A retained visual event changed'}
 if(-not [object]::ReferenceEquals($rb.RootChunk.TrackRoot.Chunk.Tracks[$i+1].Chunk.Items[0].Chunk,$event)){throw 'Retained visual track does not refer to matching event'}
}
$norm=Read-Cr2wFile $originalCopy
$norm.RootChunk.EffectLoops.Clear();$norm.RootChunk.Events.RemoveAt(1);$norm.RootChunk.TrackRoot.Chunk.Tracks[0].Chunk.Items.Clear()
if((Json $norm.RootChunk) -cne (Json $rb.RootChunk)){throw 'Complete root comparison found an unintended delta'}
if($fx.MetaData.Version -ne $rb.MetaData.Version -or $fx.MetaData.BuildVersion -ne $rb.MetaData.BuildVersion){throw 'CR2W metadata changed'}
Export-Cr2wJson $rb (Join-Path $out 'patched.json')
$files=@(Get-ChildItem -LiteralPath $source -Recurse -File)
if($files.Count -ne 1 -or [IO.Path]::GetRelativePath($source,$files[0].FullName) -ne $depot){throw 'Non-target resource in pack source'}
$archiveName='TowerContinued_StairsFX_GD2.archive';$archivePath=Join-Path $out $archiveName
$stream=[IO.File]::Create($archivePath)
try{$writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService,[WolvenKit.SerilogWrapper]::new());if(-not $writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Archive packing failed'}}finally{$stream.Dispose()}
$packed=Archive $archivePath
if($packed.Files.Count -ne 1 -or $packed.Files.Values[0].Name -ne $depot -or $packed.Files.Values[0].Key -ne $resourceKey){throw 'Packed resource count/depot/key mismatch'}
$patchedHash=(Get-FileHash -LiteralPath $patched).Hash
$memory=[IO.MemoryStream]::new()
try{
 $packed.Files.Values[0].Extract($memory)
 if((Sha $memory.ToArray()) -ne $patchedHash){throw 'Packed bytes differ from patched resource'}
 $memory.Position=0;$cr=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($memory);$packedFx=$null
 if($cr.ReadFile([ref]$packedFx,$true).ToString() -ne 'NoError' -or (Json $packedFx.RootChunk) -cne $expected){throw 'Packed semantic CR2W readback differs'}
}finally{$memory.Dispose()}
if((Get-FileHash -LiteralPath $originalPath).Hash -ne $originalHash){throw 'Original source changed during build'}
WriteJson @($collisions) (Join-Path $out 'collision_audit.json')
$manifest=[ordered]@{
 status='BUILT_GD2_CANDIDATE';created_utc=[DateTime]::UtcNow.ToString('o')
 archive=$archiveName;archive_sha256=(Get-FileHash -LiteralPath $archivePath).Hash;archive_bytes=(Get-Item -LiteralPath $archivePath).Length
 resource_count=1;resource_depot=$depot;resource_key=$resourceKey.ToString();original_sha256=$originalHash;patched_sha256=$patchedHash
 builder_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;native_archive=$nativePath;source_relative=('source/'+$depot);original_relative=('original/'+$depot)
 change='Remove only the5.0->5.5-second EffectLoops item, LoopMarker RUID3485649208182173696, and its first-track item reference; retain20-second duration, allfive track shells, and allfour visual event payloads/curves.'
 collision_audit='collision_audit.json';scanned_installed_archives=$collisions.Count;includes_scripts=$false;includes_xl=$false;game_save_cache_settings_writes=$false
 scene_binding_changes=0;compiled_scene_resources=0;scene_lifecycle_proof='Separate lifecycle audit required; this build demonstrates only the stated effect-local delta.'
 limitations='Finite authored recovery is a candidate intervention, not proof the original loop caused the reported fault or that the engine consumes this override. No renderer-state measurements or game launch.'
 live_verified=$false;shader_cause_confirmed=$false
}
WriteJson $manifest (Join-Path $out 'build.json')
$checks=@(
 'Pinned original extracted SHA matches original source.'
 'Current official archive resource is unique and matches pinned SHA.'
 'All installed mod archive keys/depot names checked with no target collision.'
 'Native worldEffect type,20-second length and zero input parameters pinned.'
 'Native EffectLoops contains exactly5.0->5.5.'
 'Native five event types/order pinned.'
 'LoopMarker RUID and5.0/0.5 start/duration pinned.'
 'Native five single-item track shells pinned.'
 'Native track event reference identities pinned.'
 'Patched CR2W full root matches expected semantic delta.'
 'Patched effect has zero loops and exactlyfour visual events.'
 'Allfive native tracks retained, item counts0,1,1,1,1.'
 'Allfour retained visual payloads/curves/IDs semantically identical independently.'
 'Allfour retained track item references still target correct visual events.'
 'Independent normalized original full-root comparison permits only three exact removals.'
 'CR2W Version and BuildVersion retained.'
 'Source directory has exactly one intended resource.'
 'Packed archive reopens with one intended depot and original key.'
 'Packed resource byte SHA equals patched source.'
 'Packed extracted CR2W decodes and full semantic root matches expected.'
 'Original extracted source remains byte-identical after build.'
)
WriteJson ([ordered]@{status='PASS_NOT_LIVE';build_sha256=(Get-FileHash -LiteralPath (Join-Path $out 'build.json')).Hash;check_count=$checks.Count;checks=$checks;limitations=@('No game launch or engine effect-execution proof','No scene-binding or camera changes','No runtime/save/cache/settings/driver writes','No root-cause claim')}) (Join-Path $out 'tests.json')
[pscustomobject]$manifest | ConvertTo-Json -Depth 10
