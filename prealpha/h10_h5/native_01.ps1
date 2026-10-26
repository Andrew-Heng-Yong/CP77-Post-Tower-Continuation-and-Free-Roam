$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent;$C=Join-Path $PSScriptRoot 'candidate_01'
$source=Join-Path $C 'native_source';if(Test-Path -LiteralPath $source){throw 'Use successor'}
. (Join-Path $W 'tools/build_phase2a.ps1') -WorkspaceRoot $W -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$donor=Join-Path $game 'archive/pc/mod/00000000_TowerContinued_Housing_H1.archive'
if((Get-FileHash -LiteralPath $donor).Hash -cne '4D4CB40E745F9508F97F1A2A0F2D09DD02E0AD527BEC1A4D1B874AA647F55208'){throw 'Housing donor drift'}
function OpenArc($p){$a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($p,$hs,[ref]$a).ToString() -ne 'NoError'){throw 'Read failed'};return $a}
$arc=OpenArc $donor;$templates=@{}
New-Item -ItemType Directory -Path (Join-Path $C 'native_donor')|Out-Null
foreach($e in $arc.Files.Values){
 if($e.Name -notin @('towercontinued\housing_h1\native\northside_purchase.scene','towercontinued\housing_h1\native\northside_owner.questphase')){continue}
 $ms=[IO.MemoryStream]::new();try{$e.Extract($ms);$p=Join-Path $C ('native_donor/'+[IO.Path]::GetFileName($e.Name));[IO.File]::WriteAllBytes($p,$ms.ToArray())}finally{$ms.Dispose()}
 $templates[[IO.Path]::GetFileName($e.Name)]=$p;Export-Cr2wJson (Read-Cr2wFile $p) ($p+'.json')
}
if($templates.Count -ne 2){throw 'Donor selection mismatch'}
& 'C:/Users/Ayong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' (Join-Path $PSScriptRoot 'prepare_scene_01.py')
if($LASTEXITCODE -ne 0){throw 'Scene preparation failed'}
$options=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
$dto=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],(Get-Content -LiteralPath (Join-Path $C 'h10_purchase.scene.json') -Raw),$options)
$sceneDepot='towercontinued\housing_h5\h10_purchase.scene';Write-Cr2wFile $dto.Data (Join-Path $source $sceneDepot)
$old=(Read-Cr2wFile $templates['northside_owner.questphase']).RootChunk
$sg=(Get-QuestNode $old.Graph.Chunk 32).PhaseGraph.Chunk
function ClearH5($n){foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}}
function EqH5($n,$v){return New-FactCondition $n $v ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)}
function PauseH5($id,$cond){$p=(Get-QuestNode $sg 20).DeepCopy();$p.Id=[uint16]$id;ClearH5 $p;Set-RedHandleProperty $p Condition $cond;return $p}
$g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
$guard=[WolvenKit.RED4.Types.questLogicalCondition]::new();$guard.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
Add-RedHandle $guard.Conditions (EqH5 'PTFRH5_Ready' 1);Add-RedHandle $guard.Conditions (EqH5 'PTFRH5_Request' 0);Add-RedHandle $guard.Conditions (EqH5 'PTFRH5_Cancel' 0)
$sn=(Get-QuestNode $sg 22).DeepCopy();$sn.Id=[uint16]2;ClearH5 $sn
$sn.SceneFile=[WolvenKit.RED4.Types.CResourceAsyncReference[WolvenKit.RED4.Types.scnSceneResource]]::new($sceneDepot)
$door='$/03_night_city/c_watson/little_china/loc_megabuilding_a_prefab4KCU2IQ/loc_megabuilding_a_gameplay_prefab2GWVWSA/#loc_megabuilding_a_devices/{q001_door_v_flat}_prefab4EOA7RA/#q001_door_v_flat'
$sn.SceneLocation.NodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($door)
foreach($n in @((New-InputNode 0 'In1'),(PauseH5 1 $guard),$sn,(PauseH5 3 (EqH5 'PTFRH5_Ready' 0)))){Add-RedHandle $g.Nodes $n}
foreach($e in @(@(0,'Out',1,'In'),@(1,'Out',2,'in_purchase'),@(2,'out',3,'In'),@(2,'Default INT',3,'In'),@(3,'Out',1,'In'))){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $e[0]) $e[1]) (Get-QuestSocket (Get-QuestNode $g $e[2]) $e[3]))}
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC;Set-RedHandleProperty $root Graph $g
$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
$ownerDepot='towercontinued\housing_h5\h10_purchase.questphase';Write-Cr2wFile $file (Join-Path $source $ownerDepot)
New-Item -ItemType Directory -Path (Join-Path $C 'native_readback')|Out-Null
foreach($depot in @($sceneDepot,$ownerDepot)){Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $depot)) (Join-Path $C ('native_readback/'+[IO.Path]::GetFileName($depot)+'.json'))}
$rel='archive/pc/mod/00000000_TowerContinued_Housing_H5.archive';$dest=Join-Path $C ('package/'+$rel)
if(Test-Path -LiteralPath (Join-Path $game $rel)){throw 'Target exists'}
New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent)|Out-Null
$s=[IO.File]::Create($dest);try{if(!([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$s)){throw 'Pack failed'}}finally{$s.Dispose()}
$packed=OpenArc $dest;if($packed.Files.Count -ne 2){throw 'Scope drift'};$rows=@()
foreach($e in $packed.Files.Values){$m=[IO.MemoryStream]::new();try{$e.Extract($m);$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray()))}finally{$m.Dispose()}
 if($e.Name -notin @($sceneDepot,$ownerDepot) -or $hash -cne (Get-FileHash -LiteralPath (Join-Path $source $e.Name)).Hash){throw 'Readback mismatch'};$rows+=@{depot=$e.Name;sha256=$hash}
}
$xl="quest:`n  phases:`n    - path: $ownerDepot`n      parent: ep1\quest\ep1.quest`n      input:`n        node: [1]`n        socket: Out`n"
[IO.File]::WriteAllText(($dest+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
@{status='H5_NATIVE_BUILT_NOT_LIVE';resources=$rows;files=@(@{target=$rel;before=$null;after=(Get-FileHash -LiteralPath $dest).Hash},@{target=($rel+'.xl');before=$null;after=(Get-FileHash -LiteralPath ($dest+'.xl')).Hash});donor=$donor;donor_sha256=(Get-FileHash -LiteralPath $donor).Hash}|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $C 'native_01.json') -Encoding utf8
Write-Output 'H5 native dialogue and owner packed; existing archives unchanged.'
