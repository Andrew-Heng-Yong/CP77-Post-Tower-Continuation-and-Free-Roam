param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
. (Join-Path $PSScriptRoot 'shark_b7_2_helpers.ps1')
$audit=Join-Path $WorkspaceRoot 'research/gig_restoration/native_jeopardy_u4';$out=Join-Path $WorkspaceRoot 'build/NativeJeopardyU4'
if(Test-Path (Join-Path $audit 'install_receipt.json')){throw 'Installed U4 evidence pinned'}
New-Item -ItemType Directory -Force $audit,(Join-Path $out 'source')|Out-Null
$helper=Get-Content (Join-Path $PSScriptRoot 'build_fresh_gigs_b5.ps1') -Raw;$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
$planPath=Join-Path $WorkspaceRoot 'research/gig_restoration/family_b7/build_plan.json'
R5Match $planPath '329F8CE605137D6E32556029B673D7375FC4B7F30436D73C127F92CB7609B5E3'
$job=(Get-Content $planPath -Raw|ConvertFrom-Json).jobs|Where-Object id -eq 'sts_hey_rey_06'
$bootPath=Join-Path $WorkspaceRoot 'build/GigFamilyB7/source/towercontinued/family_b7/sts_hey_rey_06/boot.questphase'
$boot=Read-Cr2wFile $bootPath;$g=$boot.RootChunk.Graph.Chunk
$child=Get-QuestNode $g 7
$child.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($job.resources[0].depot)
foreach($id in @(65000,65003,65004,65006)){$n=Get-QuestNode $g $id;$n.Type.Chunk.FactName=$n.Type.Chunk.FactName.ToString().Replace('PTFRB7_hey_rey_06','PTFRU4_Jeopardy')}
foreach($id in @(65001,65002)){
 $n=Get-QuestNode $g $id
 foreach($h in $n.Condition.Chunk.Conditions){$t=$h.Chunk.Type.Chunk;$t.FactName=$t.FactName.ToString().Replace('PTFRB7_hey_rey_06','PTFRU4_Jeopardy')}
 foreach($key in @('Queued','Request','Started','OwnerFinished','Fault')){Add-RedHandle $n.Condition.Chunk.Conditions (New-FactCondition ('PTFRB7_hey_rey_06_'+$key) 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
}
$depot='towercontinued\native_jeopardy_u4\jeopardy_wrapper.questphase';$raw=Join-Path (Join-Path $out 'source') $depot
New-Item -ItemType Directory -Force (Split-Path -Parent $raw)|Out-Null
Write-Cr2wFile $boot $raw;Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $audit 'wrapper.json')
$nativePins=[ordered]@{};foreach($r in $job.resources){$nativePins[$r.raw]=R5Hash (Join-Path $WorkspaceRoot $r.raw);R5Match (Join-Path $WorkspaceRoot $r.binding.source) $r.binding.sha256}
$read=Read-Cr2wFile $raw
if((Get-QuestNode $read.RootChunk.Graph.Chunk 7).PhaseResource.DepotPath.ToString() -cne $job.resources[0].depot){throw 'Native reference mismatch'}
if((EdgesB5 $read.RootChunk.Graph.Chunk|ConvertTo-Json -Compress -Depth 8) -cne (EdgesB5 $g|ConvertTo-Json -Compress -Depth 8)){throw 'Edge readback mismatch'}
B71Parser|Out-Null
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$inventory=@(B72Inventory $game);$collision=B72CollisionCheck $inventory $WorkspaceRoot $depot
if($collision.new_id -in $inventory.id){throw 'U4 injection ID already installed'}
$xl=B71Render @($depot);$yaml=B71Parse $xl;$ph=B71Child (B71Child $yaml 'quest') 'phases';if($ph.Children.Count -ne 1){throw 'Expected one trial binding'}
[IO.File]::WriteAllText((Join-Path $out 'TowerContinued_NativeJeopardyU4.archive.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$archive=Join-Path $out 'TowerContinued_NativeJeopardyU4.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne 1){throw 'Pack scope failure'}
$entry=@($packed.Files.Values)[0];if($entry.Name -cne $depot){throw 'Packed unexpected resource'}
$mem=[IO.MemoryStream]::new();try{$entry.Extract($mem);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray())) -ne (R5Hash $raw)){throw 'Packed mismatch'}}finally{$mem.Dispose()}
$originalScript=Join-Path $WorkspaceRoot 'build/NativeQueueU3/GigFamilyB7.reds'
R5Match $originalScript '5595FF260571C1FE711F92D92938ABBB7F8E541808F94BBF6CD4C6393E6403A5'
$text=Get-Content $originalScript -Raw;$anchor='  public func Restore(id: String,overrideHistory: Bool) -> String {'
$insert=@'

    // U4 excludes the copied Jeopardy owner while its original-resource pilot is installed.
    if Equals(id,"sts_hey_rey_06") { return "Jeopardy copied adapter disabled; use NativeJeopardyU4 Start on the reviewed disposable snapshot."; }
    let u4Index=GigDataB7.Index(id);
    if u4Index>=0 && Equals(GigDataB7.Region(u4Index),"hey") && this.Fact("PTFRU4_Jeopardy_Request")==1 && this.Fact("PTFRU4_Jeopardy_OwnerFinished")!=1 && (this.Fact("PTFRU4_Jeopardy_Permit")==1 || this.Fact("PTFRU4_Jeopardy_Started")==1) { return "Deferred: original Jeopardy owns Heywood test window."; }
'@
if([regex]::Matches($text,[regex]::Escape($anchor)).Count -ne 1){throw 'B7 insertion anchor mismatch'}
$new=$text.Replace($anchor,$anchor+$insert);if($new.Replace($insert,'') -cne $text){throw 'Unexpected B7 delta'}
[IO.File]::WriteAllText((Join-Path $out 'GigFamilyB7.reds'),$new,[Text.UTF8Encoding]::new($false))
$files=@(
 @{source='build/NativeJeopardyU4/TowerContinued_NativeJeopardyU4.archive';relative='archive/pc/mod/TowerContinued_NativeJeopardyU4.archive';predecessor=$null},
 @{source='build/NativeJeopardyU4/TowerContinued_NativeJeopardyU4.archive.xl';relative='archive/pc/mod/TowerContinued_NativeJeopardyU4.archive.xl';predecessor=$null},
 @{source='redscript/PTFR_NativeJeopardyU4/NativeJeopardyU4.reds';relative='r6/scripts/PTFR_NativeJeopardyU4/NativeJeopardyU4.reds';predecessor=$null},
 @{source='build/NativeJeopardyU4/GigFamilyB7.reds';relative='r6/scripts/PTFR_GigFamilyB7/GigFamilyB7.reds';predecessor=R5Hash $originalScript}
)
foreach($f in $files){$f.sha256=R5Hash (Join-Path $WorkspaceRoot $f.source)}
R5Json (Join-Path $audit 'manifest.json') ([ordered]@{status='BUILT_U4_ENGINE_PENDING';files=$files;depot=$depot;native_resource=$job.resources[0].depot;native_pins=$nativePins;collision=$collision;wrapper_only=$true;original_resources_packed=0;packed_readback=$true;old_boot_sha256=R5Hash $bootPath;scope='One whitelisted original Jeopardy phase trial. Developer incomplete-as-unstarted admission, separate safe entry shape. No history certification, native graph edits, phone reroutes, fixer credit bridge or tier forcing.'})
'BUILT_U4_ENGINE_PENDING'
