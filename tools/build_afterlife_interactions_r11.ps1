param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\afterlife_world\interactions_r11'
$out=Join-Path $WorkspaceRoot 'build\AfterlifeInteractionsR11'
$source=Join-Path $out 'source';$safeSource=Join-Path $out 'safe_source'
New-Item -ItemType Directory -Force $audit,$source,$safeSource|Out-Null
$old=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\afterlife_world\interactions_r10\manifest.json') -Raw|ConvertFrom-Json
$hashes=[ordered]@{}
foreach($rel in $old.resources){
 $from=Join-Path $old.source_root $rel;$hashes[$from]=(Get-FileHash -LiteralPath $from).Hash
 foreach($root in @($source,$safeSource)){
  $to=Join-Path $root $rel;New-Item -ItemType Directory -Force (Split-Path $to)|Out-Null
  Copy-Item -LiteralPath $from -Destination $to
 }
}
$dancerRel='towercontinued\afterlife_r1\dancers.questphase'
$retirement=& (Join-Path $PSScriptRoot 'build_afterlife_retirement_r11.ps1') -WorkspaceRoot $WorkspaceRoot -OutputPath (Join-Path $source $dancerRel)
Copy-Item -LiteralPath (Join-Path $source $dancerRel) -Destination (Join-Path $safeSource $dancerRel)
# The fallback also retires dancers and never restores face-changing behavior.
$receipt=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\afterlife_world\interactions_r10\install_receipt.json') -Raw|ConvertFrom-Json
$driverRel='r6/scripts/PTFR_Afterlife_Interactions_R8/AfterlifeInteractionsR8.reds'
$driver=@($receipt.files|Where-Object relative -eq $driverRel)[0]
$safeDriver=Join-Path $out 'safe_runtime\AfterlifeInteractionsR8.reds'
$installedDriver=Join-Path $receipt.game_root $driverRel
if((Get-FileHash -LiteralPath $installedDriver).Hash -ne $driver.sha256){throw 'R10 installed runtime changed'}
New-Item -ItemType Directory -Force (Split-Path $safeDriver)|Out-Null
Copy-Item -LiteralPath $installedDriver -Destination $safeDriver
$emmerickRel='towercontinued\afterlife_interactions_r8\emmerick.scene'
$rogueRel='towercontinued\afterlife_interactions_r8\rogue.scene'
$emmerick=& (Join-Path $PSScriptRoot 'build_afterlife_emmerick_r11.ps1') -WorkspaceRoot $WorkspaceRoot -OutputPath (Join-Path $source $emmerickRel)
$rogue=& (Join-Path $PSScriptRoot 'build_afterlife_rogue_r11.ps1') -WorkspaceRoot $WorkspaceRoot -OutputPath (Join-Path $source $rogueRel)
$ownerRel='towercontinued\afterlife_interactions_r8\owner.questphase'
$owner=Read-Cr2wFile (Join-Path $old.source_root $ownerRel);$g=$owner.RootChunk.Graph.Chunk
(Get-QuestNode $g 2).Type.Chunk.Value=11
$r9=Read-Cr2wFile (Join-Path $WorkspaceRoot ('build\AfterlifeInteractionsR9\source\'+$ownerRel))
$original=(Get-QuestNode (Get-QuestNode $r9.RootChunk.Graph.Chunk 204).PhaseGraph.Chunk 4)
$target=(Get-QuestNode (Get-QuestNode $g 204).PhaseGraph.Chunk 4)
if($target.InterruptionOperations.Count -ne 0 -or $original.InterruptionOperations.Count -eq 0){throw 'Unexpected Rogue interruption baseline'}
foreach($operation in $original.InterruptionOperations){[void]$target.InterruptionOperations.Add($operation.DeepCopy())}
Write-Cr2wFile $owner (Join-Path $source $ownerRel)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $ownerRel)) (Join-Path $audit 'owner.questphase.json')
function Pack-R11([string]$Root,[string]$Archive){
 $hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($Archive)
 try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($Root),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
 $packed=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($Archive,$hs,[ref]$packed).ToString() -ne 'NoError'){throw 'Readback failed'}
 if(@(Compare-Object @($old.resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Unexpected resources'}
 foreach($p in $packed.Files.Values){
  $ms=[IO.MemoryStream]::new()
  try{$p.Extract($ms);$h=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($ms.ToArray()))}finally{$ms.Dispose()}
  if($h -ne (Get-FileHash -LiteralPath (Join-Path $Root $p.Name)).Hash){throw 'Readback byte mismatch'}
 }
}
$archive=Join-Path $out 'TowerContinued_AfterlifeR1.archive'
$safeArchive=Join-Path $out 'safe\TowerContinued_AfterlifeR1.archive'
New-Item -ItemType Directory -Force (Split-Path $safeArchive)|Out-Null
Pack-R11 $source $archive;Pack-R11 $safeSource $safeArchive
foreach($p in $hashes.Keys){if((Get-FileHash -LiteralPath $p).Hash -ne $hashes[$p]){throw "Source changed $p"}}
$m=@{status='BUILT_R11_NOT_INSTALLED_NOT_LIVE';source_root=$source;archive=$archive;sha256=(Get-FileHash -LiteralPath $archive).Hash;resources=$old.resources;source_hashes=$hashes;changed_payloads=@($dancerRel,$emmerickRel,$rogueRel,$ownerRel);unchanged_r10_payloads=9;packed_readback=$true;xl_unchanged=$true;new_actor_identities=0;new_story_writes=0;crash_root_cause_unproven=$true;safe_source_root=$safeSource;safe_archive=$safeArchive;safe_archive_sha256=(Get-FileHash -LiteralPath $safeArchive).Hash;safe_driver=$safeDriver;safe_driver_sha256=$driver.sha256;safe_rollback_preserves_dancer_retirement=$true}
$m.safe_rollback=@(@{relative='archive/pc/mod/TowerContinued_AfterlifeR1.archive';source=$safeArchive;sha256=$m.safe_archive_sha256},@{relative=$driverRel;source=$safeDriver;sha256=$m.safe_driver_sha256})
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($m|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
$m|Select-Object status,sha256,unchanged_r10_payloads,safe_rollback_preserves_dancer_retirement|ConvertTo-Json
