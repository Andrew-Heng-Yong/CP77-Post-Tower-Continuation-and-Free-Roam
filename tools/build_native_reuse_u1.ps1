param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
. (Join-Path $PSScriptRoot 'shark_b7_2_helpers.ps1')
$audit=Join-Path $WorkspaceRoot 'research/gig_restoration/native_reuse_u1';$out=Join-Path $WorkspaceRoot 'build/NativeReuseU1'
if(Test-Path (Join-Path $audit 'install_receipt.json')){throw 'Installed U1 evidence pinned'}
New-Item -ItemType Directory -Force $audit,(Join-Path $out 'source')|Out-Null
$helper=Get-Content (Join-Path $PSScriptRoot 'build_fresh_gigs_b5.ps1') -Raw;$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
$planPath=Join-Path $WorkspaceRoot 'research/gig_restoration/family_b7/build_plan.json'
R5Match $planPath '329F8CE605137D6E32556029B673D7375FC4B7F30436D73C127F92CB7609B5E3'
$job=(Get-Content $planPath -Raw|ConvertFrom-Json).jobs|Where-Object id -eq 'sts_wat_kab_06'
$bootPath=Join-Path $WorkspaceRoot ('build/SharkB7_2/source/'+(B72NewPath))
R5Match $bootPath 'A5882AD02871F3F6046CA32FC300994BE6F72B21F68AF2559E68A946DE071BA7'
$boot=Read-Cr2wFile $bootPath;$g=$boot.RootChunk.Graph.Chunk
# Keep ONLY the already-audited small parent prelude and one-shot entry shell.
# Replace its child reference with stock r0. No native quest/scene copies packed.
$child=Get-QuestNode $g 11
$child.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($job.resources[0].depot)
foreach($id in @(65000,65003,65004,65006)){
 $n=Get-QuestNode $g $id;$n.Type.Chunk.FactName=$n.Type.Chunk.FactName.ToString().Replace('PTFRB7_wat_kab_06','PTFRU1_Shark')
}
foreach($id in @(65001,65002)){
 $n=Get-QuestNode $g $id
 foreach($h in $n.Condition.Chunk.Conditions){$t=$h.Chunk.Type.Chunk;$t.FactName=$t.FactName.ToString().Replace('PTFRB7_wat_kab_06','PTFRU1_Shark')}
 # Recheck conflicting legacy request immediately before entering native child.
 foreach($key in @('Queued','Request','Started','OwnerFinished','Fault')){Add-RedHandle $n.Condition.Chunk.Conditions (New-FactCondition ('PTFRB7_wat_kab_06_'+$key) 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
}
$depot='towercontinued\native_reuse_u1\shark_wrapper.questphase';$raw=Join-Path (Join-Path $out 'source') $depot
New-Item -ItemType Directory -Force (Split-Path -Parent $raw)|Out-Null
Write-Cr2wFile $boot $raw;Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $audit 'wrapper.json')
$nativePins=[ordered]@{}
foreach($r in $job.resources){$nativePins[$r.raw]=R5Hash (Join-Path $WorkspaceRoot $r.raw);R5Match (Join-Path $WorkspaceRoot $r.binding.source) $r.binding.sha256}
$read=Read-Cr2wFile $raw
if((Get-QuestNode $read.RootChunk.Graph.Chunk 11).PhaseResource.DepotPath.ToString() -cne $job.resources[0].depot){throw 'Native reference mismatch'}
if((EdgesB5 $read.RootChunk.Graph.Chunk|ConvertTo-Json -Compress -Depth 8) -cne (EdgesB5 $g|ConvertTo-Json -Compress -Depth 8)){throw 'Edge readback mismatch'}
B71Parser|Out-Null
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$inventory=@(B72Inventory $game);$collision=B72CollisionCheck $inventory $WorkspaceRoot $depot
if($collision.new_id -in $inventory.id){throw 'U1 injection ID already installed'}
$xl=B71Render @($depot);$yaml=B71Parse $xl;$ph=B71Child (B71Child $yaml 'quest') 'phases'
if($ph.Children.Count -ne 1){throw 'Expected one trial binding'}
[IO.File]::WriteAllText((Join-Path $out 'TowerContinued_NativeReuseU1.archive.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$archive=Join-Path $out 'TowerContinued_NativeReuseU1.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne 1){throw 'Pack scope/readback failure'}
$entry=@($packed.Files.Values)[0];if($entry.Name -cne $depot){throw 'Packed non-wrapper resource'}
$mem=[IO.MemoryStream]::new();try{$entry.Extract($mem);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray())) -ne (R5Hash $raw)){throw 'Packed mismatch'}}finally{$mem.Dispose()}
$files=@(
 @{source='build/NativeReuseU1/TowerContinued_NativeReuseU1.archive';relative='archive/pc/mod/TowerContinued_NativeReuseU1.archive'},
 @{source='build/NativeReuseU1/TowerContinued_NativeReuseU1.archive.xl';relative='archive/pc/mod/TowerContinued_NativeReuseU1.archive.xl'},
 @{source='redscript/PTFR_NativeReuseU1/NativeReuseU1.reds';relative='r6/scripts/PTFR_NativeReuseU1/NativeReuseU1.reds'},
 @{source='build/NativeReuseU1/GigFamilyB7.reds';relative='r6/scripts/PTFR_GigFamilyB7/GigFamilyB7.reds'}
)
$originalScript=Join-Path $WorkspaceRoot 'redscript/PTFR_GigFamilyB7/GigFamilyB7.reds'
R5Match $originalScript '9BC70799B64D4A6EB8B605CCC51ECB1FB9C6D378F060B10EF79E2B7C6A92CD51'
$originalText=Get-Content $originalScript -Raw
$anchor='  public func Restore(id: String,overrideHistory: Bool) -> String {'
$insert=@'

    // U1 experimental exclusion; original owner files and persistent fields unchanged.
    if Equals(id,"sts_wat_kab_06") { return "Shark copied adapter disabled while NativeReuseU1 is installed. Use U1 Start on an unused disposable snapshot."; }
    let u1Index=GigDataB7.Index(id);
    if u1Index>=0 && Equals(GigDataB7.Region(u1Index),"wat") && this.Fact("PTFRU1_Shark_Request")==1 && this.Fact("PTFRU1_Shark_OwnerFinished")!=1 { return "Deferred: native Shark U1 trial owns the Watson test window."; }
'@
if([regex]::Matches($originalText,[regex]::Escape($anchor)).Count -ne 1){throw 'B7 insertion anchor mismatch'}
$newText=$originalText.Replace($anchor,$anchor+$insert)
if($newText.Replace($insert,'') -cne $originalText){throw 'Unexpected B7 change'}
[IO.File]::WriteAllText((Join-Path $out 'GigFamilyB7.reds'),$newText,[Text.UTF8Encoding]::new($false))
foreach($f in $files){$f.sha256=R5Hash (Join-Path $WorkspaceRoot $f.source)}
R5Json (Join-Path $audit 'manifest.json') ([ordered]@{status='BUILT_U1_ENGINE_PENDING';files=$files;depot=$depot;native_resource=$job.resources[0].depot;native_pins=$nativePins;collision=$collision;wrapper_only=$true;original_resources_packed=0;packed_readback=$true;scope='One small entry/prelude wrapper referencing original Shark phase and all its original dependencies. No native graph edits, reward guards, phone reroutes, fixer credit writes or tier forcing.'})
'BUILT_U1_ENGINE_PENDING'
