param(
 [ValidateSet('Validate','Apply','Verify')][string]$Action='Validate',
 [Parameter(Mandatory=$true)][string]$GameRoot
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
function Hash($p){if(Test-Path -LiteralPath $p -PathType Leaf){return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash};return $null}
function NoLinks($p){$cursor=$p;while($cursor){if((Test-Path -LiteralPath $cursor) -and ((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Linked path refused'};$cursor=Split-Path $cursor -Parent}}
if(Get-Process -Name Cyberpunk2077,REDprelauncher -ErrorAction SilentlyContinue){throw 'Close game and launcher first'}
$root=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$target=[IO.Path]::GetFullPath((Join-Path $root 'r6/scripts/virtual-atelier-full/SetupNewTab.reds'))
if(!$target.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Target escapes game root'}
NoLinks $target
$oldHash='14B651576CC6D1FCEDBC11A48A96D1A2AC79DD84FCCFB90097F4169057378F80'
$newHash='5743CDCD6F8CD46A58F9642002F75EBCA25D84BE340856C2E6D85B15DAD973F8'
$h=Hash $target
if($null -eq $h){if(Test-Path -LiteralPath (Split-Path $target -Parent)){throw 'Atelier folder exists but supported script is missing'};@{status='ATELIER_NOT_PRESENT'}|ConvertTo-Json;exit}
if($h -cne $oldHash -and $h -cne $newHash){throw 'Unsupported or edited Atelier script; review required'}
if($Action -eq 'Verify'){if($h -cne $newHash){throw 'Required compatibility correction is not applied'};@{status='VERIFIED'}|ConvertTo-Json;exit}
if($h -ceq $newHash){@{status='ALREADY_PATCHED'}|ConvertTo-Json;exit}
$text=[IO.File]::ReadAllText($target);$nl="`r`n"
$old=@('  let root: ref<inkCompoundWidget> = this.GetWidget(n"page/linkPanel/panel") as inkCompoundWidget;','  if (!IsDefined(root)) {','    root = this.GetWidget(n"Page/linkPanel/panel") as inkCompoundWidget;') -join $nl
$new=@('  // Replace the complete native web page body; news widgets live outside linkPanel/panel.','  let root: ref<inkCompoundWidget> = this.GetWidget(n"page") as inkCompoundWidget;','  if !IsDefined(root) {','    root = this.GetWidget(n"Page") as inkCompoundWidget;','  };','  if !IsDefined(root) {','    root = this.GetRootCompoundWidget();') -join $nl
if(!$text.Contains($old)){throw 'Patch context mismatch'}
$bytes=[Text.UTF8Encoding]::new($false).GetBytes($text.Replace($old,$new))
$sha=[Security.Cryptography.SHA256]::Create();try{$got=([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','')}finally{$sha.Dispose()}
if($got -cne $newHash){throw 'Patch result hash mismatch'}
if($Action -eq 'Validate'){@{status='READY'}|ConvertTo-Json;exit}
$original=[IO.File]::ReadAllBytes($target)
if((Hash $target) -cne $oldHash){throw 'Original changed during preparation'}
try{[IO.File]::WriteAllBytes($target,$bytes);if((Hash $target) -cne $newHash){throw 'Patch readback failed'}}catch{[IO.File]::WriteAllBytes($target,$original);throw}
@{status='PATCHED_VERIFIED'}|ConvertTo-Json
