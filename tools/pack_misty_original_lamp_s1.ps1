param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$alias=Get-Content (Join-Path $audit 'original_lamp_alias_s1_manifest.json') -Raw|ConvertFrom-Json
$controller=Get-Content (Join-Path $audit 'original_lamp_s1_controller_manifest.json') -Raw|ConvertFrom-Json
if($alias.status -ne 'BUILT_SINGLETON_ORIGINAL_ALIAS_SOURCE_ONLY_NOT_INSTALLED' -or $controller.status -ne 'BUILT_SINGLETON_ORIGINAL_CONTROLLER_SOURCE_ONLY_NOT_INSTALLED' -or $alias.alias -ne $controller.alias){throw 'Singleton source manifests changed'}
if((Get-FileHash -LiteralPath $alias.target).Hash -ne $alias.target_sha256){throw 'Alias target changed'}
$out=Join-Path $WorkspaceRoot 'build\MistyOriginalLampAliasS1'
$source=Join-Path $out 'source'
$phasePath=Join-Path $source $controller.phase_depot
if((Get-FileHash -LiteralPath $phasePath).Hash -ne $controller.phase_sha256){throw 'Controller source changed'}
$expected=@($alias.source_depot,$controller.phase_depot)
$actual=@(Get-ChildItem -LiteralPath $source -File -Recurse | ForEach-Object {$_.FullName.Substring($source.Length+1)})
if(@(Compare-Object @($expected|Sort-Object) @($actual|Sort-Object)).Count){throw 'Singleton archive source contains unexpected resources'}
$crc=65535
foreach($byte in [Text.Encoding]::UTF8.GetBytes($controller.phase_depot+':1')){
 $x=($crc -shr 8) -bxor $byte;$x=$x -bxor ($x -shr 4)
 $crc=(($crc -shl 8) -bxor ($x -shl 12) -bxor ($x -shl 5) -bxor $x) -band 65535
}
$parent=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\ep1.quest')
if(@($parent.RootChunk.Graph.Chunk.Nodes|Where-Object {$_.Chunk.Id.ToString() -eq "$crc"}).Count){throw 'Native parent registration ID collision'}
$xl=@('quest:','  phases:',"    - path: $($controller.phase_depot)",'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out')
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load()
$archivePath=Join-Path $out 'TowerContinued_MistyOriginalLampAliasS1.archive'
$stream=[IO.File]::Create($archivePath)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hash,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Singleton archive pack failed'}}finally{$stream.Dispose()}
[IO.File]::WriteAllLines(($archivePath+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archivePath,$hash,[ref]$packed).ToString() -ne 'NoError'){throw 'Singleton archive reopen failed'}
if(@(Compare-Object @($expected|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Singleton archive packed unexpected resources'}
$probe=Join-Path $WorkspaceRoot 'diagnostics\PTFR_MistyViktor_Original_Lamp_S1\init.lua'
$manifest=[ordered]@{
 status='BUILT_SINGLETON_ORIGINAL_LAMP_NOT_INSTALLED_OR_LIVE'
 archive=$archivePath;sha256=(Get-FileHash $archivePath).Hash
 xl=$archivePath+'.xl';xl_sha256=(Get-FileHash ($archivePath+'.xl')).Hash
 probe=$probe;probe_sha256=(Get-FileHash $probe).Hash
 resources=$expected;phase_depot=$controller.phase_depot;registration_id=$crc
 alias=$alias.alias;source_sector_sha256=$alias.source_sha256
 original_sector_override=$alias.source_depot;original_placement_alias_writes=1
 original_light_properties_changed=0;original_variant_writes=0;story_fact_writes=0
 native_nodes=33;installed=$false;live_tested=$false
}
[IO.File]::WriteAllText((Join-Path $audit 'original_lamp_s1_package_manifest.json'),($manifest|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
[pscustomobject]$manifest|Select-Object status,sha256,resources,native_nodes,registration_id|ConvertTo-Json
