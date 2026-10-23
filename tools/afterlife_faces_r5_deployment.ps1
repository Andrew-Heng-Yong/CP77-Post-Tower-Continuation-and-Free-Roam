# Shared exact-scope deployment helpers. Dot-source; no deployment at load time.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
function R5Hash([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash }
function R5Match([string]$Path,[string]$Hash) { if((R5Hash $Path) -ne $Hash){throw "Hash mismatch: $Path"} }
function R5Within([string]$Path,[string]$Root) {
 $value=[IO.Path]::GetFullPath($Path)
 if(-not $value.StartsWith($Root.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)){throw "Path escaped root: $value"}
 return $value
}
function R5Closed {
 if(@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Close Cyberpunk 2077 before deployment'}
}
function R5Scope { @('r6/scripts/PTFR_Afterlife_Faces_R5/AfterlifeFacesR5.reds','r6/scripts/PTFR_Afterlife_Faces_R5/FaceCatalogR5.reds') }
function R5Snapshot([string]$Game,[string[]]$Exclude=@()) {
 $result=[ordered]@{}
 $files=@()
 $archive=Join-Path $Game 'archive\pc\mod'
 if(Test-Path -LiteralPath $archive){$files+=@(Get-ChildItem -LiteralPath $archive -File -Filter 'TowerContinued*')}
 foreach($relative in @('r6\scripts','bin\x64\plugins\cyber_engine_tweaks\mods')){
  $root=Join-Path $Game $relative
  if(Test-Path -LiteralPath $root){foreach($dir in Get-ChildItem -LiteralPath $root -Directory -Filter 'PTFR_*'){$files+=@(Get-ChildItem -LiteralPath $dir.FullName -File -Recurse)}}
 }
 $tweaks=Join-Path $Game 'r6\tweaks'
 if(Test-Path -LiteralPath $tweaks){$files+=@(Get-ChildItem -LiteralPath $tweaks -File -Recurse)}
 foreach($file in $files){if($file.FullName -notin $Exclude){$result[$file.FullName]=R5Hash $file.FullName}}
 return $result
}
function R5Unchanged($Snapshot) { foreach($path in $Snapshot.Keys){R5Match $path $Snapshot[$path]} }
function R5Json([string]$Path,$Value) { [IO.File]::WriteAllText($Path,($Value|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false)) }
