param([Parameter(Mandatory=$true)][string]$Output)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$w=(Get-Location).Path
. (Join-Path $w 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $w 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
if(Test-Path -LiteralPath $Output){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $Output|Out-Null
$manifest=Get-Content -LiteralPath (Join-Path $w 'prealpha/quest_restoration_qr7/shared/actor_providers_01/manifest.json') -Raw|ConvertFrom-Json
$records=@()
foreach($pin in @($manifest.providers|Where-Object {$_.raw.EndsWith('.streamingsector')})){
 if((Get-FileHash -LiteralPath $pin.raw).Hash -ne $pin.raw_sha256){throw 'Source drift'}
 $script:events=[Collections.Generic.List[object]]::new()
 $stream=[IO.File]::OpenRead($pin.raw)
 try{
  $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
  $reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e)
   $values=@{}
   foreach($p in $e.GetType().GetProperties()){
    try{$v=$p.GetValue($e);$values[$p.Name]=if($null -eq $v){$null}else{[string]$v}}catch{$values[$p.Name]='Unreadable: '+$_.Exception.Message}
   }
   $script:events.Add(@{type=$e.GetType().FullName;properties=$values})
   return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])
  })
  $file=$null
  if($reader.ReadFile([ref]$file,$true).ToString() -ne 'NoError'){throw 'Parse failed'}
 }finally{$stream.Dispose()}
 $registries=@($file.RootChunk.Nodes|Where-Object {$_.Chunk.GetType().Name -eq 'worldCommunityRegistryNode'})
 $entries=@()
 foreach($reg in $registries){foreach($entry in $reg.Chunk.CommunitiesData){
  $name=$entry.Template.Chunk.SpawnSetReference.ToString()
  if($name -notin @('#mr_hands_combat_zone','#mr_hands_holo')){continue}
  $entries+=@{name=$name;characters=@($entry.Template.Chunk.Entries|ForEach-Object {$_.Chunk.CharacterRecordId.ToString()});phases=@($entry.Template.Chunk.Entries|ForEach-Object {@($_.Chunk.Phases|ForEach-Object {$_.Chunk.PhaseName.ToString()})});initial=@($entry.EntriesInitialState|ForEach-Object {@{entry=$_.EntryName.ToString();active=$_.EntryActiveOnStart.ToString();phase=$_.InitialPhaseName.ToString()}})}
 }}
 if($pin.raw.EndsWith('provider_3.streamingsector') -and $entries.Count -ne 2){throw 'EP1 target entries not fully populated'}
 $records+=@{source=$pin.raw;source_sha256=$pin.raw_sha256;accepted_events=@($script:events);populated_target_entries=$entries}
}
@{scope='Read-only exact tolerated event details and populated target registry assertion';records=$records;script_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash}|ConvertTo-Json -Depth 20|Set-Content -LiteralPath (Join-Path $Output 'evidence.json') -Encoding utf8NoBOM
Write-Output 'Recorded exact accepted members and target registry population'
