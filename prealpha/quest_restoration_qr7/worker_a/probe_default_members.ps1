param([Parameter(Mandatory=$true)][string]$Output)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$w=(Get-Location).Path
. (Join-Path $w 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $w 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
if(Test-Path -LiteralPath $Output){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $Output|Out-Null
$p=Join-Path $w 'prealpha/quest_restoration_qr7/shared/actor_providers_01/provider_3.streamingsector'
$expected='2BCB4243CDD2CF5DAE17AFFAA15063B96330690146AA1821EAD071F4B4A7B9CF'
if((Get-FileHash -LiteralPath $p).Hash -ne $expected){throw 'Input drift'}
$records=@()
# EventArgs is deliberately empty in WK9.1. Refuse each successive event once
# to get CR2WReader's exact member exception, without changing the library.
for($n=0;$n -le 11;$n++){
 $script:acceptedLimit=$n;$script:eventCount=0;$script:types=[Collections.Generic.List[string]]::new()
 $stream=[IO.File]::OpenRead($p)
 $errorText=$null;$result=$null
 try{
  $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
  $reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) $script:eventCount++;$script:types.Add($e.GetType().FullName);return (($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs]) -and $script:eventCount -le $script:acceptedLimit)})
  $file=$null;$result=$reader.ReadFile([ref]$file,$true).ToString()
 }catch{$ex=$_.Exception;while($null -ne $ex.InnerException){$ex=$ex.InnerException};$errorText=$ex.Message}
 finally{$stream.Dispose()}
 $records+=@{accepted_before_refusal=$n;event_count=$script:eventCount;types=@($script:types);status=$result;exact_refused_member_error=$errorText}
 if($n -lt 11 -and $null -eq $errorText){throw 'Unexpected event count'}
 if($n -eq 11 -and $result -ne 'NoError'){throw 'Full narrow decode failed'}
}
@{scope='Current EP1 provider exact accepted-member identification by bounded sequential refusal; no source writes';source=$p;source_sha256=$expected;records=$records;script_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash}|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $Output 'evidence.json') -Encoding utf8NoBOM
Write-Output 'Enumerated all eleven current EP1 default mismatch members'
