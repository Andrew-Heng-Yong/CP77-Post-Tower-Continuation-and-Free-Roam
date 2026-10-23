param([Parameter(Mandatory)][string]$Build)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$Build=[IO.Path]::GetFullPath($Build)
if(!$Build.StartsWith($ws+'\prealpha\camera_pa4\build\',[StringComparison]::OrdinalIgnoreCase)){throw 'PA4 scoped build required'}
if(Test-Path -LiteralPath (Join-Path $Build 'compile.json')){throw 'Existing verified compile report is pinned; use a new build'}
$cursor=$Build;while($cursor){if(Test-Path -LiteralPath $cursor){if(((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'Reparse build path refused'}};$parent=[IO.Directory]::GetParent($cursor);if($null -eq $parent){break};$cursor=$parent.FullName}
$stage=Join-Path $Build ('compile_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))
New-Item -ItemType Directory $stage|Out-Null
$scripts=Join-Path $stage 'scripts';$cache=Join-Path $stage 'cache'
New-Item -ItemType Directory $scripts,$cache|Out-Null
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function TextFile([string]$p,[string]$s){[IO.File]::WriteAllText($p,$s,[Text.UTF8Encoding]::new($false))}
$built=Get-Content -LiteralPath (Join-Path $Build 'build.json') -Raw|ConvertFrom-Json
if($built.status -cne 'BUILT_BASELINE_IDENTICAL_COMPILE_PENDING' -or $built.package_root -cne [IO.Path]::GetFullPath((Join-Path $Build 'package'))){throw 'Build/package identity mismatch'}
if(!$built.archive_unchanged -or $built.unchanged_files -ne 51 -or $built.prior_build_sha256 -cne 'AAC05EBBED94A72B8B7AAD03CE9EC8033483691E574EE80D681287B9899228AC'){throw 'PA4 immutable baseline check failed'}
function VerifyPackage {
 $actual=@(Get-ChildItem -LiteralPath $built.package_root -File -Recurse|ForEach-Object {[IO.Path]::GetRelativePath($built.package_root,$_.FullName).Replace('\','/')})
 $expected=@($built.package_files|ForEach-Object {$_.relative})
 if($actual.Count -eq 0 -or @($expected|Sort-Object -Unique).Count -ne $expected.Count -or @(Compare-Object ($actual|Sort-Object) ($expected|Sort-Object) -CaseSensitive).Count){throw 'Readback-verified package file set changed'}
 foreach($f in $built.package_files){$p=Join-Path $built.package_root $f.relative;if((Hash $p) -cne $f.sha256){throw "Readback-verified package bytes changed: $($f.relative)"}}
}
VerifyPackage
$buildHash=Hash (Join-Path $Build 'build.json')
$protected=@{}
foreach($f in Get-ChildItem -LiteralPath (Join-Path $game 'r6/cache') -File){$protected[$f.FullName]=Hash $f.FullName}
foreach($name in @('final.redscripts','final.redscripts.ts')){Copy-Item -LiteralPath (Join-Path $game ('r6/cache/'+$name)) -Destination (Join-Path $cache $name)}
foreach($f in Get-ChildItem -LiteralPath (Join-Path $game 'r6/scripts') -File -Recurse -Filter '*.reds'){
 $rel=[IO.Path]::GetRelativePath((Join-Path $game 'r6/scripts'),$f.FullName)
 if($rel -match '^PTFR_'){continue}
 $dest=Join-Path $scripts $rel;New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null
 Copy-Item -LiteralPath $f.FullName -Destination $dest;$protected[$f.FullName]=Hash $f.FullName
}
Copy-Item -LiteralPath (Join-Path $Build 'package/r6/scripts/PTFR_PreAlpha') -Destination (Join-Path $scripts 'PTFR_PreAlpha') -Recurse
$plugins=@(Get-Content (Join-Path $ws 'research/restriction_profiles/implementation_r1/compile_paths.txt')|Select-Object -Skip 2)
foreach($dir in $plugins){foreach($f in Get-ChildItem -LiteralPath $dir -Recurse -File -Filter '*.reds'){$protected[$f.FullName]=Hash $f.FullName}}
$paths=Join-Path $stage 'plugins.txt';TextFile $paths (($plugins -join "`n")+"`n")
$cli=Join-Path $ws 'research/finalboards_dismissal/tooling/redscript-cli.exe'
$base=Join-Path $cache 'final.redscripts'
$head=Join-Path $cache 'headless.redscripts'
$args=@('compile','-s',(Join-Path $scripts 'PTFR_PreAlpha'),'-s',(Join-Path $game 'red4ext/plugins/Codeware/Scripts'),'-b',$base,'-o',$head)
$log=(& $cli @args 2>&1|Out-String);TextFile (Join-Path $stage 'headless.log') $log
if($LASTEXITCODE -ne 0 -or $log -notmatch 'Output successfully saved' -or $log -match '\[ERROR'){Write-Output $log;throw 'Headless compile failed'}
$compiled=Join-Path $cache 'compiled.redscripts'
$args=@('-compile',$scripts,'-compilePathsFile',$paths,'-customCacheDir',$cache,'-outputCacheFile',$compiled,$base)
$log=(& (Join-Path $game 'engine/tools/scc.exe') @args 2>&1|Out-String);TextFile (Join-Path $stage 'engine.log') $log
if($LASTEXITCODE -ne 0 -or $log -notmatch 'Compilation complete' -or $log -notmatch 'Output successfully saved' -or $log -match '\[ERROR'){Write-Output $log;throw 'Full engine compile failed'}
if($log -notmatch 'EquipmentEx'){throw 'Expected third-party dependency absent'}
$flat=Join-Path $stage 'compiled.script'
$log=(& $cli decompile -i $compiled -o $flat 2>&1|Out-String);TextFile (Join-Path $stage 'decompile.log') $log
if($LASTEXITCODE -ne 0 -or $log -notmatch 'Output successfully saved'){throw 'Compiled readback failed'}
$text=[IO.File]::ReadAllText($flat)
foreach($symbol in @('class PTFR.ActivityStateR3.PreAlphaEntry','class PTFR.ActivityStateR3.PreAlphaArrivalPA1','func GameplayReady(','func CameraSample(','func FPPAtPlayer(','func CameraAligned(','func CameraStatus(','func ControlReady(','func PostEndingAuthorized(','func PTFRPAComplete(','func RestoreCertified(','class PTFR.RestrictionsR3.ProfilePhysical','EquipmentEx.OutfitSystem.GetInstance')){if(!$text.Contains($symbol)){throw "Missing compiled symbol: $symbol"}}
foreach($cameraEvidence in @('PTFRPA4_CameraRequest','PTFRPA4_CameraAligned','GetActiveCameraWorldTransform','GetFPPCameraComponent().Activate')){if(!$text.Contains($cameraEvidence)){throw "Missing compiled camera repair: $cameraEvidence"}}
foreach($old in @('class PTFR.ActivityStateR3.ActivityState','class PTFR.ActivityStateR3.NativeReuseU1','class PTFR.ActivityStateR3.GigFamilyB7','class PTFR.ActivityStateR3.FreshGigsB5')){if($text.Contains($old)){throw "Retired runtime still present $old"}}
foreach($p in $protected.Keys){if((Hash $p) -cne $protected[$p]){throw "Protected compile input changed $p"}}
VerifyPackage
if((Hash (Join-Path $Build 'build.json')) -cne $buildHash){throw 'Build report changed during compile'}
$result=@{status='PASS_COMPILE_AND_READBACK_NOT_LIVE';stage=$stage;build_sha256=$buildHash;compiled_sha256=(Hash $compiled);headless_sha256=(Hash $head);flat_sha256=(Hash $flat);protected=$protected;package_scripts=@(Get-ChildItem (Join-Path $Build 'package/r6/scripts') -Recurse -File|ForEach-Object {@{path=$_.FullName;sha256=(Hash $_.FullName)}})}
TextFile (Join-Path $Build 'compile.json') ($result|ConvertTo-Json -Depth 10)
Write-Output ('COMPILE_PASS='+$stage)
