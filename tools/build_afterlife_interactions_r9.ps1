param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\afterlife_world\interactions_r9'
$out=Join-Path $WorkspaceRoot 'build\AfterlifeInteractionsR9'
$source=Join-Path $out 'source'
New-Item -ItemType Directory -Force $audit,$source|Out-Null
$old=Get-Content (Join-Path $WorkspaceRoot 'research\afterlife_world\interactions_r8\manifest.json') -Raw|ConvertFrom-Json
$hashes=[ordered]@{}
function ReadSource([string]$p){$script:hashes[$p]=(Get-FileHash -LiteralPath $p).Hash;Read-Cr2wFile $p}
function Ref([string]$s){[WolvenKit.RED4.Types.NodeRef]::op_Implicit($s)}
function Name([string]$s){[WolvenKit.RED4.Types.CName]::op_Implicit($s)}
function Put($g,$n){Add-RedHandle $g.Nodes $n}
function Link($g,[int]$a,[string]$s,[int]$b,[string]$dest='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $s) (Get-QuestSocket (Get-QuestNode $g $b) $dest))}
function ClearSockets($n){foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}}
function Save($f,[string]$rel){Write-Cr2wFile $f (Join-Path $script:source $rel);Export-Cr2wJson (Read-Cr2wFile (Join-Path $script:source $rel)) (Join-Path $script:audit ([IO.Path]::GetFileName($rel)+'.json'))}
foreach($rel in $old.resources){$p=Join-Path $old.source_root $rel;$hashes[$p]=(Get-FileHash $p).Hash;$to=Join-Path $source $rel;New-Item -ItemType Directory -Force (Split-Path $to)|Out-Null;Copy-Item -LiteralPath $p -Destination $to}

# Reuse the tested Streetkid typed-JSON traversal technique. First remove all
# obsolete hologram references, THEN compact player 2->1 / performer 513->257.
$rogueRel='towercontinued\afterlife_interactions_r8\rogue.scene'
$rogue=ReadSource (Join-Path $old.source_root $rogueRel)
$options=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
$dto=[WolvenKit.Common.Conversion.RedFileDto]::new($rogue,$false)
$doc=ConvertFrom-Json ([WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($dto,$options)) -AsHashtable -Depth 100
$root=$doc['Data']['RootChunk']
if($root['actors'].Count -ne 1 -or $root['actors'][0]['actorId']['id'] -ne 0 -or $root['playerActors'].Count -ne 1 -or $root['playerActors'][0]['actorId']['id'] -ne 2){throw 'Unexpected R8 Rogue cast'}
$changes=[Collections.Generic.List[object]]::new()
function Repair($value,[string]$path){
 if($value -is [Collections.IDictionary]){
  # These are alternate hologram speakers on otherwise local dialogue events.
  if($value.Contains('additionalSpeakers') -and $value['additionalSpeakers']){
   $speakers=$value['additionalSpeakers']['speakers'];$kept=@($speakers|Where-Object {$_['actorId']['id'] -ne 1})
   if($kept.Count -ne $speakers.Count){$changes.Add(@{path=$path+'.additionalSpeakers.speakers';removed_holo=$speakers.Count-$kept.Count});$value['additionalSpeakers']['speakers']=$kept}
  }
  if($value.Contains('performersDebugSymbols')){
   $symbols=$value['performersDebugSymbols'];$kept=@($symbols|Where-Object {$_['performerId']['id'] -ne 257})
   if($kept.Count -ne $symbols.Count){$changes.Add(@{path=$path+'.performersDebugSymbols';removed_holo=$symbols.Count-$kept.Count});$value['performersDebugSymbols']=$kept}
  }
  if($value.Contains('$type') -and $value.Contains('id') -and $value['$type'] -in 'scnActorId','scnPerformerId'){
   $type=$value['$type'];$id=[uint32]$value['id']
   if(($type -eq 'scnActorId' -and $id -eq 1) -or ($type -eq 'scnPerformerId' -and $id -eq 257)){throw "Unremoved hologram reference at $path"}
   if(($type -eq 'scnActorId' -and $id -eq 2) -or ($type -eq 'scnPerformerId' -and $id -eq 513)){
    $next=if($type -eq 'scnActorId'){[uint32]1}else{[uint32]257}
    $value['id']=$next;$changes.Add(@{path=$path;type=$type;from=$id;to=$next})
   }
  }
  foreach($key in @($value.Keys)){Repair $value[$key] ($path+'.'+$key)}
 }elseif($value -is [Collections.IEnumerable] -and $value -isnot [string]){$i=0;foreach($v in $value){Repair $v ($path+'['+$i+']');$i++}}
}
Repair $root '$.Data.RootChunk'
$fixed=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],(ConvertTo-Json -InputObject $doc -Depth 100 -Compress),$options)
Save $fixed.Data $rogueRel

