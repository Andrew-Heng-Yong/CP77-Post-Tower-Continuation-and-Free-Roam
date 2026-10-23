param([string]$Revision='s25_01',[Parameter(Mandatory=$true)][string[]]$Components,[Parameter(Mandatory=$true)][string]$Runtime)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
. (Join-Path $WorkspaceRoot 'tools/shark_b7_2_helpers.ps1')
if($Revision -cnotmatch '^s25_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Immutable build exists'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback')|Out-Null
$pins=[ordered]@{};$resources=[ordered]@{};$boots=@();$componentsOut=@();$files=@();$overrides=@();$donors=[ordered]@{};$replacements=@();$sourceReads=@()
function Pin($p){
 if([IO.Path]::IsPathRooted($p) -or $p -match '(^|/)\.\.(/|$)'){throw 'Unsafe pin'}
 $pins[$p]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash
}
function Pins($m){foreach($p in $m.source_pins.PSObject.Properties){Pin $p.Name;if($pins[$p.Name] -cne $p.Value){throw "Component source drift: $($p.Name)"}}}
foreach($p in @('prealpha/sidejobs_s25/build.ps1','tools/build_phase2a.ps1','tools/shark_b7_2_helpers.ps1','tools/gig_family_b7_1_xl.ps1','tools/afterlife_faces_r5_deployment.ps1','research/q307_extracted/raw/base/quest/cyberpunk2077.questphase','research/q307_extracted/json/ep1/quest/ep1.quest.json','research/sidejobs_s23/live_20261016_01/capture.json')){Pin $p}
foreach($p in @('prealpha/sidejobs_s21/compile.py','prealpha/sidejobs_s23/compile.py','prealpha/sidejobs_s22b/compile.py','prealpha/sidejobs_s22/runtime_v2/test.py','prealpha/sidejobs_s22/delamain_v2/test.py')){Pin $p}
$prophetReview='research/sidejobs_s25/policy/prophet_review_01.json';Pin $prophetReview
$pr=Get-Content -LiteralPath (Join-Path $WorkspaceRoot $prophetReview) -Raw|ConvertFrom-Json
if($pr.status -cne 'PASS_INDEPENDENT_BOUNDED_REVIEW_NOT_LIVE' -or !$pr.old_new_mutual_exclusion){throw 'Independent Prophet review required'}
Pins $pr
Pin 'prealpha/sidejobs_s25/policy/review_prophet.py'
if($pins['prealpha/sidejobs_s25/policy/review_prophet.py'] -cne $pr.reviewer_sha256){throw 'Prophet reviewer drift'}
foreach($rel in $Components){
 $path=Join-Path $WorkspaceRoot $rel;$root=Split-Path $path -Parent
 $m=Get-Content -LiteralPath $path -Raw|ConvertFrom-Json;Pins $m;Pin $rel
 # Bind every JSON witness consumed by component tests; native readbacks that
 # lack hashes in an older component manifest get a fresh raw-file comparison.
 foreach($r in Get-ChildItem -LiteralPath $root -Filter '*.json' -File -Recurse){Pin ([IO.Path]::GetRelativePath($WorkspaceRoot,$r.FullName).Replace('\','/'))}
 if($m.PSObject.Properties.Name -contains 'native_readbacks'){
  foreach($r in $m.native_readbacks.PSObject.Properties){
   if(!$pins.Contains($r.Name)){throw 'Unpinned raw native readback source'}
   $witness=Join-Path $root $r.Value
   $witnessRel=[IO.Path]::GetRelativePath($WorkspaceRoot,$witness).Replace('\','/');Pin $witnessRel
   $freshRel='readback/native_source_'+$sourceReads.Count+'.json';$fresh=Join-Path $out $freshRel
   Export-Cr2wJson (Read-Cr2wFile (Join-Path $WorkspaceRoot $r.Name)) $fresh
   $oldData=(Get-Content -LiteralPath $witness -Raw|ConvertFrom-Json).Data|ConvertTo-Json -Depth 100 -Compress
   $newData=(Get-Content -LiteralPath $fresh -Raw|ConvertFrom-Json).Data|ConvertTo-Json -Depth 100 -Compress
   if($oldData -cne $newData){throw "Native raw/readback payload mismatch: $($r.Name)"}
   $sourceReads+=,@{raw=$r.Name;raw_sha256=$pins[$r.Name];witness=$witnessRel;witness_sha256=$pins[$witnessRel];fresh=$freshRel;fresh_sha256=(Get-FileHash -LiteralPath $fresh).Hash;payload_equal=$true}
  }
 }
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
 if($m.PSObject.Properties.Name -contains 'mod_overrides'){$overrides+=@($m.mod_overrides)}
 elseif($m.PSObject.Properties.Name -contains 'override_donors'){$overrides+=@($m.override_donors.PSObject.Properties.Name)}
 if($m.PSObject.Properties.Name -contains 'override_donors'){
  foreach($p in $m.override_donors.PSObject.Properties){if($donors.Contains($p.Name)){throw 'Duplicate override donor'};$donors[$p.Name]=$p.Value;Pin $p.Value.source;if($pins[$p.Value.source] -cne $p.Value.sha256){throw 'Override donor drift'}}
 }
 if($m.PSObject.Properties.Name -contains 'policy_plan'){
  $plan=Get-Content -LiteralPath (Join-Path $WorkspaceRoot $m.policy_plan) -Raw|ConvertFrom-Json
  foreach($p in $plan.resources){
   $depot=$p.depot
   if($donors.Contains($depot)){throw 'Duplicate policy donor'}
   $oldArchive=if($depot -like 'towercontinued\sidejobs_s22\*'){'000_TowerContinued_SideJobs_S22.archive'}elseif($depot -like 'towercontinued\sidejobs_s23\*'){'0000_TowerContinued_SideJobs_S23.archive'}elseif($depot -ceq 'towercontinued\side_job_pilot_s1\owner.questphase'){'TowerContinued_PreAlpha.archive'}else{throw 'Unrecognized policy donor'}
   $donors[$depot]=@{source=$p.source;sha256=$p.source_sha256;archive=$oldArchive}
   $witness=Join-Path $root ('original_readback/'+$depot.Replace('\','_')+'.json')
   $witnessRel=[IO.Path]::GetRelativePath($WorkspaceRoot,$witness).Replace('\','/')
   if(!$pins.Contains($witnessRel)){throw 'Unpinned policy original readback'}
   $freshRel='readback/native_source_'+$sourceReads.Count+'.json';$fresh=Join-Path $out $freshRel
   Export-Cr2wJson (Read-Cr2wFile (Join-Path $WorkspaceRoot $p.source)) $fresh
   $oldData=(Get-Content -LiteralPath $witness -Raw|ConvertFrom-Json).Data|ConvertTo-Json -Depth 100 -Compress
   $newData=(Get-Content -LiteralPath $fresh -Raw|ConvertFrom-Json).Data|ConvertTo-Json -Depth 100 -Compress
   if($oldData -cne $newData){throw "Policy raw/readback payload mismatch: $depot"}
   $sourceReads+=,@{raw=$p.source;raw_sha256=$pins[$p.source];witness=$witnessRel;witness_sha256=$pins[$witnessRel];fresh=$freshRel;fresh_sha256=(Get-FileHash -LiteralPath $fresh).Hash;payload_equal=$true}
  }
 }
 if($m.PSObject.Properties.Name -contains 'script_replacements'){
  foreach($p in $m.script_replacements){
   Pin $p.path;Pin $p.source
   if($pins[$p.path] -cne $p.sha256 -or $pins[$p.source] -cne $p.source_sha256){throw 'Replacement script drift'}
   $name=[IO.Path]::GetFileName($p.relative)
   if(Test-Path -LiteralPath (Join-Path $out $name)){throw 'Duplicate replacement name'}
   Copy-Item -LiteralPath (Join-Path $WorkspaceRoot $p.path) -Destination (Join-Path $out $name)
   $replacements+=,@{relative=$p.relative;source=$name;sha256=$p.sha256;action='replace';before_sha256=$p.source_sha256}
  }
 }
}
if(@($boots|Select-Object -Unique).Count -ne $boots.Count){throw 'Duplicate boot resource'}
$metadataProof='research/sidejobs_s25/journal_metadata_02.json'
Pin $metadataProof
Pin 'prealpha/sidejobs_s25/verify_journal_metadata.py'
$metadata=Get-Content -LiteralPath (Join-Path $WorkspaceRoot $metadataProof) -Raw|ConvertFrom-Json
if($metadata.status -cne 'PASS_USED_JOURNAL_METADATA_ALL_VARIANTS'){throw 'Journal metadata proof required'}
Pins $metadata
if((@($donors.Keys|Sort-Object)-join '|') -cne (@($overrides|Sort-Object)-join '|')){throw 'Override donor scope mismatch'}
$rt=Join-Path $WorkspaceRoot $Runtime;$runtimeManifest=Join-Path $rt 'manifest.json'
$r=Get-Content -LiteralPath $runtimeManifest -Raw|ConvertFrom-Json;Pins $r
foreach($name in @('manifest.json','tests.json','SideJobsS25.reds')){Pin ($Runtime+'/'+$name)}
Pin 'prealpha/sidejobs_s25/runtime/test.py'
$proof=Get-Content -LiteralPath (Join-Path $rt 'tests.json') -Raw|ConvertFrom-Json
if($proof.status -cne 'PASS_OFFLINE_NOT_LIVE' -or $proof.manifest_sha256 -cne (Get-FileHash $runtimeManifest).Hash){throw 'Runtime proof mismatch'}
if((Get-FileHash -LiteralPath (Join-Path $rt 'SideJobsS25.reds')).Hash -cne $r.files.'SideJobsS25.reds'){throw 'Runtime source drift'}
Copy-Item -LiteralPath (Join-Path $rt 'SideJobsS25.reds') -Destination (Join-Path $out 'SideJobsS25.reds')
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
$archive=Join-Path $out '000000_TowerContinued_SideJobs_S25.archive'
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
foreach($file in @($archive,($archive+'.xl'))){$files+=,@{relative='archive/pc/mod/'+[IO.Path]::GetFileName($file);source=[IO.Path]::GetFileName($file);action='add';sha256=(Get-FileHash -LiteralPath $file).Hash}}
$files+=,@{relative='r6/scripts/TowerContinued_SideJobs_S25/SideJobsS25.reds';source='SideJobsS25.reds';action='add';sha256=(Get-FileHash -LiteralPath (Join-Path $out 'SideJobsS25.reds')).Hash}
$files+=@($replacements)
foreach($p in $pins.Keys){if((Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash -cne $pins[$p]){throw "Source changed during build: $p"}}
foreach($p in $xlPins.Keys){if((Get-FileHash -LiteralPath $p).Hash -cne $xlPins[$p]){throw 'Installed XL changed during build'}}
if((@($xlPins.Keys|Sort-Object)-join '|') -cne (@(Get-ChildItem -LiteralPath $xlRoot -Filter '*.xl' -File|ForEach-Object FullName|Sort-Object)-join '|')){throw 'Installed XL set changed during build'}
$result=[ordered]@{status='BUILT_S25_LIVE_PENDING';files=$files;resources=$resources;boots=$boots;injections=$injections;components=$componentsOut;runtime=$Runtime;journal_metadata_proof=$metadataProof;source_pins=$pins;native_source_readbacks=$sourceReads;installed_injections=$inventory;installed_xl_pins=$xlPins;packed_readback=$true;official_overrides=@();mod_overrides=@($overrides|Sort-Object);override_donors=$donors;scope='Inactive-only new activation; additional bounded stock fresh-entry families. Previously issued progress and all excluded/active/completed jobs preserved. No claimed pre-ending history.'}
[IO.File]::WriteAllText((Join-Path $out 'build.json'),($result|ConvertTo-Json -Depth 45),[Text.UTF8Encoding]::new($false))
@{status=$result.status;build=$out;resources=$resources.Count;boots=$boots.Count;sha256=(Get-FileHash -LiteralPath (Join-Path $out 'build.json')).Hash}|ConvertTo-Json



