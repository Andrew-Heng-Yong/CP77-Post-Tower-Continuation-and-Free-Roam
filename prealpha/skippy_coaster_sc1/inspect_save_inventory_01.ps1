Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$wk='C:\Users\Ayong\Documents\WolvenKit-8.20.0'
foreach($a in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')){[void][Reflection.Assembly]::LoadFrom((Join-Path $wk $a))}
$p='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077\AutoSave-19\sav.dat'
$before=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash
$s=[IO.File]::Open($p,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite)
try{$save=$null;$r=([WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($s)).ReadFile([ref]$save).ToString();if($r -ne 'NoError'){throw $r}
 $nodes=@($save.Nodes|Where-Object {$_.Value -is [WolvenKit.RED4.Save.Inventory]})
 $rows=@()
 foreach($node in $nodes){foreach($sub in $node.Value.SubInventories){foreach($item in $sub.Items){
  $rows+=@{node=$node.Name;inventory=$sub.InventoryId.ToString();itemid=$item.ItemInfo.ItemId.Id.ToString();quantity=$item.Quantity.ToString()}
 }}}
 $target=[WolvenKit.RED4.Types.TweakDBID]::op_Implicit('Items.mq007_skippy').ToString()
 $signature=($target -split 'TweakDBID ')[1].Split(' ')[0]
 @{nodes=$nodes.Count;total_items=$rows.Count;target=$target;sample=@($rows|Select-Object -First 4);matches=@($rows|Where-Object {$_.itemid -like ('*'+$signature+'*')})}|ConvertTo-Json -Depth 8
}finally{$s.Dispose()}
if((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -cne $before){throw 'Save changed'}
