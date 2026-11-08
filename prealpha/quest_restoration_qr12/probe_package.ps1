# Narrow managed read-only parser-surface probe, no writer/game API.
$ErrorActionPreference='Stop';$taskRoot=$PSScriptRoot;$dest=Join-Path $taskRoot 'package_probe_01.json'
if(Test-Path -LiteralPath $dest){throw 'Fresh output only'}
$wk='C:\Users\Ayong\Documents\WolvenKit-8.20.0';foreach($a in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')){[void][Reflection.Assembly]::LoadFrom((Join-Path $wk $a))}
$source='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077\ManualSave-24\sav.dat';$before=(Get-FileHash -LiteralPath $source).Hash
$fs=[IO.File]::Open($source,[IO.FileMode]::Open,[IO.FileAccess]::Read,([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete));$ms=[IO.MemoryStream]::new();try{$fs.CopyTo($ms)}finally{$fs.Dispose()};$ms.Position=0
try{
 $save=$null;$reader=[WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($ms);$result=$reader.ReadFile([ref]$save).ToString();if($result -ne 'NoError'){throw $result}
 $pkg=($save.Nodes|Where-Object Name -eq 'ScriptableSystemsContainer').Value.Content
 $properties=@($pkg.GetType().GetProperties()|ForEach-Object {@{name=$_.Name;type=$_.PropertyType.FullName}})
 $chunks=@();if($pkg.PSObject.Properties.Name -contains 'Chunks'){
  foreach($c in $pkg.Chunks){$fields=@($c.GetType().GetProperties()|ForEach-Object {@{name=$_.Name;type=$_.PropertyType.FullName}});$name=if($c.PSObject.Properties.Name -contains 'ClassName'){[string]$c.ClassName}else{$c.GetType().FullName};$chunks+=,@{name=$name;type=$c.GetType().FullName;properties=$fields}}
 }
 $debug=($save.Nodes|Where-Object Name -eq 'questSystem').Children|Where-Object Name -eq 'questDebugLogManager'
 $lines=if($debug){@($debug.Value.Lines)}else{@()}
 $output=@{source=$source;sha256=$before;parse=$result;content_type=$pkg.GetType().FullName;properties=$properties;chunks=$chunks;debug_lines=$lines;limits='In-memory saved representation, not executing-owner proof'}
}finally{$ms.Dispose()}
if((Get-FileHash -LiteralPath $source).Hash -cne $before){throw 'Source drift'}
[IO.File]::WriteAllText($dest,($output|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
