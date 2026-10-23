param([string]$Revision='s28_01',[Parameter(Mandatory=$true)][string[]]$Components,[Parameter(Mandatory=$true)][string]$Runtime,[Parameter(Mandatory=$true)][string[]]$CurrentDonorProofs)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $WorkspaceRoot 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
. (Join-Path $WorkspaceRoot 'prealpha/sidejobs_s28/vehicles/prereq_models_04.ps1')
. (Join-Path $WorkspaceRoot 'tools/shark_b7_2_helpers.ps1')
$nativeHashService=[WolvenKit.Common.Services.HashService]::new();$nativeHashService.Load()
if($Revision -cnotmatch '^s28_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Immutable build exists'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback')|Out-Null
$pins=[ordered]@{};$resources=[ordered]@{};$boots=@();$componentsOut=@();$files=@();$sourceReads=@();$donors=[ordered]@{}
$python='C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
function Pin($p){
 if([IO.Path]::IsPathRooted($p) -or $p -match '(^|/)\.\.(/|$)'){throw 'Unsafe pin'}
 $h=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash
 if($pins.Contains($p) -and $pins[$p] -cne $h){throw 'Source changed'}
 $pins[$p]=$h
}
function Pins($m){foreach($p in $m.source_pins.PSObject.Properties){Pin $p.Name;if($pins[$p.Name] -cne $p.Value){throw "Source drift: $($p.Name)"}}}
foreach($p in @('recovery/framework_pr63_01/receipt.json','research/framework_pr63_01/package.json','prealpha/sidejobs_s28/vehicles/prereq_models_04.ps1','prealpha/sidejobs_s28/build_02.ps1','prealpha/sidejobs_s28/test_02.py','prealpha/sidejobs_s28/resource_check_02.ps1','prealpha/sidejobs_s28/compile_02.py','prealpha/sidejobs_s28/runtime/generate_03.py','prealpha/sidejobs_s28/runtime/test_03.py','prealpha/sidejobs_s28/verify_journal_metadata_02.py','prealpha/sidejobs_s21/compile.py','tools/catalog_gig_rollout_r2.py','prealpha/sidejobs_s27/raw_compare.py','tools/build_phase2a.ps1','tools/shark_b7_2_helpers.ps1','tools/gig_family_b7_1_xl.ps1','tools/afterlife_faces_r5_deployment.ps1','research/q307_extracted/json/ep1/quest/ep1.quest.json','research/q307_extracted/raw/ep1/quest/ep1.quest')){Pin $p}
$historical=[ordered]@{};$currentNative=@();$donorProofs=@()
foreach($rel in $CurrentDonorProofs){
 Pin $rel;$proof=Get-Content -LiteralPath (Join-Path $WorkspaceRoot $rel) -Raw|ConvertFrom-Json;Pins $proof
 if($proof.status -cnotlike 'PASS_CURRENT_OFFICIAL_*'){throw 'Current donor proof required'}
 foreach($row in $proof.rows){
  if(!$row.current_byte_exact -or (Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $row.raw)).Hash -cne $row.sha256){throw 'Current donor identity mismatch'}
  Pin $row.raw;$currentNative+=,$row
 }
 foreach($row in @($proof.historical_comparison_sources)+@($proof.metadata_only_sources)){
  Pin $row.raw;if($pins[$row.raw] -cne $row.sha256){throw 'Historical evidence changed'};$historical[$row.raw]=$row.sha256
 }
 $donorProofs+=,$rel
}
foreach($rel in @('research/sidejobs_s28/encounters/world_support_01.json','research/sidejobs_s28/review/encounter_world_review_01.json','research/sidejobs_s28/review/encounter_review_08.json')){
 Pin $rel;$e=Get-Content -LiteralPath (Join-Path $WorkspaceRoot $rel) -Raw|ConvertFrom-Json
 if($e.PSObject.Properties.Name -contains 'source_pins'){Pins $e}
}
foreach($rel in $Components){
 $path=Join-Path $WorkspaceRoot $rel;$root=Split-Path $path -Parent
 $m=Get-Content -LiteralPath $path -Raw|ConvertFrom-Json;Pins $m;Pin $rel
 if($m.PSObject.Properties.Name -contains 'override_donors' -and @($m.override_donors.PSObject.Properties).Count -ne 0){throw 'S28 overrides forbidden'}
 $proofPath=Join-Path $root 'tests.json';$proofRel=[IO.Path]::GetRelativePath($WorkspaceRoot,$proofPath).Replace('\','/');Pin $proofRel
 $proof=Get-Content -LiteralPath $proofPath -Raw|ConvertFrom-Json
 $bound=if($proof.PSObject.Properties.Name -contains 'component_sha256'){$proof.component_sha256}else{$proof.build_sha256}
 if($proof.status -cnotlike 'PASS*' -or $bound -cne $pins[$rel]){throw 'Component test binding mismatch'}
 if($proof.PSObject.Properties.Name -contains 'source_pins'){Pins $proof}
 $testers=@(Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.py' -File -Recurse|Where-Object {(Get-FileHash -LiteralPath $_.FullName).Hash -ceq $proof.tester_sha256})
 if($testers.Count -ne 1){throw 'Ambiguous component tester'}
 Pin ([IO.Path]::GetRelativePath($WorkspaceRoot,$testers[0].FullName).Replace('\','/'))
 $componentsOut+=,@{manifest=$rel;tests=$proofRel;root=[IO.Path]::GetRelativePath($WorkspaceRoot,$root).Replace('\','/')}
 foreach($p in $m.resources.PSObject.Properties){
  if($resources.Contains($p.Name) -or $p.Name -cnotlike 'towercontinued\sidejobs_s28\*'){throw 'Duplicate or out-of-scope resource'}
  $source=Join-Path (Join-Path $root 'source') $p.Name
  if((Get-FileHash -LiteralPath $source).Hash -cne $p.Value){throw 'Component resource drift'}
  $target=Join-Path (Join-Path $out 'source') $p.Name
  New-Item -ItemType Directory (Split-Path -Parent $target) -Force|Out-Null
  Copy-Item -LiteralPath $source -Destination $target;$resources[$p.Name]=$p.Value
  Export-Cr2wJson (Read-Cr2wFile $target) (Join-Path $out ('readback/'+$p.Name.Replace('\','_')+'.json'))
 }
 $boots+=@($m.boots)
}
if(@($boots|Select-Object -Unique).Count -ne $boots.Count -or $boots.Count -lt 4){throw 'Incomplete/duplicate boots'}
$metadataProof='research/sidejobs_s28/journal_metadata_02.json';Pin $metadataProof
$metadata=Get-Content -LiteralPath (Join-Path $WorkspaceRoot $metadataProof) -Raw|ConvertFrom-Json;Pins $metadata
if($metadata.status -cne 'PASS_USED_JOURNAL_METADATA_ALL_VARIANTS'){throw 'Journal metadata proof required'}
Pin 'research/sidejobs_s28/journal_variants_05/ep1_2_gamedata/raw/ep1/journal/cooked_journal.journal'
foreach($p in @($pins.Keys)){
 if($p -match '/raw/(base|ep1)/journal/cooked_journal\.journal$' -and $p -cnotin @($metadata.source_pins.PSObject.Properties.Name)){$historical[$p]=$pins[$p]}
}
$rt=Join-Path $WorkspaceRoot $Runtime
$r=Get-Content -LiteralPath (Join-Path $rt 'manifest.json') -Raw|ConvertFrom-Json;Pins $r
foreach($name in @('manifest.json','tests.json','SideJobsS28.reds')){Pin ($Runtime+'/'+$name)}
$proof=Get-Content -LiteralPath (Join-Path $rt 'tests.json') -Raw|ConvertFrom-Json;Pins $proof
if($proof.status -cne 'PASS_OFFLINE_NOT_LIVE' -or $proof.manifest_sha256 -cne (Get-FileHash -LiteralPath (Join-Path $rt 'manifest.json')).Hash){throw 'Runtime proof mismatch'}
if((Get-FileHash -LiteralPath (Join-Path $rt 'SideJobsS28.reds')).Hash -cne $r.files.'SideJobsS28.reds'){throw 'Runtime drift'}
Copy-Item -LiteralPath (Join-Path $rt 'SideJobsS28.reds') -Destination (Join-Path $out 'SideJobsS28.reds')
foreach($p in @($pins.Keys)){
 if($p -notmatch '/raw/.+\.(quest|questphase|scene|workspot)$'){continue}
 $witness=$p.Replace('/raw/','/json/')+'.json';if(!$pins.Contains($witness)){Pin $witness}
 $freshRel='readback/native_source_'+$sourceReads.Count+'.json';$fresh=Join-Path $out $freshRel
 Export-Cr2wJson (Read-Cr2wFile (Join-Path $WorkspaceRoot $p)) $fresh
 & $python (Join-Path $WorkspaceRoot 'prealpha/sidejobs_s27/raw_compare.py') (Join-Path $WorkspaceRoot $witness) $fresh
 if($LASTEXITCODE -ne 0){throw "Native raw/witness mismatch: $p"}
 $sourceReads+=,@{raw=$p;raw_sha256=$pins[$p];witness=$witness;witness_sha256=$pins[$witness];fresh=$freshRel;fresh_sha256=(Get-FileHash -LiteralPath $fresh).Hash;payload_equal=$true}
}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$xlRoot=Join-Path $game 'archive/pc/mod';$xlPins=[ordered]@{}
foreach($file in Get-ChildItem -LiteralPath $xlRoot -Filter '*.xl' -File|Sort-Object Name){$xlPins[$file.FullName]=(Get-FileHash -LiteralPath $file.FullName).Hash}
B71Parser|Out-Null;$inventory=@(B72Inventory $game)
foreach($entry in $inventory){if($xlPins[(Join-Path $xlRoot $entry.source)] -cne $entry.source_sha256){throw 'Injection source changed'}}
$stock=Get-Content (Join-Path $WorkspaceRoot 'research/q307_extracted/json/ep1/quest/ep1.quest.json') -Raw|ConvertFrom-Json
$used=@($stock.Data.RootChunk.graph.Data.nodes.Data.id)+@($inventory.id);$injections=@()
foreach($depot in $boots){
 if(!$resources.Contains($depot)){throw 'Unpacked boot'}
 $id=B72Id ($depot+':1')
 if($id -in $used -or $id -ne (B72IdIndependent ($depot+':1'))){throw "Injection collision: $depot"}
 $used+=,$id;$injections+=,@{depot=$depot;id=$id}
}
$archive=Join-Path $out 'TowerContinued_SideJobs_S28.archive';$xl=B71Render $boots;B71Parse $xl|Out-Null
[IO.File]::WriteAllText(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne $resources.Count){throw 'Archive scope mismatch'}
foreach($entry in $packed.Files.Values){
 if(!$resources.Contains($entry.Name)){throw 'Unexpected resource'}
 $mem=[IO.MemoryStream]::new()
 try{$entry.Extract($mem);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray())) -cne $resources[$entry.Name]){throw 'Packed readback mismatch'}}finally{$mem.Dispose()}
}
foreach($file in @($archive,($archive+'.xl'))){$files+=,@{relative='archive/pc/mod/'+[IO.Path]::GetFileName($file);sha256=(Get-FileHash -LiteralPath $file).Hash}}
$files+=,@{relative='r6/scripts/TowerContinued_SideJobs_S28/SideJobsS28.reds';sha256=(Get-FileHash -LiteralPath (Join-Path $out 'SideJobsS28.reds')).Hash}
foreach($p in $pins.Keys){if((Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash -cne $pins[$p]){throw "Source changed: $p"}}
foreach($p in $xlPins.Keys){if((Get-FileHash -LiteralPath $p).Hash -cne $xlPins[$p]){throw 'XL changed'}}
if((@($xlPins.Keys|Sort-Object)-join '|') -cne (@(Get-ChildItem -LiteralPath $xlRoot -Filter '*.xl' -File|ForEach-Object FullName|Sort-Object)-join '|')){throw 'XL set changed'}
$result=[ordered]@{status='BUILT_S28_LIVE_PENDING';current_donor_proofs=$donorProofs;current_native_donors=$currentNative;historical_evidence=$historical;files=$files;resources=$resources;boots=$boots;injections=$injections;components=$componentsOut;runtime=$Runtime;journal_metadata_proof=$metadataProof;source_pins=$pins;native_source_readbacks=$sourceReads;installed_injections=$inventory;installed_xl_pins=$xlPins;packed_readback=$true;official_overrides=@();mod_overrides=@();override_donors=$donors;scope='Four original native side-job beginnings, existing progress/owners/completed rewards protected. Unsupported continuation defers without restart. Native scenes adapted only for approved Johnny presentation.'}
[IO.File]::WriteAllText((Join-Path $out 'build.json'),($result|ConvertTo-Json -Depth 60),[Text.UTF8Encoding]::new($false))
@{status=$result.status;build=$out;resources=$resources.Count;boots=$boots.Count;sha256=(Get-FileHash -LiteralPath (Join-Path $out 'build.json')).Hash}|ConvertTo-Json
