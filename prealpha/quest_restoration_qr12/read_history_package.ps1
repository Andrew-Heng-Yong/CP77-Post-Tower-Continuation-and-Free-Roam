param([string]$SaveName='ManualSave-24',[string]$Tag='history_package_01')
# Saved managed object -> fresh JSON only; no save serializer/writer is created.
$ErrorActionPreference='Stop';if($SaveName -notmatch '^(ManualSave|AutoSave)-\d+$' -or $Tag -notmatch '^[A-Za-z0-9_]{1,80}$' -or $Tag -match '^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$'){throw 'Bounded save/non-device tag required'}
$dest=Join-Path $PSScriptRoot ($Tag+'.json');if(Test-Path -LiteralPath $dest){throw 'Fresh output only'}
$wk='C:\Users\Ayong\Documents\WolvenKit-8.20.0';foreach($a in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')){[void][Reflection.Assembly]::LoadFrom((Join-Path $wk $a))}
if((Get-FileHash -LiteralPath (Join-Path $wk 'WolvenKit.RED4.dll')).Hash -cne 'E607F058C74822B157CAE97F827310C4353CB323D440AE1E3A591307717645FD'){throw 'Parser drift'}
$source=Join-Path 'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077' ($SaveName+'/sav.dat');$before=(Get-FileHash -LiteralPath $source).Hash
$ms=[IO.MemoryStream]::new();$fs=[IO.File]::Open($source,[IO.FileMode]::Open,[IO.FileAccess]::Read,([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete));try{$fs.CopyTo($ms)}finally{$fs.Dispose()};$ms.Position=0
if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($ms.ToArray())) -cne $before){$ms.Dispose();throw 'Unstable in-memory snapshot'}
$rows=@();try{
 $save=$null;$result=([WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($ms)).ReadFile([ref]$save).ToString();if($result -ne 'NoError'){throw $result}
 $pkg=($save.Nodes|Where-Object Name -eq 'ScriptableSystemsContainer').Value.Content
 foreach($chunk in $pkg.Chunks){
  $name=if($chunk.PSObject.Properties.Name -contains 'ClassName'){[string]$chunk.ClassName}else{$chunk.GetType().FullName}
  if($name -match '^PTFR\.(HistorySnapshotHS1|ActivityStateR3|GigsU10|SideJobsS2)\.'){
   $opts=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
   $text=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($chunk,$opts)
   $rows+=,@{class=$name;decoded_json=$text;interpretation='Serialized saved fields only; native executing-owner/liveness not established'}
  }
 }
}finally{$ms.Dispose()}
if((Get-FileHash -LiteralPath $source).Hash -cne $before){throw 'Save changed during inspection'}
[IO.File]::WriteAllText($dest,(@{source=$source;sha256=$before;rows=$rows;save_writes=0}|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
