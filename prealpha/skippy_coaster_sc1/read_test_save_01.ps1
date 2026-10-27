Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $PSScriptRoot 'diagnostics_01'
if(Test-Path -LiteralPath $out){throw 'Preserve diagnostic output'}
[void][IO.Directory]::CreateDirectory($out)
$wk='C:\Users\Ayong\Documents\WolvenKit-8.20.0'
foreach($a in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')){[void][Reflection.Assembly]::LoadFrom((Join-Path $wk $a))}
$names=@('PostTowerFreeRoamActive','PTFRP0_DR13','PTFRPA2_Finished','PTFRPA2_Fault','PTFRU9_Support_Issued','PTFRU9_Support_Fault','PTFRBASE_Suspended','q307_active','q307_done','q307_finished','q307_2079','q307_main_game_killed','q307_ep1_killed','q307_debug_reset','q115_point_of_no_return','q305_johnny_scene_active','PTFRSKIP_Ambient_Ready','PTFRSKIP_Ambient_Request','PTFRSKIP_Ambient_Claimed','PTFRSKIP_Ambient_Entered','PTFRSKIP_Ambient_Stop','PTFRSKIP_Ambient_Stopped','PTFRS23_MQ007_Ready','PTFRS23_MQ007_Permit','PTFRS23_MQ007_Issued','PTFRS23_MQ007_RESUME_Ready','PTFRS23_MQ007_RESUME_Permit','PTFRS23_MQ007_RESUME_Issued','PTFRS23_MQ007_ModeTalkConfirmed','mq007_done','mq007_interrupt_skippy_dialogue','mq007_rapid_interrupt','mq007_skippy_goes_emo','mq007_skippy_enemies_total','mq007_skippy_reload','mq007_skippy_aiming')
$toHash=[WolvenKit.RED4.Save.Fact].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32]}
$wanted=@{};foreach($name in $names){$fact=[WolvenKit.RED4.Save.Fact]::op_Implicit($name);$key=[uint32]$toHash.Invoke($null,[object[]]@($fact));$wanted[$key]=$name}
$root='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077'
foreach($slot in @('AutoSave-18','AutoSave-19')){
 $path=Join-Path $root ($slot+'\sav.dat')
 $before=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
 $stream=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite)
 $values=[ordered]@{};foreach($name in $names){$values[$name]=@()}
 try{
  $save=$null;$result=([WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($stream)).ReadFile([ref]$save).ToString()
  if($result -ne 'NoError'){throw ('Save parse '+$result)}
  function WalkNodes($nodes){foreach($node in $nodes){
   if($node.Value -is [WolvenKit.RED4.Save.FactsTable]){foreach($entry in $node.Value.FactEntries){$key=[uint32]$script:toHash.Invoke($null,[object[]]@($entry.FactName));if($script:wanted.ContainsKey($key)){$name=$script:wanted[$key];$script:values[$name]+=([uint32]$entry.Value)}}}
   if($node.Children.Count){WalkNodes $node.Children}
  }}
  WalkNodes $save.Nodes
 }finally{$stream.Dispose()}
 $after=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
 if($before -cne $after){throw ('Save changed during read '+$slot)}
 $report=[ordered]@{status='READ_ONLY_SERIALIZED_FACTS_NOT_RUNTIME';slot=$slot;sha256=$before;facts=$values;note='Empty fact arrays mean absent from serialized tables; this does not prove current runtime state.'}
 [IO.File]::WriteAllText((Join-Path $out ($slot+'.json')),($report|ConvertTo-Json -Depth 8)+"`n",[Text.UTF8Encoding]::new($false))
}
@{status='READ_ONLY';slots=2;names=$names.Count}|ConvertTo-Json
