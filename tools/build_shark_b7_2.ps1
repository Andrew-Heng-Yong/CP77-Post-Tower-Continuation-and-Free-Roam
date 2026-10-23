param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
# Build a single byte-identical alias. Do not rerun or edit the installed B7 build.
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
. (Join-Path $PSScriptRoot 'shark_b7_2_helpers.ps1')
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot)
$audit=Join-Path $workspace 'research/gig_restoration/shark_b7_2'
$out=Join-Path $workspace 'build/SharkB7_2'
if(Test-Path -LiteralPath (Join-Path $audit 'install_receipt.json')){throw 'Installed evidence pinned'}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
B71Parser|Out-Null
$oldXl=Join-Path $workspace 'build/GigFamilyB7_1/TowerContinued_FamilyB7.archive.xl'
R5Match $oldXl '76B32526DB9068D39C9D32C6FB187D4D27697F9F5B5045940388C626C4F3C623'
R5Match (Join-Path $game 'archive/pc/mod/TowerContinued_FamilyB7.archive.xl') (R5Hash $oldXl)
$inventory=@(B72Inventory $game)
$collision=B72CollisionCheck $inventory $workspace (B72NewPath)
if($collision.old_id -ne 1 -or $collision.new_id -ne 55205){throw 'Unexpected generated IDs'}
if((B72Id '123456789') -ne 0x29B1){throw 'CRC known-vector failure'}
New-Item -ItemType Directory -Force (Join-Path $audit 'predecessor')|Out-Null
Copy-Item -LiteralPath $oldXl -Destination (Join-Path $audit 'predecessor/TowerContinued_FamilyB7.archive.xl')
$pins=[ordered]@{}
foreach($rel in @('research/gig_restoration/family_b7/manifest.json','research/gig_restoration/family_b7/install_receipt.json','research/gig_restoration/family_b7/tests.json','research/gig_restoration/family_b7/compile_result.json','research/gig_restoration/family_b7_1/install_receipt.json','research/gig_restoration/family_b7_1/tests.json','research/gig_restoration/family_b7_1/deployment_tests.json','tools/build_gig_family_b7.ps1','tools/deploy_gig_family_b7_1.ps1','tools/prepare_gig_family_b7_1.ps1','research/q307_extracted/json/ep1/quest/ep1.quest.json')){$pins[$rel]=R5Hash (Join-Path $workspace $rel)}
$prior=Get-Content (Join-Path $workspace 'research/gig_restoration/family_b7/install_receipt.json') -Raw|ConvertFrom-Json
$unchanged=@($prior.files|Where-Object {$_.relative -ne 'archive/pc/mod/TowerContinued_FamilyB7.archive.xl'})
foreach($f in $unchanged){R5Match (Join-Path $workspace $f.source) $f.sha256;R5Match (Join-Path $game $f.relative) $f.sha256;$pins[$f.source]=$f.sha256}
$pins['build/GigFamilyB7_1/TowerContinued_FamilyB7.archive.xl']=R5Hash $oldXl
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$baseArchive=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive((Join-Path $game 'archive/pc/mod/TowerContinued_FamilyB7.archive'),$hs,[ref]$baseArchive).ToString() -ne 'NoError'){throw 'Cannot read installed B7 archive'}
$original=@($baseArchive.Files.Values|Where-Object {$_.Name -ceq (B72OldPath)})
if($original.Count -ne 1){throw 'Expected one packed original Shark boot'}
$mem=[IO.MemoryStream]::new()
try{$original[0].Extract($mem);$bytes=$mem.ToArray()}finally{$mem.Dispose()}
$bootHash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
if($bootHash -ne 'A5882AD02871F3F6046CA32FC300994BE6F72B21F68AF2559E68A946DE071BA7'){throw 'Original Shark boot mismatch'}
$source=Join-Path $out 'source';$alias=Join-Path $source (B72NewPath)
New-Item -ItemType Directory -Force (Split-Path -Parent $alias)|Out-Null
[IO.File]::WriteAllBytes($alias,$bytes)
# Decode as an additional type/input check. No CR2W rewriting/serialization.
$decoded=Read-Cr2wFile $alias
if($decoded.RootChunk.GetType().Name -ne 'questQuestPhaseResource'){throw 'Alias is not a quest phase'}
if(@($decoded.RootChunk.Graph.Chunk.Nodes|Where-Object {$_.Chunk.GetType().Name -eq 'questInputNodeDefinition' -and $_.Chunk.SocketName.ToString() -ceq 'In1'}).Count -ne 1){throw 'Expected unchanged In1 input'}
$archive=Join-Path $out 'TowerContinued_SharkB7_2.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError'){throw 'Packed alias readback failed'}
if($packed.Files.Count -ne 1){throw 'Expected one additive archive resource'}
$entry=@($packed.Files.Values)[0]
if($entry.Name -cne (B72NewPath)){throw 'Wrong packed alias path'}
$mem=[IO.MemoryStream]::new()
try{$entry.Extract($mem);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray())) -ne $bootHash){throw 'Alias packed bytes changed'}}finally{$mem.Dispose()}
$oldText=Get-Content -LiteralPath $oldXl -Raw
if([regex]::Matches($oldText,[regex]::Escape((B72OldPath))).Count -ne 1){throw 'Expected single Shark path replacement'}
$newText=$oldText.Replace((B72OldPath),(B72NewPath))
B72ValidateXl $newText $workspace
if($newText.Replace((B72NewPath),(B72OldPath)) -cne $oldText){throw 'Non-Shark XL change'}
$xl=Join-Path $out 'TowerContinued_FamilyB7.archive.xl'
[IO.File]::WriteAllText($xl,$newText,[Text.UTF8Encoding]::new($false))
B72ValidateXl (Get-Content -LiteralPath $xl -Raw) $workspace
$refused=[Collections.Generic.List[string]]::new()
foreach($candidate in @((B72OldPath),$inventory[0].path)) {
    $bad=$false;try{B72CollisionCheck $inventory $workspace $candidate|Out-Null}catch{$bad=$true}
    if(-not $bad){throw 'Collision mutant accepted'};$refused.Add($candidate)
}
foreach($text in @($oldText,($newText.Replace('socket: Out','socket: In')),($newText.Replace('node: [1]','node: [2]')))) {
    $bad=$false;try{B72ValidateXl $text $workspace}catch{$bad=$true}
    if(-not $bad){throw 'Configuration mutant accepted'};$refused.Add('invalid_XL')
}
$log=Join-Path $game 'red4ext/plugins/ArchiveXL/ArchiveXL.log'
$live=@(Get-Content -LiteralPath $log|Where-Object {$_ -match 'sts_wat_kab_06' -or $_ -match 'ArchiveXL .*starting'})
if(-not @($live|Where-Object {$_ -match 'same id already exists'}).Count){throw 'Collision live evidence missing'}
R5Json (Join-Path $audit 'collision_review.json') ([ordered]@{source='https://github.com/psiberx/cp2077-archive-xl/blob/v1.27.1/src/App/Extensions/QuestPhase/Extension.cpp#L324-L360';config_source='https://github.com/psiberx/cp2077-archive-xl/blob/v1.27.1/src/App/Extensions/QuestPhase/Config.cpp';collision=$collision;installed_inventory=$inventory;live_log_excerpt=$live;captured_utc=[DateTime]::UtcNow.ToString('o');scope='Direct ep1 root injections from installed XLs, checked against observed merge inventory and pinned native root. No arbitrary external code injection guarantee.'})
$tools=[ordered]@{}
foreach($name in @('shark_b7_2_helpers.ps1','build_shark_b7_2.ps1','test_shark_b7_2_deployment.ps1','build_phase2a.ps1','gig_family_b7_1_xl.ps1','afterlife_faces_r5_deployment.ps1')){$tools['tools/'+$name]=R5Hash (Join-Path $PSScriptRoot $name)}
foreach($p in $pins.Keys){R5Match (Join-Path $workspace $p) $pins[$p]}
$result=[ordered]@{status='PASS_B7_2_SHARK_ALIAS_ENGINE_PENDING';utc=[DateTime]::UtcNow.ToString('o');collision=$collision;packed_alias_byte_identical=$true;boot_sha256=$bootHash;other_75_bindings_unchanged=$true;rejected_cases=$refused.Count;unchanged_b7_files=$unchanged;tools=$tools;pinned=$pins;files=@(
 [ordered]@{source='build/SharkB7_2/TowerContinued_SharkB7_2.archive';relative='archive/pc/mod/TowerContinued_SharkB7_2.archive';predecessor=$null;sha256=R5Hash $archive},
 [ordered]@{source='build/SharkB7_2/TowerContinued_FamilyB7.archive.xl';relative='archive/pc/mod/TowerContinued_FamilyB7.archive.xl';predecessor=R5Hash $oldXl;sha256=R5Hash $xl}
);engine_proof=$false;script_compile_required=$false;native_quest_logic_changed=$false}
R5Json (Join-Path $audit 'tests.json') $result
[pscustomobject]$result|Select-Object status,collision,packed_alias_byte_identical,other_75_bindings_unchanged,rejected_cases,files|ConvertTo-Json -Depth 7
