# Workspace-only official decoder download. Does not install into the game.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$out=Join-Path $PSScriptRoot 'work/tooling/wolvenkit_10_0_0_beta_1'
if(Test-Path -LiteralPath $out){throw 'Fresh tooling directory required'}
for($item=Get-Item -LiteralPath $PSScriptRoot -Force;$null -ne $item;$item=$item.Parent){if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked task directory'}}
[void][IO.Directory]::CreateDirectory($out)
$zip=Join-Path $out 'WolvenKit.Console-10.0.0-beta.1.zip'
$url='https://github.com/WolvenKit/WolvenKit/releases/download/10.0.0-beta.1/WolvenKit.Console-10.0.0-beta.1.zip'
$expected='292185C2F51D1CA85B95E1A7CA63A2D1BC8A3FC5EE387275E9A42EC78103155E'
Invoke-WebRequest -Uri $url -OutFile $zip -Headers @{'User-Agent'='PTFR-World-Overlap-Audit'}
if((Get-FileHash -LiteralPath $zip).Hash -cne $expected -or (Get-Item -LiteralPath $zip).Length -ne 44957672){throw 'Official release checksum/size mismatch'}
$archive=[IO.Compression.ZipFile]::OpenRead($zip)
try{
 foreach($entry in $archive.Entries){
  $name=$entry.FullName.Replace('\','/')
  if($name.StartsWith('/') -or $name.Contains(':') -or @($name.Split('/')|Where-Object {$_ -in @('.','..')}).Count){throw 'Unsafe ZIP member'}
  if(($entry.ExternalAttributes -shr 16 -band 0xF000) -eq 0xA000){throw 'ZIP symlink refused'}
 }
}finally{$archive.Dispose()}
$package=Join-Path $out 'package'
[IO.Compression.ZipFile]::ExtractToDirectory($zip,$package)
@{status='OFFICIAL_RELEASE_DIGEST_VERIFIED';tag='10.0.0-beta.1';url=$url;sha256=$expected;bytes=44957672;game_writes=0}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $out 'receipt.json') -Encoding utf8NoBOM
Write-Output 'Official WolvenKit 10 beta CLI downloaded and checksum verified in the audit workspace.'
