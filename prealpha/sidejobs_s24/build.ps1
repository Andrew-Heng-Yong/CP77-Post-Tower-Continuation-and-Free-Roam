param([string]$Revision='s24_01',[Parameter(Mandatory=$true)][string[]]$Components,[Parameter(Mandatory=$true)][string]$Runtime)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
. (Join-Path $WorkspaceRoot 'tools/shark_b7_2_helpers.ps1')
if($Revision -cnotmatch '^s24_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Immutable build exists'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback')|Out-Null
$pins=[ordered]@{};$resources=[ordered]@{};$boots=@();$componentsOut=@();$files=@()
function Pin($p){
 if([IO.Path]::IsPathRooted($p) -or $p -match '(^|/)\.\.(/|$)'){throw 'Unsafe pin'}
 $pins[$p]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash
}
function Pins($m){foreach($p in $m.source_pins.PSObject.Properties){Pin $p.Name;if($pins[$p.Name] -cne $p.Value){throw "Component source drift: $($p.Name)"}}}
foreach($p in @('prealpha/sidejobs_s24/build.ps1','tools/build_phase2a.ps1','tools/shark_b7_2_helpers.ps1','tools/gig_family_b7_1_xl.ps1','tools/afterlife_faces_r5_deployment.ps1','research/q307_extracted/raw/base/quest/cyberpunk2077.questphase','research/q307_extracted/json/ep1/quest/ep1.quest.json','research/sidejobs_s23/live_20261016_01/capture.json')){Pin $p}
foreach($rel in $Components){
 $path=Join-Path $WorkspaceRoot $rel;$root=Split-Path $path -Parent
 $m=Get-Content -LiteralPath $path -Raw|ConvertFrom-Json;Pins $m;Pin $rel
 $proofPath=Join-Path $root 'tests.json';$proofRel=[IO.Path]::GetRelativePath($WorkspaceRoot,$proofPath).Replace('\','/');Pin $proofRel
 $test=Get-Content -LiteralPath $proofPath -Raw|ConvertFrom-Json
 $bound=if($test.PSObject.Properties.Name -contains 'component_sha256'){$test.component_sha256}else{$test.build_sha256}
 if($test.status -cnotlike 'PASS*' -or $bound -cne $pins[$rel]){throw 'Component test binding mismatch'}
 $tester=@(Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.py' -File -Recurse|Where-Object {(Get-FileHash -LiteralPath $_.FullName).Hash -ceq $test.tester_sha256})
 if($tester.Count -ne 1){throw 'Missing/ambiguous component tester'}
 Pin ([IO.Path]::GetRelativePath($WorkspaceRoot,$tester[0].FullName).Replace('\','/'))
 $componentsOut+=,@{manifest=$rel;tests=$proofRel;root=[IO.Path]::GetRelativePath($WorkspaceRoot,$root).Replace('\','/')}
 foreach($p in $m.resources.PSObject.Properties){
  if($resources.Contains($p.Name) -or $p.Name -notlike 'towercontinued\*'){throw 'Duplicate or official resource override'}
  $source=Join-Path (Join-Path $root 'source') $p.Name
  if((Get-FileHash -LiteralPath $source).Hash -cne $p.Value){throw 'Component resource drift'}
  $target=Join-Path (Join-Path $out 'source') $p.Name
  New-Item -ItemType Directory (Split-Path -Parent $target) -Force|Out-Null
  Copy-Item -LiteralPath $source -Destination $target;$resources[$p.Name]=$p.Value
  Export-Cr2wJson (Read-Cr2wFile $target) (Join-Path $out ('readback/'+$p.Name.Replace('\','_')+'.json'))
 }
 $boots+=@($m.boots)
}
if(@($boots|Select-Object -Unique).Count -ne $boots.Count){throw 'Duplicate boot resource'}
$metadataProof='research/sidejobs_s24/ep1/journal_variants_01/metadata_03.json'
Pin $metadataProof
Pin 'prealpha/sidejobs_s24/ep1/verify_journal_metadata.py'
$metadata=Get-Content -LiteralPath (Join-Path $WorkspaceRoot $metadataProof) -Raw|ConvertFrom-Json
if($metadata.status -cne 'PASS_USED_JOURNAL_METADATA_ALL_VARIANTS'){throw 'Journal metadata proof required'}
Pins $metadata
$transitionProof='research/sidejobs_s24/ep1/transition_01.json'
Pin $transitionProof
$transition=Get-Content -LiteralPath (Join-Path $WorkspaceRoot $transitionProof) -Raw|ConvertFrom-Json
if($transition.status -cne 'PASS_NATIVE_FAILURE_BOUNDARIES'){throw 'Fresh/resume exclusivity proof required'}
Pins $transition
$rt=Join-Path $WorkspaceRoot $Runtime;$runtimeManifest=Join-Path $rt 'manifest.json'
$r=Get-Content -LiteralPath $runtimeManifest -Raw|ConvertFrom-Json;Pins $r
foreach($name in @('manifest.json','tests.json','SideJobsS24.reds')){Pin ($Runtime+'/'+$name)}
Pin 'prealpha/sidejobs_s24/runtime/test.py'
$proof=Get-Content -LiteralPath (Join-Path $rt 'tests.json') -Raw|ConvertFrom-Json
if($proof.status -cne 'PASS_OFFLINE_NOT_LIVE' -or $proof.manifest_sha256 -cne (Get-FileHash $runtimeManifest).Hash){throw 'Runtime proof mismatch'}
if((Get-FileHash -LiteralPath (Join-Path $rt 'SideJobsS24.reds')).Hash -cne $r.files.'SideJobsS24.reds'){throw 'Runtime source drift'}
Copy-Item -LiteralPath (Join-Path $rt 'SideJobsS24.reds') -Destination (Join-Path $out 'SideJobsS24.reds')
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$xlRoot=Join-Path $game 'archive/pc/mod';$xlPins=[ordered]@{}
foreach($file in Get-ChildItem -LiteralPath $xlRoot -Filter '*.xl' -File|Sort-Object Name){$xlPins[$file.FullName]=(Get-FileHash -LiteralPath $file.FullName).Hash}
B71Parser|Out-Null;$inventory=@(B72Inventory $game)
foreach($entry in $inventory){if($xlPins[(Join-Path $xlRoot $entry.source)] -cne $entry.source_sha256){throw 'Parsed injection source changed'}}
$stock=Get-Content (Join-Path $WorkspaceRoot 'research/q307_extracted/json/ep1/quest/ep1.quest.json') -Raw|ConvertFrom-Json
$used=@($stock.Data.RootChunk.graph.Data.nodes.Data.id)+@($inventory.id);$injections=@()
foreach($depot in $boots){
 if(!$resources.Contains($depot)){throw 'Unpacked boot'}
 $id=B72Id ($depot+':1')
 if($id -in $used -or $id -ne (B72IdIndependent ($depot+':1'))){throw "Injection collision: $depot"}
 $used+=,$id;$injections+=,@{depot=$depot;id=$id}
}
$archive=Join-Path $out '00000_TowerContinued_SideJobs_S24.archive'
$xl=B71Render $boots;B71Parse $xl|Out-Null
[IO.File]::WriteAllText(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne $resources.Count){throw 'Archive scope mismatch'}
foreach($entry in $packed.Files.Values){
 if(!$resources.Contains($entry.Name)){throw 'Unexpected packed resource'}
 $mem=[IO.MemoryStream]::new()
 try{$entry.Extract($mem);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray())) -cne $resources[$entry.Name]){throw 'Packed readback mismatch'}}finally{$mem.Dispose()}
}
foreach($file in @($archive,($archive+'.xl'))){$files+=,@{relative='archive/pc/mod/'+[IO.Path]::GetFileName($file);sha256=(Get-FileHash -LiteralPath $file).Hash}}
$files+=,@{relative='r6/scripts/TowerContinued_SideJobs_S24/SideJobsS24.reds';sha256=(Get-FileHash -LiteralPath (Join-Path $out 'SideJobsS24.reds')).Hash}
foreach($p in $pins.Keys){if((Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash -cne $pins[$p]){throw "Source changed during build: $p"}}
foreach($p in $xlPins.Keys){if((Get-FileHash -LiteralPath $p).Hash -cne $xlPins[$p]){throw 'Installed XL changed during build'}}
if((@($xlPins.Keys|Sort-Object)-join '|') -cne (@(Get-ChildItem -LiteralPath $xlRoot -Filter '*.xl' -File|ForEach-Object FullName|Sort-Object)-join '|')){throw 'Installed XL set changed during build'}
$result=[ordered]@{status='BUILT_S24_LIVE_PENDING';files=$files;resources=$resources;boots=$boots;injections=$injections;components=$componentsOut;runtime=$Runtime;journal_metadata_proof=$metadataProof;source_pins=$pins;installed_injections=$inventory;installed_xl_pins=$xlPins;packed_readback=$true;official_overrides=@();mod_overrides=@('towercontinued\gig_phone_u9\fixer_cleanup.questphase');scope='Fresh whitelisted side-job restoration. Previous restorations and completed/active/progressed jobs preserved. No claimed pre-ending history.'}
[IO.File]::WriteAllText((Join-Path $out 'build.json'),($result|ConvertTo-Json -Depth 45),[Text.UTF8Encoding]::new($false))
@{status=$result.status;build=$out;resources=$resources.Count;boots=$boots.Count;sha256=(Get-FileHash -LiteralPath (Join-Path $out 'build.json')).Hash}|ConvertTo-Json

