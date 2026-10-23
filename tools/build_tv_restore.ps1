param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\b0_tv_restore'
$source=Join-Path $WorkspaceRoot 'archive\b0_tv_restore\source'
$build=Join-Path $WorkspaceRoot 'build\TVRestore'
New-Item -ItemType Directory -Force -Path $audit,$source,$build|Out-Null
$file=Read-Cr2wFile (Join-Path $WorkspaceRoot 'archive\b0_red_dirt_auto\source\towercontinued\red_dirt_auto\bootstrap.questphase')
$graph=$file.RootChunk.Graph.Chunk
$pause=(Get-QuestNode $graph 1).DeepCopy()
foreach($s in $pause.Sockets){$s.Chunk.Connections.Clear()}
$guard=[WolvenKit.RED4.Types.questLogicalCondition]::new()
$guard.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
$facts=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q305_johnny_scene_active=0;q115_point_of_no_return=0;PTFRBASE_Suspended=0;PTFRTV_Suspended=0;PTFRTV_Applied=0}
foreach($f in $facts.Keys){Add-RedHandle $guard.Conditions (New-FactCondition $f $facts[$f] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
Set-RedHandleProperty $pause Condition $guard
$graph.Nodes.Clear()
Add-RedHandle $graph.Nodes (New-InputNode 0 'In1')
Add-RedHandle $graph.Nodes $pause
Add-RedHandle $graph.Nodes (New-ConditionNode 2 (New-FactCondition 'tv_on' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)))
Add-RedHandle $graph.Nodes (New-SetFactNode 3 'tv_on' 1)
Add-RedHandle $graph.Nodes (New-SetFactNode 4 'PTFRTV_Applied' 1)
Add-RedHandle $graph.Nodes (New-OutputNode 5 'Out1')
foreach($e in @(@(0,'Out',1),@(1,'Out',2),@(2,'True',3),@(2,'False',4),@(3,'Out',4),@(4,'Out',5))){
 [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $e[0]) $e[1]) (Get-QuestSocket (Get-QuestNode $graph $e[2]) 'In'))
}
$depot='towercontinued\tv_restore\bootstrap.questphase'
Write-Cr2wFile $file (Join-Path $source $depot)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $depot)) (Join-Path $audit 'bootstrap.json')
$crc=65535
foreach($b in [Text.Encoding]::UTF8.GetBytes($depot+':1')){$x=($crc -shr 8) -bxor $b;$x=$x -bxor ($x -shr 4);$crc=(($crc -shl 8) -bxor ($x -shl 12) -bxor ($x -shl 5) -bxor $x) -band 65535}
$ep1=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\ep1.quest')
if(@($ep1.RootChunk.Graph.Chunk.Nodes|Where-Object {$_.Chunk.Id.ToString() -eq "$crc"}).Count){throw 'Parent registration collision'}
$xl=Join-Path $WorkspaceRoot 'archive\b0_tv_restore\TowerContinued_TVRestore.archive.xl'
[IO.File]::WriteAllLines($xl,@('# One-time post-Tower TV availability repair.','quest:','  phases:',"    - path: $depot",'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out'),[Text.UTF8Encoding]::new($false))
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load()
$archive=Join-Path $build 'TowerContinued_TVRestore.archive'
$stream=[IO.File]::Create($archive)
try{$writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hash,[WolvenKit.SerilogWrapper]::new());if(-not $writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Archive write failed'}}finally{$stream.Dispose()}
$reader=[WolvenKit.RED4.Archive.IO.ArchiveReader]::new();$packed=$null
if($reader.ReadArchive($archive,$hash,[ref]$packed).ToString() -ne 'NoError'){throw 'Archive reopen failed'}
if($packed.Files.Count -ne 1 -or @($packed.Files.Values)[0].Name -ne $depot){throw 'Unexpected archive resources'}
Copy-Item $xl ($archive+'.xl') -Force
$manifest=@{status='ONE_TIME_AUTOMATIC_CANDIDATE';archive_sha256=(Get-FileHash $archive).Hash;xl_sha256=(Get-FileHash ($archive+'.xl')).Hash;registration_id=$crc;resource=$depot;guards=$facts;writers=@('tv_on=1 only when zero','PTFRTV_Applied=1');vanilla_replacements=@();runtime_polling_added=$false;story_or_media_owner_restarted=$false}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($manifest|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
$manifest|ConvertTo-Json -Depth 5
