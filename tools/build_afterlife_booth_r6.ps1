param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\afterlife_world\booth_r6'
$out=Join-Path $WorkspaceRoot 'build\AfterlifeBoothR6'
$source=Join-Path $out 'source'
New-Item -ItemType Directory -Force $audit,$source|Out-Null
$r3=Get-Content (Join-Path $WorkspaceRoot 'research\afterlife_world\idles_r3\manifest.json') -Raw|ConvertFrom-Json -Depth 30
$hashes=[ordered]@{}
function ReadChecked([string]$p){$script:hashes[$p]=(Get-FileHash -LiteralPath $p).Hash;return Read-Cr2wFile $p}
# Preserve all R3 resource identities and readiness/controller/registry bytes.
# Only four resource references in the private AISpot sector are changed.
foreach($relative in $r3.resources){
 $from=Join-Path $r3.source_root $relative;$to=Join-Path $source $relative
 $hashes[$from]=(Get-FileHash -LiteralPath $from).Hash
 New-Item -ItemType Directory -Force (Split-Path $to)|Out-Null
 Copy-Item -LiteralPath $from -Destination $to
}
$spotPath=Join-Path $source 'towercontinued\afterlife_idles_r3\spots.streamingsector'
$spots=Read-Cr2wFile $spotPath
$edits=[Collections.Generic.List[object]]::new();$resources=[Collections.Generic.List[string]]::new()
foreach($relative in $r3.resources){$resources.Add($relative)}
for($i=0;$i -lt 4;$i++){
 $entry=$r3.entries[$i]
 $original=Join-Path $WorkspaceRoot ('research\afterlife_world\idles_r3\entry_sources\raw\'+$entry.animation)
 $f=ReadChecked $original
 $tree=$f.RootChunk.WorkspotTree.Chunk
 $root=$tree.RootEntry.Chunk
 $idleParent=$root
 if($entry.entry -eq 'merc_03'){
  $male=@($root.List|Where-Object {$_.Chunk.GetType().Name -eq 'workConditionalSequence' -and $_.Chunk.Id.Id.ToString() -eq '18'})
  if($male.Count -ne 1 -or $male[0].Chunk.ConditionList[0].Chunk.Rig.DepotPath.ToString() -ne 'base\characters\base_entities\man_base\man_base.rig'){throw 'Male bodytype branch mismatch'}
  $idleParent=$male[0].Chunk
 }
 $target=@($idleParent.List|Where-Object {$_.Chunk.GetType().Name -eq 'workSequence' -and $_.Chunk.Id.Id.ToString() -eq '2'})
 if($target.Count -ne 1 -or $target[0].Chunk.LoopInfinitely.ToString() -ne 'False'){throw "Unexpected vanilla idle branch: $($entry.entry) matches=$($target.Count)"}
 $target[0].Chunk.LoopInfinitely=$true
 $relative='towercontinued\afterlife_booth_r6\merc_'+($i+1).ToString('00')+'.workspot'
 Write-Cr2wFile $f (Join-Path $source $relative)
 Export-Cr2wJson $f (Join-Path $audit ('merc_'+($i+1).ToString('00')+'.workspot.json'))
 $spot=$spots.RootChunk.Nodes[$i].Chunk.Spot.Chunk
 $type=$spot.GetType().GetProperty('Resource').PropertyType
 $spot.Resource=[Activator]::CreateInstance($type,[object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($relative)))
 $resources.Add($relative)
 $edits.Add(@{entry=$entry.entry;source=$original;source_resource=$entry.animation;private_resource=$relative;sequence_id=2;idle=$target[0].Chunk.IdleAnim.ToString();changed_property='loopInfinitely';before=$false;after=$true})
}
Write-Cr2wFile $spots $spotPath
Export-Cr2wJson $spots (Join-Path $audit 'spots.streamingsector.json')
$archive=Join-Path $out 'TowerContinued_AfterlifeIdlesR3.archive'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError'){throw 'Readback failed'}
if(@(Compare-Object @($resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Unexpected archive scope'}
foreach($p in $packed.Files.Values){$ms=[IO.MemoryStream]::new();try{$p.Extract($ms);$actual=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($ms.ToArray()))}finally{$ms.Dispose()};if($actual -ne (Get-FileHash -LiteralPath (Join-Path $source $p.Name)).Hash){throw 'Packed bytes mismatch'}}
foreach($p in $hashes.Keys){if((Get-FileHash -LiteralPath $p).Hash -ne $hashes[$p]){throw 'Source changed'}}
$manifest=@{status='BUILT_R6_NOT_INSTALLED_NOT_LIVE';archive=$archive;sha256=(Get-FileHash -LiteralPath $archive).Hash;resources=@($resources);source_root=$source;edits=@($edits);source_hashes=$hashes;packed_readback=$true;replacements=2;unchanged_r3_payloads=3;original_resource_overrides=0;new_actor_identities=0;story_writes=0}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($manifest|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
$manifest|Select-Object status,sha256,packed_readback,unchanged_r3_payloads|ConvertTo-Json
