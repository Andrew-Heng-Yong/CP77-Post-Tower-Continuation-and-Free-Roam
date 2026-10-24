$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$outRoot=Join-Path $PSScriptRoot 'candidate_01/diagnosis_01'
$wk=Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package'
foreach($a in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')){[void][Reflection.Assembly]::LoadFrom((Join-Path $wk $a))}
$out=Join-Path $outRoot 'saved_systems_01'
if(Test-Path -LiteralPath $out){throw 'Use a successor output'}
[void][IO.Directory]::CreateDirectory($out)
foreach($slot in @('AutoSave-11','AutoSave-12')){
 $source=Join-Path $ws "recovery/h10_h2_diagnosis_01/$slot/sav.dat"
 $before=(Get-FileHash -LiteralPath $source).Hash
 $stream=[IO.File]::Open($source,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
 try{
  $reader=[WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($stream);$save=$null
  if($reader.ReadFile([ref]$save).ToString() -ne 'NoError'){throw 'Save parse failed'}
  $package=($save.Nodes|Where-Object Name -eq 'ScriptableSystemsContainer').Value.Content
  $index=[Collections.Generic.List[object]]::new();$i=0
  foreach($chunk in $package.Chunks){
   $type=$chunk.GetType().FullName
   if($chunk -is [WolvenKit.RED4.Types.IDynamicClass]){$type=$chunk.ClassName.ToString()}
   $index.Add(@{index=$i;type=$type})
   if($type -match 'PTFR.*(PreAlpha|Profile|BodyPolicy|CyberwarePolicy|Housing|CameraOptics)|PlayerDevelopmentSystem'){
    $options=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
    $json=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($chunk,$options)
    $safe=$type -replace '[^A-Za-z0-9_.-]','_'
    [IO.File]::WriteAllText((Join-Path $out "$slot.$safe.json"),$json,[Text.UTF8Encoding]::new($false))
   }
   $i++
  }
  [IO.File]::WriteAllText((Join-Path $out "$slot.index.json"),($index.ToArray()|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
  Write-Output "${slot}: $($index.Count) scriptable chunks inspected"
 }finally{$stream.Dispose()}
 if((Get-FileHash -LiteralPath $source).Hash -ne $before){throw 'Backup changed'}
}
