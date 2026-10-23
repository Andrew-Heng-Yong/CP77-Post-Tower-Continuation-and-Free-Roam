param([string]$Revision='s22_03',[string]$Delamain='delamain_07',[string]$MovingHeat='ep1_04')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
. (Join-Path $WorkspaceRoot 'tools/shark_b7_2_helpers.ps1')
$helper=Get-Content (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
. (Join-Path $WorkspaceRoot 'prealpha/sidejobs_s22/boxing/build.ps1')
. (Join-Path $WorkspaceRoot 'prealpha/sidejobs_s22/the_gig/build.ps1')
if($Revision -cnotmatch '^s22_\d{2}$' -or $Delamain -cnotmatch '^delamain_\d{2}$' -or $MovingHeat -cnotmatch '^ep1_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Immutable build exists'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback')|Out-Null
$pins=[ordered]@{};$resources=[ordered]@{};$boots=@();$components=@();$files=@()
function Pin($p){
 $pins[$p]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash
 if($p.Contains('/raw/')){$decoded=$p.Replace('/raw/','/json/')+'.json';if(Test-Path -LiteralPath (Join-Path $WorkspaceRoot $decoded)){$pins[$decoded]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $decoded)).Hash}}
}
function Pins($m){foreach($p in $m.source_pins.PSObject.Properties){Pin $p.Name;if($pins[$p.Name] -cne $p.Value){throw "Component source drift: $($p.Name)"}}}
function CopyResource($root,$depot,$sha){
 $source=Join-Path (Join-Path $root 'source') $depot
 if((Get-FileHash -LiteralPath $source).Hash -cne $sha -or $resources.Contains($depot)){throw 'Invalid or duplicate component resource'}
 $target=Join-Path (Join-Path $out 'source') $depot
 New-Item -ItemType Directory (Split-Path $target -Parent) -Force|Out-Null
 Copy-Item -LiteralPath $source -Destination $target;$resources[$depot]=$sha
 $label=$depot.Replace('\','_')+'.json'
 Export-Cr2wJson (Read-Cr2wFile $target) (Join-Path (Join-Path $out 'readback') $label)
}
foreach($p in @('prealpha/sidejobs_s22b/build.ps1','prealpha/sidejobs_s22/boxing/build.ps1','prealpha/sidejobs_s22/boxing/contract.json','prealpha/sidejobs_s22/the_gig/build.ps1','prealpha/sidejobs_s22/the_gig/contract.json','research/sidejobs_s22/policy_01.json','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1','tools/shark_b7_2_helpers.ps1','tools/gig_family_b7_1_xl.ps1','tools/afterlife_faces_r5_deployment.ps1','research/q307_extracted/raw/base/quest/cyberpunk2077.questphase','research/q307_extracted/json/ep1/quest/ep1.quest.json')){Pin $p}
$common=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0}
foreach($component in @((New-S22BoxingGraph $WorkspaceRoot $common),(New-S22TheGigGraph $WorkspaceRoot $common))){
 $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $root Graph $component.graph
 $f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$root
 $depot=$component.depot;$raw=Join-Path (Join-Path $out 'source') $depot;Write-Cr2wFile $f $raw
 Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $out ('readback/'+$depot.Replace('\','_')+'.json'))
 $resources[$depot]=(Get-FileHash -LiteralPath $raw).Hash;$boots+=,$depot
 Pin $component.spec.native_source;Pin ($component.spec.native_source.Replace('/raw/','/json/')+'.json')
}
$dmRel='prealpha/sidejobs_s22/delamain_v2/build/'+$Delamain
$dmRoot=Join-Path $WorkspaceRoot $dmRel;$dm=Get-Content (Join-Path $dmRoot 'build.json') -Raw|ConvertFrom-Json
Pins $dm;Pin ($dmRel+'/build.json');Pin ($dmRel+'/tests.json');$components+=,@{name='delamain';manifest=$dmRel+'/build.json';tests=$dmRel+'/tests.json'}
foreach($p in $dm.resources.PSObject.Properties){CopyResource $dmRoot $p.Name $p.Value};$boots+=@($dm.boots)
$mhRel='prealpha/sidejobs_s22/ep1_jobs/build/'+$MovingHeat
$mhRoot=Join-Path $WorkspaceRoot $mhRel;$mh=Get-Content (Join-Path $mhRoot 'component.json') -Raw|ConvertFrom-Json
Pins $mh;Pin ($mhRel+'/component.json');Pin ($mhRel+'/tests.json');$components+=,@{name='moving_heat';manifest=$mhRel+'/component.json';tests=$mhRel+'/tests.json'}
CopyResource $mhRoot $mh.depot $mh.sha256;CopyResource $mhRoot $mh.boot $mh.boot_sha256;$boots+=,$mh.boot
# Pin the additional native child/scene closure already audited by each component.
foreach($folder in @('research/sidejobs_s22/boxing/native_01','research/sidejobs_s22/boxing/native_02','research/sidejobs_s22/delamain/dependencies_01','research/sidejobs_s22/ep1_jobs/native_01','research/sidejobs_s22/ep1_jobs/native_02','research/activity_state_r3/native_sources/raw/base/quest/minor_quests/mq025')){
 if(!(Test-Path (Join-Path $WorkspaceRoot $folder))){continue}
 foreach($p in Get-ChildItem (Join-Path $WorkspaceRoot $folder) -Recurse -File|Where-Object {$_.FullName -match '[\\/]raw[\\/]'}){Pin ([IO.Path]::GetRelativePath($WorkspaceRoot,$p.FullName).Replace('\','/'))}
}
foreach($p in @('research/sidejobs_s22/boxing/audit_02/tests.json','prealpha/sidejobs_s22/boxing/test.py','prealpha/sidejobs_s22/delamain_v2/test.py','prealpha/sidejobs_s22/ep1_jobs/test_component.py')){Pin $p}
$components+=,@{name='boxing';tests='research/sidejobs_s22/boxing/audit_02/tests.json'}
$runtime=Get-Content (Join-Path $WorkspaceRoot 'prealpha/sidejobs_s22/runtime_v2/manifest.json') -Raw|ConvertFrom-Json
Pins $runtime;Pin 'prealpha/sidejobs_s22/runtime_v2/manifest.json'
Pin 'prealpha/sidejobs_s22/runtime_v2/test.py';Pin 'prealpha/sidejobs_s22/runtime_v2/test_result_01.json'
foreach($name in @('SideJobsS2.reds','SideJobsS22.reds')){Pin ('prealpha/sidejobs_s22/runtime_v2/'+$name);Copy-Item -LiteralPath (Join-Path $WorkspaceRoot ('prealpha/sidejobs_s22/runtime_v2/'+$name)) -Destination (Join-Path $out $name)}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
B71Parser|Out-Null;$inventory=@(B72Inventory $game)
$stock=Get-Content (Join-Path $WorkspaceRoot 'research/q307_extracted/json/ep1/quest/ep1.quest.json') -Raw|ConvertFrom-Json
$used=@($stock.Data.RootChunk.graph.Data.nodes.Data.id)+@($inventory.id);$injections=@()
foreach($depot in $boots){$id=B72Id ($depot+':1');if($id -in $used -or $id -ne (B72IdIndependent ($depot+':1'))){throw "Injection collision: $depot"};$used+=,$id;$injections+=,@{depot=$depot;id=$id}}
$archive=Join-Path $out '000_TowerContinued_SideJobs_S22.archive'
$xl=B71Render $boots;B71Parse $xl|Out-Null;[IO.File]::WriteAllText(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne $resources.Count){throw 'Archive scope mismatch'}
foreach($entry in $packed.Files.Values){if(!$resources.Contains($entry.Name)){throw 'Unexpected packed resource'};$mem=[IO.MemoryStream]::new();try{$entry.Extract($mem);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray())) -cne $resources[$entry.Name]){throw 'Packed readback mismatch'}}finally{$mem.Dispose()}}
foreach($file in @($archive,($archive+'.xl'))){$files+=,@{relative='archive/pc/mod/'+[IO.Path]::GetFileName($file);sha256=(Get-FileHash $file).Hash}}
$files+=,@{relative='r6/scripts/TowerContinued_SideJobs_S22/SideJobsS22.reds';sha256=(Get-FileHash (Join-Path $out 'SideJobsS22.reds')).Hash}
$files+=,@{relative='r6/scripts/TowerContinued_SideJobs_S2/SideJobsS2.reds';sha256=(Get-FileHash (Join-Path $out 'SideJobsS2.reds')).Hash;old_sha256='68947EA168C7F3A3AD589BB8E568AF6EF4E1B54F62EB8ACE8190E339F8582C1F'}
$result=[ordered]@{status='BUILT_S22_LIVE_PENDING';files=$files;resources=$resources;boots=$boots;injections=$injections;components=$components;source_pins=$pins;installed_injections=$inventory;common=$common;packed_readback=$true;official_overrides=@();mod_overrides=@('towercontinued\gig_phone_u9\fixer_cleanup.questphase');scope='Bounded progress-preserving native side-job resume routes; existing S2 fresh Inactive current-policy admission. No completed reward replay, generic reset, excluded sequel, global phone restart or save editing. Not all 58 whitelist jobs implemented.'}
[IO.File]::WriteAllText((Join-Path $out 'build.json'),($result|ConvertTo-Json -Depth 35),[Text.UTF8Encoding]::new($false))
@{status=$result.status;build=$out;sha256=(Get-FileHash (Join-Path $out 'build.json')).Hash}|ConvertTo-Json
