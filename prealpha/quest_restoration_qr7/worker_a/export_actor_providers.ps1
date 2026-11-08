param([Parameter(Mandatory=$true)][string]$Output)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$w=(Get-Location).Path
. (Join-Path $w 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $w 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
if(Test-Path -LiteralPath $Output){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $Output|Out-Null
$manifestPath=Join-Path $w 'prealpha/quest_restoration_qr7/shared/actor_providers_01/manifest.json'
$manifest=Get-Content -LiteralPath $manifestPath -Raw|ConvertFrom-Json
$records=@()
foreach($pin in @($manifest.providers|Where-Object {$_.raw.EndsWith('.streamingsector')})){
 if((Get-FileHash -LiteralPath $pin.raw).Hash -ne $pin.raw_sha256){throw 'Source drift'}
 $script:events=[Collections.Generic.List[object]]::new()
 $stream=[IO.File]::OpenRead($pin.raw)
 try{
  $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
  $reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) $script:events.Add(@{type=$e.GetType().FullName;text=$e.ToString()});return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])})
  $file=$null
  $status=$reader.ReadFile([ref]$file,$true).ToString()
  if($status -ne 'NoError'){throw ('Parse failed '+$status)}
 }finally{$stream.Dispose()}
 $name=[IO.Path]::GetFileName($pin.raw)
 $jp=Join-Path $Output ($name+'.json');$bp=Join-Path $Output ($name+'.nodeData.buffer')
 Export-Cr2wJson $file $jp
 [IO.File]::WriteAllBytes($bp,$file.RootChunk.NodeData.Buffer.GetBytes())
 $records+=@{source_pin=$pin;json=$jp;json_sha256=(Get-FileHash -LiteralPath $jp).Hash;buffer=$bp;buffer_sha256=(Get-FileHash -LiteralPath $bp).Hash;node_definitions=$file.RootChunk.Nodes.Count;node_setups=$file.RootChunk.NodeData.Data.Count;accepted_events=@($script:events)}
}
@{scope='Read-only current provider exports; accept only recorded InvalidDefaultValueEventArgs, no unknown classes or serialization';source_manifest=$manifestPath;source_manifest_sha256=(Get-FileHash -LiteralPath $manifestPath).Hash;records=$records;script_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash}|ConvertTo-Json -Depth 18|Set-Content -LiteralPath (Join-Path $Output 'manifest.json') -Encoding utf8NoBOM
Write-Output ('Fresh actor exports '+$records.Count)
