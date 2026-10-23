param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [switch]$ValidateOnly
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$audit=Join-Path $workspace 'research\misty_viktor_world'
if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Close Cyberpunk before rollback'}
$receipt=Get-Content (Join-Path $audit 'lighting_r8_install_receipt.json') -Raw|ConvertFrom-Json
if($receipt.status -ne 'INSTALLED_R8_AUTOMATIC_LIVE_PENDING' -or $receipt.files.Count -ne 5 -or $receipt.s1_recovered.Count -ne 3){throw 'R8 receipt changed'}
$recovery=Join-Path $audit 'rollback_r8_to_s1'
$entries=[Collections.Generic.List[object]]::new()
foreach($item in $receipt.files){
 $from=[IO.Path]::GetFullPath((Join-Path $game $item.relative))
 $to=[IO.Path]::GetFullPath((Join-Path $recovery $item.relative))
 if(-not $from.StartsWith($game+'\',[StringComparison]::OrdinalIgnoreCase) -or -not $to.StartsWith($workspace+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Rollback path escaped root'}
 if((Get-FileHash -LiteralPath $from).Hash -ne $item.sha256 -or (Test-Path -LiteralPath $to)){throw ('R8 target changed or backup exists: '+$from)}
 $entries.Add([pscustomobject]@{from=$from;to=$to;sha=$item.sha256})
}
$restore=[Collections.Generic.List[object]]::new()
foreach($item in $receipt.s1_recovered){
 $from=[IO.Path]::GetFullPath((Join-Path $receipt.s1_recovery_root $item.relative))
 $to=[IO.Path]::GetFullPath((Join-Path $game $item.relative))
 if(-not $from.StartsWith($workspace+'\',[StringComparison]::OrdinalIgnoreCase) -or -not $to.StartsWith($game+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'S1 restore path escaped root'}
 if((Get-FileHash -LiteralPath $from).Hash -ne $item.sha256 -or (Test-Path -LiteralPath $to)){throw ('S1 recovery changed or destination exists: '+$from)}
 $restore.Add([pscustomobject]@{from=$from;to=$to;sha=$item.sha256})
}
$rollbackReceipt=Join-Path $audit 'lighting_r8_rollback_receipt.json'
if(Test-Path -LiteralPath $rollbackReceipt){throw 'Rollback receipt already exists'}
if($ValidateOnly){@{status='ROLLBACK_VALIDATED_NO_CHANGES';r8_files=$entries.Count;s1_files=$restore.Count;game_closed=$true}|ConvertTo-Json;return}
foreach($item in $entries){
 if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game started during rollback'}
 New-Item -ItemType Directory -Path (Split-Path -Parent $item.to) -Force|Out-Null
 Move-Item -LiteralPath $item.from -Destination $item.to -ErrorAction Stop
 if((Get-FileHash -LiteralPath $item.to).Hash -ne $item.sha){throw ('R8 recovery readback failed: '+$item.to)}
}
foreach($item in $restore){
 if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game started during rollback'}
 New-Item -ItemType Directory -Path (Split-Path -Parent $item.to) -Force|Out-Null
 Move-Item -LiteralPath $item.from -Destination $item.to -ErrorAction Stop
 if((Get-FileHash -LiteralPath $item.to).Hash -ne $item.sha){throw ('S1 restore readback failed: '+$item.to)}
}
$data=@{status='ROLLED_BACK_R8_TO_S1';utc=[DateTime]::UtcNow.ToString('o');r8_recovery=$recovery;r8_files=$entries.Count;s1_files=$restore.Count;deleted_files=0;save_files_modified=$false}
[IO.File]::WriteAllText($rollbackReceipt,($data|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
$data|ConvertTo-Json
