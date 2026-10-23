param([Parameter(Mandatory)][string]$Build)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$Build=[IO.Path]::GetFullPath($Build)
if(!$Build.StartsWith($ws+'\prealpha\postending_pa5\camera\build\',[StringComparison]::OrdinalIgnoreCase) -or (Test-Path (Join-Path $Build 'compile.json'))){throw 'Fresh scoped component compile required'}
function TextFile($p,$s){[IO.File]::WriteAllText($p,$s,[Text.UTF8Encoding]::new($false))}
function Hash($p){(Get-FileHash -LiteralPath $p).Hash}
$built=Get-Content -Raw (Join-Path $Build 'build.json')|ConvertFrom-Json
if($built.status -cne 'CAMERA_PA5_BUILT_NOT_LIVE'){throw 'Unexpected candidate manifest'}
foreach($f in $built.package_files){if((Hash (Join-Path $built.package_root $f.relative)) -cne $f.sha256){throw 'Package hash drift'}}
$stage=Join-Path $Build ('compile_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))
$scripts=Join-Path $stage 'scripts';$cache=Join-Path $stage 'cache'
New-Item -ItemType Directory -Force $scripts,$cache|Out-Null
$protected=@{}
foreach($f in Get-ChildItem -LiteralPath (Join-Path $game 'r6/cache') -File){$protected[$f.FullName]=Hash $f.FullName}
foreach($name in @('final.redscripts','final.redscripts.ts')){Copy-Item -LiteralPath (Join-Path $game ('r6/cache/'+$name)) -Destination (Join-Path $cache $name)}
foreach($f in Get-ChildItem -LiteralPath (Join-Path $game 'r6/scripts') -Recurse -File -Filter '*.reds'){
 $rel=[IO.Path]::GetRelativePath((Join-Path $game 'r6/scripts'),$f.FullName)
 $dest=Join-Path $scripts $rel;New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null
 Copy-Item -LiteralPath $f.FullName -Destination $dest;$protected[$f.FullName]=Hash $f.FullName
}
$component='r6/scripts/PTFR_PreAlpha/PA5/CameraOpticsPA5.reds'
$dest=Join-Path $scripts 'PTFR_PreAlpha/PA5/CameraOpticsPA5.reds';New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null
if(Test-Path -LiteralPath $dest){throw 'Unexpected already-installed camera PA5 source'}
Copy-Item -LiteralPath (Join-Path $built.package_root $component) -Destination $dest
$plugins=@(Get-Content (Join-Path $ws 'research/restriction_profiles/implementation_r1/compile_paths.txt')|Select-Object -Skip 2)
foreach($dir in $plugins){foreach($f in Get-ChildItem -LiteralPath $dir -Recurse -File -Filter '*.reds'){$protected[$f.FullName]=Hash $f.FullName}}
$paths=Join-Path $stage 'plugins.txt';TextFile $paths (($plugins -join "`n")+"`n")
$cli=Join-Path $ws 'research/finalboards_dismissal/tooling/redscript-cli.exe';$base=Join-Path $cache 'final.redscripts'
$head=Join-Path $cache 'headless.redscripts'
$log=(& $cli compile -s (Join-Path $scripts 'PTFR_PreAlpha') -s (Join-Path $game 'red4ext/plugins/Codeware/Scripts') -b $base -o $head 2>&1|Out-String)
TextFile (Join-Path $stage 'headless.log') $log
if($LASTEXITCODE -ne 0 -or $log -notmatch 'Output successfully saved' -or $log -match '\[ERROR'){Write-Output $log;throw 'Headless compile failed'}
$compiled=Join-Path $cache 'compiled.redscripts'
$log=(& (Join-Path $game 'engine/tools/scc.exe') -compile $scripts -compilePathsFile $paths -customCacheDir $cache -outputCacheFile $compiled $base 2>&1|Out-String)
TextFile (Join-Path $stage 'engine.log') $log
if($LASTEXITCODE -ne 0 -or $log -notmatch 'Compilation complete' -or $log -notmatch 'Output successfully saved' -or $log -match '\[ERROR'){Write-Output $log;throw 'Full engine compile failed'}
if($log -notmatch 'EquipmentEx'){throw 'Expected third-party compile dependency absent'}
$flat=Join-Path $stage 'compiled.script'
$log=(& $cli decompile -i $compiled -o $flat 2>&1|Out-String);TextFile (Join-Path $stage 'decompile.log') $log
if($LASTEXITCODE -ne 0 -or $log -notmatch 'Output successfully saved'){throw 'Readback failed'}
$text=[IO.File]::ReadAllText($flat)
foreach($token in @('class PTFR.ActivityStateR3.CameraOpticsPA5','func SampleValid(','func Optics(','PTFRPA5O_NativeOut','PTFRPA5O_Permit','fovOverrideWeight','zoomWeaponOverrideWeight','GetActiveCameraFOV','GetFOV()','GetZoom()','PTFR.ActivityStateR3.CameraOpticsPA5.Get(gameInstance)')){if(!$text.Contains($token)){throw "Compiled camera evidence missing $token"}}
foreach($p in $protected.Keys){if((Hash $p) -cne $protected[$p]){throw 'Protected runtime compile input changed'}}
foreach($f in $built.package_files){if((Hash (Join-Path $built.package_root $f.relative)) -cne $f.sha256){throw 'Package changed during compile'}}
TextFile (Join-Path $Build 'compile.json') (@{status='PASS_COMPONENT_FULL_COMPILE_AND_READBACK_NOT_LIVE';stage=$stage;compiled_sha256=Hash $compiled;headless_sha256=Hash $head;flat_sha256=Hash $flat;protected_entries=$protected.Count;build_sha256=Hash (Join-Path $Build 'build.json');limitations='Compile against currently installed PA4 plus this component. Root must compile final combined PA5 package separately.'}|ConvertTo-Json -Depth 12)
Write-Output ('CAMERA_COMPILE_PASS='+$stage)
