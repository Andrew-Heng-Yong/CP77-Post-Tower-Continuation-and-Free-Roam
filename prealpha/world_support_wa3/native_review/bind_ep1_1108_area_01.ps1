$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $PSScriptRoot 'ep1_1108_area_01';[void][IO.Directory]::CreateDirectory($out)
foreach($raw in @((Join-Path $PSScriptRoot '../extracted_01/ep1_1_nightcity.archive/always_loaded_1.streamingsector'),(Join-Path $PSScriptRoot '../extracted_01/basegame_3_nightcity.archive/always_loaded_1.streamingsector'))){
 $s=[IO.File]::OpenRead($raw)
 try{$r=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($s);$r.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e)return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])});$f=$null;if($r.ReadFile([ref]$f,$true).ToString() -ne 'NoError'){throw 'Read failed'}
 $count=0;foreach($h in $f.RootChunk.Nodes){$n=$h.Chunk;if($n.GetType().Name -like 'worldCompiledCommunityAreaNode*'){$count++;if($n.SourceObjectId.Hash.ToString() -eq '16139198176876474021'){$p=Join-Path $out ((Split-Path (Split-Path $raw -Parent) -Leaf)+'.json');[IO.File]::WriteAllText($p,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($n,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()));Write-Output $p}}};Write-Output "areas $count"
 }finally{$s.Dispose()}
}
