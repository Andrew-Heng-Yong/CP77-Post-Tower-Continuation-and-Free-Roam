param([string]$SavePath='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077\AutoSave-8\sav.dat',[string]$OutputPath='research/courier_c1/save_probe_01.json')
$ErrorActionPreference='Stop'
if(Test-Path $OutputPath){throw 'Evidence exists'}
$py='C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$names=@((& $py prealpha/courier_c1/research.py facts)|ConvertFrom-Json)+@('ep1_active','ep1_side_content','ep1_installed','PTFRPA2_Finished','PTFRU9_Support_Issued','PTFRU9_Support_Fault')
foreach($a in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')){[void][Reflection.Assembly]::LoadFrom((Join-Path 'C:\Users\Ayong\Documents\WolvenKit-8.20.0' $a))}
$toHash=[WolvenKit.RED4.Save.Fact].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32]}
$wanted=@{};$values=[ordered]@{}
foreach($name in $names|Sort-Object -Unique){$fact=[WolvenKit.RED4.Save.Fact]::op_Implicit($name);$key=[uint32]$toHash.Invoke($null,[object[]]@($fact));$wanted[$key]=$name;$values[$name]=@()}
$before=(Get-FileHash -LiteralPath $SavePath).Hash
$stream=[IO.File]::Open($SavePath,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
try{
 $reader=[WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($stream);$save=$null
 if($reader.ReadFile([ref]$save).ToString() -ne 'NoError'){throw 'Save parse failed'}
 function WalkNodes($nodes){foreach($node in $nodes){
  if($node.Value -is [WolvenKit.RED4.Save.FactsTable]){foreach($entry in $node.Value.FactEntries){$key=[uint32]$script:toHash.Invoke($null,[object[]]@($entry.FactName));if($script:wanted.ContainsKey($key)){$script:values[$script:wanted[$key]]+=([uint32]$entry.Value)}}}
  if($node.Children.Count){WalkNodes $node.Children}
 }}
 WalkNodes $save.Nodes
}finally{$stream.Dispose()}
if((Get-FileHash -LiteralPath $SavePath).Hash -cne $before){throw 'Save changed'}
$report=@{status='READ_ONLY_NOT_LIVE';source=$SavePath;sha256=$before;unchanged=$true;facts=$values;note='Absent serialized facts are not proof of runtime zero.'}
[IO.File]::WriteAllText((Join-Path (Get-Location) $OutputPath),($report|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
$values.GetEnumerator()|Where-Object {$_.Value.Count -and ($_.Key -match 'couriers_active|introduction|courier_outro|hacking_mission|ready_to_start|ep1_active|ep1_side|ep1_installed|courier_holocall_status|courier_car_mounted|courier_loop_blocked|courier_force_despawn|Support_|Finished')}|Format-Table -AutoSize
