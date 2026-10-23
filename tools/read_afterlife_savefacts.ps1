param([string]$SavePath='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077\AutoSave-10\sav.dat',[string]$OutputPath='research/afterlife_world/afterlife_save_facts.json')
$ErrorActionPreference='Stop'
foreach($a in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')){[void][Reflection.Assembly]::LoadFrom((Join-Path 'C:\Users\Ayong\Documents\WolvenKit-8.20.0' $a))}
$names=@('PostTowerFreeRoamActive','PTFRP0_DR13','q307_active','q307_done','q307_finished','q307_2079','q307_main_game_killed','q307_ep1_killed','q103_active','q115_active','q203_active','q115_point_of_no_return','rogue_default_on','rogue_default_holo','q116_rogue_dead','q103_rogue_met','sq031_rogue_met_johnny','q005_disable_emmerick_oneliner','nix_default_on','nix_dd_holo','mq016_active','mq016_done','mq016_saved_life','mq016_hacked','PTFRB0S4NIX_Ready','PTFRB0S4NIX_Enabled','PTFRB0S4NIX_OwnerActive','PTFRB0S4NIX_OwnerStarts','PTFRB0S4NIX_SceneRequests','PTFRB0S4NIX_QuestOwns')
$toHash=[WolvenKit.RED4.Save.Fact].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32]}
$wanted=@{};$values=[ordered]@{}
foreach($name in $names){$fact=[WolvenKit.RED4.Save.Fact]::op_Implicit($name);$key=[uint32]$toHash.Invoke($null,[object[]]@($fact));$wanted[$key]=$name;$values[$name]=@()}
$before=(Get-FileHash -LiteralPath $SavePath).Hash
$stream=[IO.File]::Open($SavePath,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
try{
 $reader=[WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($stream);$save=$null
 if($reader.ReadFile([ref]$save).ToString() -ne 'NoError'){throw 'Save parse failed'}
 function WalkNodes($nodes){foreach($node in $nodes){
  if($node.Value -is [WolvenKit.RED4.Save.FactsTable]){foreach($entry in $node.Value.FactEntries){$key=[uint32]$script:toHash.Invoke($null,[object[]]@($entry.FactName));if($script:wanted.ContainsKey($key)){$name=$script:wanted[$key];$script:values[$name]+=([uint32]$entry.Value)}}}
  if($node.Children.Count){WalkNodes $node.Children}
 }}
 WalkNodes $save.Nodes
}finally{$stream.Dispose()}
if((Get-FileHash -LiteralPath $SavePath).Hash -ne $before){throw 'Save changed during read'}
$report=[ordered]@{status='READ_ONLY_SAVE_SAMPLE_NOT_CURRENT_RUNTIME';source=$SavePath;sha256=$before;unchanged=$true;facts=$values;note='Empty arrays mean absent from serialized tables, not proof of a live runtime value. Multiple table values are retained rather than guessing precedence.'}
[IO.File]::WriteAllText((Join-Path (Get-Location) $OutputPath),($report|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
$report|ConvertTo-Json -Depth 6
