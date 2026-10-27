Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$wk=Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package'
foreach($a in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')){[void][Reflection.Assembly]::LoadFrom((Join-Path $wk $a))}
$out=Join-Path $PSScriptRoot 'diagnostics_01/scriptable_01'
if(Test-Path -LiteralPath $out){throw 'Preserve diagnostic output'}
[void][IO.Directory]::CreateDirectory($out)
$source='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077\AutoSave-19\sav.dat'
$before=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
$stream=[IO.File]::Open($source,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite)
try{
 $save=$null;$result=([WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($stream)).ReadFile([ref]$save).ToString()
 if($result -ne 'NoError'){throw $result}
 $package=($save.Nodes|Where-Object Name -eq 'ScriptableSystemsContainer').Value.Content
 $index=[Collections.Generic.List[object]]::new();$i=0
 foreach($chunk in $package.Chunks){
  $type=$chunk.GetType().FullName
  if($chunk -is [WolvenKit.RED4.Types.IDynamicClass]){$type=$chunk.ClassName.ToString()}
  $index.Add(@{index=$i;type=$type})
  if($type -match 'PTFR.HistorySnapshotHS1.SnapshotStateHS1|PTFR.SideJobsS23.SideJobsS23'){
   $json=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($chunk,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
   $safe=$type -replace '[^A-Za-z0-9_.-]','_'
   [IO.File]::WriteAllText((Join-Path $out ($safe+'.json')),$json,[Text.UTF8Encoding]::new($false))
  }
  $i++
 }
 [IO.File]::WriteAllText((Join-Path $out 'index.json'),($index.ToArray()|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
 @{status='READ_ONLY';chunks=$index.Count;selected=@($index|Where-Object {$_.type -match 'PTFR.HistorySnapshotHS1.SnapshotStateHS1|PTFR.SideJobsS23.SideJobsS23'})}|ConvertTo-Json -Depth 5
}finally{$stream.Dispose()}
if((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -cne $before){throw 'Save changed during read'}
