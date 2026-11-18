# Download only the explicitly selected official release into this task workspace.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$out=Join-Path $PSScriptRoot 'work/download'
if(Test-Path -LiteralPath $out){throw 'Fresh download directory required'}
for($item=Get-Item -LiteralPath $PSScriptRoot -Force;$null -ne $item;$item=$item.Parent){if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked task directory'}}
[void][IO.Directory]::CreateDirectory($out)
$archive=Join-Path $out 'RedHotTools-1.3.0.zip'
$url='https://github.com/psiberx/cp2077-red-hot-tools/releases/download/v1.3.0-rc.7/RedHotTools-1.3.0.zip'
$expected='EE58F5BB33BF9B650A8D49670CF3BA279D6F8559C0BC3DB85417AF84CD4B7BB2'
Invoke-WebRequest -Uri $url -OutFile $archive -Headers @{'User-Agent'='PTFR-RedHotTools-Installer'}
if((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -cne $expected -or (Get-Item -LiteralPath $archive).Length -ne 2423642){throw 'Official asset checksum/size mismatch'}
@{status='OFFICIAL_RELEASE_DIGEST_VERIFIED';tag='v1.3.0-rc.7';release_id=446299298;asset_id=752317148;url=$url;sha256=$expected;bytes=2423642;published_utc='2026-11-15T19:14:28Z';asset_updated_utc='2026-11-15T20:53:59Z';metadata_source='https://api.github.com/repos/psiberx/cp2077-red-hot-tools/releases/tags/v1.3.0-rc.7';game_writes=0}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $out 'receipt.json') -Encoding utf8NoBOM
Write-Output 'Official RC7 ZIP downloaded and SHA256 verified.'
