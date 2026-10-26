Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$O=Join-Path $PSScriptRoot 'research_01';if(Test-Path $O){throw 'Use successor'}
New-Item -ItemType Directory -Path $O|Out-Null
$G='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$rows=@();$refs=@()
$files=@(Get-ChildItem -LiteralPath (Join-Path $G 'archive/pc/mod') -Filter '*Tower*.archive')+@(Get-Item -LiteralPath (Join-Path $G 'archive/pc/content/basegame_4_gamedata.archive'))
foreach($p in $files){
 $a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($p.FullName,$hs,[ref]$a).ToString() -ne 'NoError'){throw 'Archive read failed'}
 foreach($e in $a.Files.Values){
  $dep=$e.Name
  if($dep -notmatch '^base\\quest\\holocalls\\dennis\\.*\.(questphase|scene)$' -and $dep -notin @('base\quest\holocalls\holocall_initializers.questphase','base\quest\holocalls\holocall_cleanup.questphase','towercontinued\sidejobs_s23\base_b\mq038.questphase','towercontinued\gig_phone_u9\fixer_cleanup.questphase')){continue}
  $raw=Join-Path $O ($p.BaseName+'/'+$dep);New-Item -ItemType Directory -Force -Path (Split-Path $raw -Parent)|Out-Null
  $s=[IO.File]::Create($raw);try{$e.Extract($s)}finally{$s.Dispose()}
  Export-Cr2wJson (Read-Cr2wFile $raw) ($raw+'.json')
  $rows+=@{archive=$p.FullName;depot=$dep;raw=[IO.Path]::GetRelativePath($W,$raw).Replace('\','/');sha256=(Get-FileHash $raw).Hash}
 }
}
$rows|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $O 'inventory.json') -Encoding utf8
Copy-Item -LiteralPath (Join-Path $G 'bin/x64/plugins/cyber_engine_tweaks/gamelog.log') -Destination (Join-Path $O 'gamelog.log')
$raw=Join-Path $W 'research/sidejobs_s28/vehicles/world_03/raw/ep1_1_nightcity_always_loaded_1.streamingsector'
$s=[IO.File]::OpenRead($raw)
try{
 $r=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($s)
 $r.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e)return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])})
 $f=$null;if($r.ReadFile([ref]$f,$true).ToString() -ne 'NoError'){throw 'World parse failed'}
 $bytes=$f.RootChunk.NodeData.Buffer.GetBytes();$i=0
 foreach($d in $f.RootChunk.NodeData.Data){
  $idx=[int]([BitConverter]::ToUInt64($bytes,$i*0x90+0x70) -band 0x7FFFF);$n=$f.RootChunk.Nodes[$idx].Chunk
  if($n.DebugName.ToString() -match '(?i)judy|sq026.*door|door.*sq026'){
   $refs+=@{datum=$i;node=$idx;type=$n.GetType().Name;position=@($d.Position.X.ToString(),$d.Position.Y.ToString(),$d.Position.Z.ToString());ref=$d.QuestPrefabRefHash.ToString();payload=([WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($n,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())|ConvertFrom-Json -Depth 100)}
  };$i++
 }
}finally{$s.Dispose()}
$refs|ConvertTo-Json -Depth 100|Set-Content -LiteralPath (Join-Path $O 'judy_world.json') -Encoding utf8
@{resources=$rows.Count;judy_nodes=$refs.Count;game_writes=0;save_writes=0}|ConvertTo-Json
