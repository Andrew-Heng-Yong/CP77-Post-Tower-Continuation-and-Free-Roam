param([string]$WorkspaceRoot=(Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path)
$ErrorActionPreference='Stop'
$savePath='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077\AutoSave-0\sav.dat'
$out=Join-Path $WorkspaceRoot 'research/postending_pa6/rogue/autosave0_fixture.json'
if(Test-Path -LiteralPath $out){throw 'Refusing overwrite'}
foreach($a in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')){[void][Reflection.Assembly]::LoadFrom((Join-Path 'C:\Users\Ayong\Documents\WolvenKit-8.20.0' $a))}
$toHash=[WolvenKit.RED4.Save.Fact].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32]}
$wanted=@{};$values=[ordered]@{}
$names=@('PTFRAL8_RStart','PTFRAL8_RActive','PTFRAL8_RRequests','PTFRAL8_RAvailable','PTFRAL8_RContinue','PTFRAL8_RDeparted','PTFRAL8_Ready','PTFRAL1_Actor27Ready','PTFRAL1_WorldApplied','PTFRPA2_Finished','PTFRPA5_OpticsDone')
foreach($name in $names){$fact=[WolvenKit.RED4.Save.Fact]::op_Implicit($name);$key=[uint32]$toHash.Invoke($null,[object[]]@($fact));$wanted[$key]=$name;$values[$name]=@()}
$before=(Get-FileHash -LiteralPath $savePath).Hash
$stream=[IO.File]::Open($savePath,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
try{
 $reader=[WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($stream);$save=$null
 if($reader.ReadFile([ref]$save).ToString() -ne 'NoError'){throw 'Parse failed'}
 function WalkNodes($nodes){foreach($node in $nodes){
  if($node.Value -is [WolvenKit.RED4.Save.FactsTable]){foreach($entry in $node.Value.FactEntries){$key=[uint32]$script:toHash.Invoke($null,[object[]]@($entry.FactName));if($script:wanted.ContainsKey($key)){$name=$script:wanted[$key];$script:values[$name]+=([uint32]$entry.Value)}}}
  if($node.Children.Count){WalkNodes $node.Children}
 }}
 WalkNodes $save.Nodes
}finally{$stream.Dispose()}
if((Get-FileHash -LiteralPath $savePath).Hash -ne $before){throw 'Save changed'}
$meta=(Get-Content -LiteralPath (Join-Path (Split-Path $savePath) 'metadata.9.json') -Raw|ConvertFrom-Json).Data.metadata
$position=$meta.playerPosition
$distance=[Math]::Sqrt([Math]::Pow(($position.X+1421.31909),2)+[Math]::Pow(($position.Y-1012.98596),2)+[Math]::Pow(($position.Z-16.8802929),2))
$report=[ordered]@{status='READ_ONLY_FIXTURE_CANDIDATE_NOT_SERIALIZED_OWNER_PROOF';slot=$meta.name;timestamp=$meta.timestampString;level=$meta.level;save_sha256=$before;position=$position;distance_to_rogue_booth_m=$distance;rogue_admission_range_m=12;rogue_continue_range_m=32;facts=$values;source_unchanged=$true;interpretation='Position is outside Rogue start/continue range and save timestamp precedes Emmerick warning and Rogue crash by14/27seconds. Serialized RActive0/RDeparted1, actorReady1/worldApplied1 and Finished1 support a post-ending pre-approach fixture; request/start facts absent means not serialized, not live zero. Suitable candidate; no native serialized-owner reconstruction claimed.'}
[IO.File]::WriteAllText($out,($report|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
$report|ConvertTo-Json -Depth 8
