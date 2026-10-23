param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\b0_red_dirt_auto'
$source=Join-Path $WorkspaceRoot 'archive\b0_red_dirt_auto\source'
$build=Join-Path $WorkspaceRoot 'build\RedDirt_Auto'
New-Item -ItemType Directory -Force -Path $audit,$source,$build|Out-Null
$c5=Join-Path $WorkspaceRoot 'archive\b0_ordinary_mirrors_c5_red_dirt\source\towercontinued\ordinary_mirrors_c5_red_dirt\m42_gate.questphase'
$file=Read-Cr2wFile $c5
$graph=$file.RootChunk.Graph.Chunk
$pause=(Get-QuestNode $graph 1).DeepCopy()
foreach($s in $pause.Sockets){$s.Chunk.Connections.Clear()}
$conditions=$pause.Condition.Chunk.Conditions
$removed=0
for($i=$conditions.Count-1;$i -ge 0;$i--){
 $c=$conditions[$i].Chunk
 if($c.GetType().Name -eq 'questFactsDBCondition' -and $c.Type.Chunk.GetType().Name -eq 'questVarComparison_ConditionType' -and $c.Type.Chunk.FactName.ToString() -eq 'PTFRBM42_Enabled'){
  if($c.Type.Chunk.Value.ToString() -ne '1'){throw 'Unexpected C5 opt-in guard'}
  $conditions.RemoveAt($i);$removed++
 }
}
if($removed -ne 1 -or $file.RootChunk.PhasePrefabs.Count -ne 0){throw 'Unexpected C5 gate foundation'}
$graph.Nodes.Clear()
Add-RedHandle $graph.Nodes (New-InputNode 0 'In1')
Add-RedHandle $graph.Nodes $pause
Add-RedHandle $graph.Nodes (New-SetFactNode 2 'PTFRBM42_Enabled' 1)
Add-RedHandle $graph.Nodes (New-OutputNode 3 'Out1')
foreach($edge in @(@(0,1),@(1,2),@(2,3))){
 [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $edge[0]) 'Out') (Get-QuestSocket (Get-QuestNode $graph $edge[1]) 'In'))
}
$depot='towercontinued\red_dirt_auto\bootstrap.questphase'
Write-Cr2wFile $file (Join-Path $source $depot)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $depot)) (Join-Path $audit 'bootstrap.json')
$crc=65535
foreach($byte in [Text.Encoding]::UTF8.GetBytes($depot+':1')){
 $x=($crc -shr 8) -bxor $byte;$x=$x -bxor ($x -shr 4)
 $crc=(($crc -shl 8) -bxor ($x -shl 12) -bxor ($x -shl 5) -bxor $x) -band 65535
}
$ep1=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\ep1.quest')
if(@($ep1.RootChunk.Graph.Chunk.Nodes|Where-Object {$_.Chunk.Id.ToString() -eq "$crc"}).Count){throw 'Parent ID collision'}
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load()
$archive=Join-Path $build 'TowerContinued_RedDirt_Auto.archive'
$stream=[IO.File]::Create($archive)
try{
 $writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hash,[WolvenKit.SerilogWrapper]::new())
 if(-not $writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Archive write failed'}
}finally{$stream.Dispose()}
$reader=[WolvenKit.RED4.Archive.IO.ArchiveReader]::new();$packed=$null
if($reader.ReadArchive($archive,$hash,[ref]$packed).ToString() -ne 'NoError'){throw 'Archive reopen failed'}
if($packed.Files.Count -ne 1 -or @($packed.Files.Values)[0].Name -ne $depot){throw 'Unexpected packed resources'}
Copy-Item (Join-Path $WorkspaceRoot 'archive\b0_red_dirt_auto\TowerContinued_RedDirt_Auto.archive.xl') ($archive+'.xl') -Force
$manifest=@{status='AUTOMATIC_CANDIDATE';archive_sha256=(Get-FileHash $archive).Hash;registration_id=$crc;resource=$depot;writer='PTFRBM42_Enabled=1';existing_owner_preserved=$true;scene_or_prefab_added=$false;vanilla_replacements=@();runtime_polling_added=$false}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($manifest|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
$manifest|ConvertTo-Json
