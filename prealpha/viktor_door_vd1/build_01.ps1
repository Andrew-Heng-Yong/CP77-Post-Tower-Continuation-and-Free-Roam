$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$base=Join-Path $ws 'prealpha/credits_cover_lc4/candidate_02'
$out=Join-Path $PSScriptRoot 'candidate_02'
if(Test-Path -LiteralPath $out){throw 'Fresh candidate required'}
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$m=Get-Content -LiteralPath (Join-Path $base 'install_manifest_01.json') -Raw|ConvertFrom-Json
$audit=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'native_review_03/providers.json') -Raw|ConvertFrom-Json
if($audit.status -cne 'PASS_NATIVE_PROVIDERS_NEW_DEPOT_FREE' -or $audit.archive_count -ne 133){throw 'Native census not ready'}
foreach($f in $m.package_files){if((Get-FileHash -LiteralPath (Join-Path $base ('package/'+$f.path))).Hash -cne $f.after){throw ('Baseline changed '+$f.path)}}
$source=Join-Path $out 'archive_source';$package=Join-Path $out 'package'
[void][IO.Directory]::CreateDirectory($out)
Copy-Item -LiteralPath (Join-Path $base 'archive_source') -Destination $source -Recurse
Copy-Item -LiteralPath (Join-Path $base 'package') -Destination $package -Recurse
$original=@(Get-ChildItem -LiteralPath $source -Recurse -File|ForEach-Object {@{depot=[IO.Path]::GetRelativePath($source,$_.FullName).Replace('/','\');sha256=(Get-FileHash -LiteralPath $_.FullName).Hash}})
if($original.Count -ne 1563){throw 'Base resource inventory changed'}
$old=Read-Cr2wFile (Join-Path $source 'towercontinued/misty_viktor_world/access_r11.questphase')
$oldg=$old.RootChunk.Graph.Chunk
$facts=[ordered]@{}
$oldManifest=Get-Content -LiteralPath (Join-Path $ws 'research/misty_viktor_world/access_r11_manifest.json') -Raw|ConvertFrom-Json
foreach($p in $oldManifest.guards.PSObject.Properties){$facts[$p.Name]=[int]$p.Value}
$facts['PTFRPA2_Finished']=1
$ref='$/03_night_city/c_watson/little_china/loc_mystic_mistys_ripperdoc_prefabH2DWJJI/#loc_mystic_mistys_ripperdoc_gameplay/single_door_prefabSSNK5BI/#q115_dvc_ripperdoc_room_door'
function Logic($op,$children){$c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::$op;foreach($child in $children){Add-RedHandle $c.Conditions $child};return $c}
function Guard([bool]$inverse=$false){$parts=@(foreach($key in $facts.Keys){New-FactCondition $key $facts[$key] $(if($inverse){[WolvenKit.RED4.Types.Enums+EComparisonType]::NotEqual}else{[WolvenKit.RED4.Types.Enums+EComparisonType]::Equal})});return Logic $(if($inverse){'OR'}else{'AND'}) $parts}
function Loaded([bool]$inverse=$false){$c=[WolvenKit.RED4.Types.questNodeLoadingCondition]::new();$c.ObjectRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref);$c.Inverted=$inverse;return $c}
function Ready {return Logic 'AND' @((Guard),(Loaded))}
function Pause($id,$condition){$n=(Get-QuestNode $oldg 50).DeepCopy();$n.Id=[uint16]$id;$n.Sockets.Clear();foreach($s in @(@('In','Input'),@('Out','Output'))){[void](New-QuestSocket $n $s[0] ([WolvenKit.RED4.Types.Enums+questSocketType]::$($s[1])))};Set-RedHandleProperty $n Condition $condition;return $n}
$g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
function Put($n){Add-RedHandle $g.Nodes $n}
function Link($a,$socket,$b){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $socket) (Get-QuestSocket (Get-QuestNode $g $b) 'In'))}
Put (New-InputNode 0 'In1')
Put (New-ConditionNode 1 (New-FactCondition 'PTFRVD1_Claimed' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)))
Put (New-SetFactNode 2 'PTFRVD1_Claimed' 1)
Put (New-SetFactNode 3 'PTFRVD1_Registered' 1)
Put (Pause 10 (Ready))
Put (New-ConditionNode 11 (Ready))
$door=(Get-QuestNode $oldg 53).DeepCopy();$door.Id=[uint16]12;$door.Sockets.Clear()
foreach($s in @(@('In','Input'),@('Out','Output'))){[void](New-QuestSocket $door $s[0] ([Enum]::Parse([WolvenKit.RED4.Types.Enums+questSocketType],$s[1])))}
$p=$door.Type.Chunk.Params[0].Chunk
if($door.Type.Chunk.Params.Count -ne 1 -or $p.DeviceControllerClass.ToString() -cne 'DoorControllerPS' -or $p.DeviceAction.ToString() -cne 'ForceUnlock' -or $p.ActionProperties.Count){throw 'Unlock precedent changed'}
$p.ObjectRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref)
Put $door
$count=New-SetFactNode 13 'PTFRVD1_Requests' 1;$count.Type.Chunk.SetExactValue=$false;Put $count
Put (New-SetFactNode 14 'PTFRVD1_Ready' 1)
Put (Pause 15 (Logic 'OR' @((Guard $true),(Loaded $true))))
Put (New-SetFactNode 16 'PTFRVD1_Ready' 0)
Link 0 Out 1;Link 1 True 2;Link 2 Out 3;Link 3 Out 10;Link 10 Out 11;Link 11 False 10;Link 11 True 12
Link 12 Out 13;Link 13 Out 14;Link 14 Out 15;Link 15 Out 16;Link 16 Out 10
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
Set-RedHandleProperty $root Graph $g
$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
$depot='towercontinued\viktor_door_vd1\clinic_access.questphase'
Write-Cr2wFile $file (Join-Path $source $depot)
$check=Read-Cr2wFile (Join-Path $source $depot)
Export-Cr2wJson $check (Join-Path $out 'owner_readback_01.json')
if($check.RootChunk.Graph.Chunk.Nodes.Count -ne 11 -or @(Get-GraphEdges $check.RootChunk.Graph.Chunk).Count -ne 12){throw 'Graph shape changed'}
foreach($socket in @($check.RootChunk.Graph.Chunk.Nodes|ForEach-Object {$_.Chunk.Sockets}|ForEach-Object {$_.Chunk})){foreach($conn in $socket.Connections){foreach($end in @($conn.Chunk.Source.Chunk,$conn.Chunk.Destination.Chunk)){if(@($end.Connections|Where-Object {[object]::ReferenceEquals($_.Chunk,$conn.Chunk)}).Count -ne 1){throw 'Nonreciprocal socket'}}}}
$xlPath=Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
$xl=[IO.File]::ReadAllText($xlPath);if([regex]::Matches($xl,'(?m)^streaming:').Count -ne 1 -or $xl.Contains($depot)){throw 'XL anchor changed'}
$nl=if($xl.Contains("`r`n")){"`r`n"}else{"`n"}
$entry=@("    - path: $depot",'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out') -join $nl
$newxl=$xl.Replace('streaming:',($entry+$nl+'streaming:'))
[IO.File]::WriteAllText($xlPath,$newxl,[Text.UTF8Encoding]::new($false))
$archive=Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError'){throw 'Archive reopen failed'}
if($packed.Files.Count -ne 1564){throw 'Resource count'}
$all=@($original)+@(@{depot=$depot;sha256=(Get-FileHash -LiteralPath (Join-Path $source $depot)).Hash})
foreach($row in $all){
 if((Get-FileHash -LiteralPath (Join-Path $source $row.depot)).Hash -cne $row.sha256){throw ('Prior source changed '+$row.depot)}
 $key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($row.depot)
 if(!$packed.Files.ContainsKey([uint64]$key)){throw ('Missing '+$row.depot)}
 $ms=[IO.MemoryStream]::new();try{$packed.Files[[uint64]$key].Extract($ms);$h=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($ms.ToArray()))}finally{$ms.Dispose()}
 if($h -cne $row.sha256){throw ('Archive readback '+$row.depot)}
}
$rows=@(foreach($f in $m.package_files){$path=Join-Path $package $f.path;@{path=$f.path;before=$f.after;after=(Get-FileHash -LiteralPath $path).Hash;bytes=(Get-Item -LiteralPath $path).Length}})
if(@($rows|Where-Object {$_.before -cne $_.after}).Count -ne 2){throw 'Package changed beyond archive and XL'}
$report=@{status='PASS_VD1_FULL_ARCHIVE_READBACK';archive_members=1564;old_member_bytes_unchanged=1563;new_resource=$depot;target=$ref;guards=$facts;nodes=11;edges=@(Get-GraphEdges $check.RootChunk.Graph.Chunk);package_files=$rows;members=$all;game_writes=0;save_writes=0}
$report|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $out 'build_01.json') -Encoding utf8NoBOM
$report|Select-Object status,archive_members,old_member_bytes_unchanged,nodes|ConvertTo-Json
