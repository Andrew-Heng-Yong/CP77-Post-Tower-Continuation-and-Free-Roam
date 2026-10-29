$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
function ReadWorld([string]$path){
 $stream=[IO.File]::OpenRead($path)
 try{$reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream);$reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e)return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])});$file=$null;if($reader.ReadFile([ref]$file,$true).ToString() -cne 'NoError'){throw 'Read failed'};return $file}finally{$stream.Dispose()}
}
$file=ReadWorld (Join-Path $PSScriptRoot '../extracted_01/basegame_3_nightcity.archive/quest_0b5baaafb70a2a64.streamingsector')
$file.RootChunk.NodeData.GetType().GetProperties()|Select-Object Name,CanWrite,PropertyType|Format-Table
$file.RootChunk.NodeData.Buffer.GetType().GetProperties()|Select-Object Name,CanWrite,PropertyType|Format-Table
$file.RootChunk.NodeData.Buffer.GetType().GetMethods()|Where-Object {$_.Name -match 'Set|Bytes|Data'}|ForEach-Object ToString