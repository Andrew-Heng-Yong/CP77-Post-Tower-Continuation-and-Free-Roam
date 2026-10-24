$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent;$C=Join-Path $PSScriptRoot 'candidate_01'
. (Join-Path $W 'tools/build_phase2a.ps1') -WorkspaceRoot $W -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$raw=Join-Path $W 'research/sidejobs_s28/vehicles/world_03/raw/ep1_1_nightcity_always_loaded_1.streamingsector'
$depot='base\worlds\03_night_city\_compiled\default\always_loaded_1.streamingsector'
$archive='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\ep1\ep1_1_nightcity.archive'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$arc=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$arc).ToString() -ne 'NoError'){throw 'Archive read failed'}
$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot);$mem=[IO.MemoryStream]::new()
try{$arc.Files[$key].Extract($mem);$actual=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()}
if($actual -cne (Get-FileHash $raw).Hash){throw 'World donor changed'}
$s=[IO.File]::OpenRead($raw)
try{
 $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($s)
 $reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e)return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])})
 $file=$null;if($reader.ReadFile([ref]$file,$true).ToString() -ne 'NoError'){throw 'Parse failed'}
 $bytes=$file.RootChunk.NodeData.Buffer.GetBytes();$rows=@();$i=0
 foreach($d in $file.RootChunk.NodeData.Data){
  $x=[double]$d.Position.X.ToString();$y=[double]$d.Position.Y.ToString();$z=[double]$d.Position.Z.ToString()
  if([math]::Abs($x+1383.8) -lt 20 -and [math]::Abs($y-1276.3) -lt 20 -and $z -gt 120 -and $z -lt 130){
   $idx=[int]([BitConverter]::ToUInt64($bytes,$i*0x90+0x70) -band 0x7FFFF);$n=$file.RootChunk.Nodes[$idx].Chunk
   $rows+=@{datum=$i;node=$idx;type=$n.GetType().Name;position=@($x,$y,$z);id=$d.Id.ToString();ref=$d.QuestPrefabRefHash.ToString();node_payload=([WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($n,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())|ConvertFrom-Json -Depth 100)}
  };$i++
 }
 @{source_sha256=$actual;archive=$archive;depot=$depot;rows=$rows}|ConvertTo-Json -Depth 100|Set-Content (Join-Path $C 'anchor_01.json') -Encoding utf8
 $rows|Select-Object datum,node,type,position,ref|ConvertTo-Json -Depth 5
}finally{$s.Dispose()}
