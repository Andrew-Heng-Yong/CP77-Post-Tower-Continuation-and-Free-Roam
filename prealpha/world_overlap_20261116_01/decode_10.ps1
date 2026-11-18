param([string]$Capture='sources_01',[string]$Name='decoded_10_01',[switch]$AcceptSerializedDefaults)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($Capture -cnotmatch '^[a-z][a-z0-9_]+$' -or $Name -cnotmatch '^[a-z][a-z0-9_]+$'){throw 'Invalid evidence name'}
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $PSScriptRoot ('work/'+$Name)
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
$tool=Join-Path $PSScriptRoot 'work/tooling/wolvenkit_10_0_0_beta_1/package'
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot $tool
$hashNames=[WolvenKit.Common.Services.HashService]::new();$hashNames.Load()
function ReadCaptured([string]$path){
 $stream=[IO.File]::OpenRead($path)
 try{
  $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
  $script:defaultCount=0
  if($AcceptSerializedDefaults){
   # Author's ReadVariable has already decoded the complete value here and
   # subsequently assigns that same value. This accepts its presence when
   # equal to the generated default; it does not substitute or skip data.
   $reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($eventArgs)
    if($eventArgs -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs]){$script:defaultCount++;return $true}
    return $false
   })
  }
  $file=$null
  if($reader.ReadFile([ref]$file,$true).ToString() -cne 'NoError'){throw 'Resource read failed'}
  return $file
 }finally{$stream.Dispose()}
}
$inputs=Get-Content -LiteralPath (Join-Path $PSScriptRoot ('work/'+$Capture+'/providers.json')) -Raw|ConvertFrom-Json
[void][IO.Directory]::CreateDirectory($out)
$rows=@(foreach($row in $inputs.hits){
 if(-not $row.depot.EndsWith('.streamingsector')){continue}
 if((Get-FileHash -LiteralPath $row.raw).Hash -cne $row.sha256){throw 'Captured input drift'}
 $dest=Join-Path $out (([IO.Path]::GetFileNameWithoutExtension($row.archive))+'/'+$row.depot+'.json')
 [void][IO.Directory]::CreateDirectory((Split-Path $dest -Parent))
 $item=@{depot=$row.depot;archive=$row.archive;raw=$row.raw;sha256=$row.sha256;json=$null;json_sha256=$null;decode_error=$null;serialized_default_events=0}
 try{Export-Cr2wJson (ReadCaptured $row.raw) $dest;$item.json=$dest;$item.json_sha256=(Get-FileHash -LiteralPath $dest).Hash;$item.serialized_default_events=$script:defaultCount}
 catch{$item.decode_error=$_.Exception.ToString()}
 $item
})
@{tool='WolvenKit 10.0.0-beta.1';tool_red4_sha256=(Get-FileHash -LiteralPath (Join-Path $tool 'WolvenKit.RED4.dll')).Hash;source_capture=$Capture;rows=$rows;game_writes=0}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8NoBOM
Write-Output ("Exported {0} of {1} sectors with the 2.5 reader" -f @($rows|Where-Object {$_.json}).Count,$rows.Count)