$ownerRel='towercontinued\afterlife_interactions_r8\owner.questphase'
$owner=ReadSource (Join-Path $old.source_root $ownerRel);$g=$owner.RootChunk.Graph.Chunk
$phase=(Get-QuestNode $g 104).PhaseGraph.Chunk
$native=ReadSource (Join-Path $WorkspaceRoot 'research\afterlife_world\patrons_sources\raw\base\quest\main_quests\part1\q103\phases\q103_emmerick_routine.questphase')
$nativeGraph=(Get-QuestNode $native.RootChunk.Graph.Chunk 24).PhaseGraph.Chunk
$oldStart=(Get-QuestNode $phase 2).Condition.Chunk.DeepCopy()
$common=$oldStart.Conditions[0].Chunk.Conditions[0].Chunk.DeepCopy()
$anchor=$oldStart.Conditions[0].Chunk.DeepCopy()
$inside=$oldStart.Conditions[1].Chunk.DeepCopy()
$distance=(Get-QuestNode $nativeGraph 12).Condition.Chunk.DeepCopy()
$distance.Type.Chunk.DistanceDefinition1.Chunk.NodeRef2.Reference=Ref '$/03_night_city/#PTFRAL1_Emmerick'
$distance.Type.Chunk.DistanceDefinition1.Chunk.NodeRef2.Names.Clear()
[void]$distance.Type.Chunk.DistanceDefinition1.Chunk.NodeRef2.Names.Add((Name emmerick))
function And($conditions){$c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND;foreach($a in $conditions){Add-RedHandle $c.Conditions $a};return $c}
function Pause([int]$id,$condition){$n=(Get-QuestNode $script:phase 2).DeepCopy();$n.Id=[uint16]$id;ClearSockets $n;Set-RedHandleProperty $n Condition $condition;return $n}
# Rebuild links explicitly so every socket is reciprocal. Keep saved IDs0..7.
foreach($n in $phase.Nodes){ClearSockets $n.Chunk}
Set-RedHandleProperty (Get-QuestNode $phase 2) Condition (And @($common,$inside))
Set-RedHandleProperty (Get-QuestNode $phase 3) Condition (And @($common,$inside,$distance,$anchor))
Put $phase (New-SetFactNode 8 PTFRAL8_EStage 3)
Put $phase (Pause 9 (And @($common,$distance)))
Put $phase (New-SetFactNode 10 PTFRAL8_EStage 4)
Put $phase (Pause 11 (And @($common,$anchor)))
Put $phase (New-SetFactNode 12 PTFRAL8_EStage 6)
Put $phase (New-SetFactNode 13 PTFRAL8_EStage 7)
Put $phase (New-SetFactNode 14 PTFRAL8_EStage 5)
$completed=New-SetFactNode 15 PTFRAL8_ECompleted 1;$completed.Type.Chunk.SetExactValue=$false;Put $phase $completed
$cancelled=New-SetFactNode 16 PTFRAL8_ECancelled 1;$cancelled.Type.Chunk.SetExactValue=$false;Put $phase $cancelled
Link $phase 0 Out 2;Link $phase 0 Out 5;Link $phase 2 Out 8;Link $phase 8 Out 9;Link $phase 9 Out 10;Link $phase 10 Out 11;Link $phase 11 Out 3;Link $phase 3 False 2;Link $phase 3 True 6;Link $phase 6 Out 7;Link $phase 7 Out 14;Link $phase 14 Out 4 emmerick_entrance;Link $phase 4 emmerick_entrance_out 12;Link $phase 12 Out 15;Link $phase 15 Out 1;Link $phase 5 Out 13;Link $phase 13 Out 16;Link $phase 16 Out 1
foreach($n in $g.Nodes){ClearSockets $n.Chunk}
Put $g (New-SetFactNode 107 PTFRAL8_EStage 2)
Put $g (New-SetFactNode 108 PTFRAL8_EStage 1)
Put $g (New-SetFactNode 109 PTFRAL8_EStage 8)
Put $g (New-SetFactNode 2 PTFRAL8_NativeRevision 9)
Link $g 0 Out 1;Link $g 1 Out 2;Link $g 2 Out 100;Link $g 2 Out 200
Link $g 100 Out 108;Link $g 108 Out 101;Link $g 101 Out 102;Link $g 102 False 101;Link $g 102 True 103;Link $g 103 Out 107;Link $g 107 Out 104 In1;Link $g 104 Out1 105;Link $g 105 Out 109;Link $g 109 Out 106;Link $g 106 Out 108
Link $g 200 Out 201;Link $g 201 Out 202;Link $g 202 False 201;Link $g 202 True 203;Link $g 203 Out 204 In1;Link $g 204 Out1 205;Link $g 205 Out 206;Link $g 206 Out 201
Save $owner $ownerRel
$archive=Join-Path $out 'TowerContinued_AfterlifeR1.archive'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError'){throw 'Readback failed'}
if(@(Compare-Object @($old.resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Unexpected resources'}
foreach($p in $packed.Files.Values){$ms=[IO.MemoryStream]::new();try{$p.Extract($ms);$h=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($ms.ToArray()))}finally{$ms.Dispose()};if($h -ne (Get-FileHash (Join-Path $source $p.Name)).Hash){throw 'Readback byte mismatch'}}
foreach($p in $hashes.Keys){if((Get-FileHash $p).Hash -ne $hashes[$p]){throw "Source changed $p"}}
$m=@{status='BUILT_R9_NOT_INSTALLED_NOT_LIVE';source_root=$source;archive=$archive;sha256=(Get-FileHash $archive).Hash;resources=$old.resources;source_hashes=$hashes;changed_payloads=@($rogueRel,$ownerRel);unchanged_r8_payloads=11;packed_readback=$true;actor_repairs=@($changes.ToArray());xl_unchanged=$true;new_actor_identities=0;new_story_writes=0}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($m|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
$m|Select-Object status,sha256,unchanged_r8_payloads,@{n='actor_repairs';e={$changes.Count}}|ConvertTo-Json
