param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$package=Get-Content (Join-Path $audit 'original_lamp_s1_package_manifest.json') -Raw|ConvertFrom-Json
$alias=Get-Content (Join-Path $audit 'original_lamp_alias_s1_manifest.json') -Raw|ConvertFrom-Json
$controller=Get-Content (Join-Path $audit 'original_lamp_s1_controller_manifest.json') -Raw|ConvertFrom-Json
if($package.status -ne 'BUILT_SINGLETON_ORIGINAL_LAMP_NOT_INSTALLED_OR_LIVE'){throw 'Package status changed'}
foreach($pair in @(@($package.archive,$package.sha256),@($package.xl,$package.xl_sha256),@($package.probe,$package.probe_sha256),@($alias.target,$alias.target_sha256))){
 if((Get-FileHash -LiteralPath $pair[0]).Hash -ne $pair[1]){throw ('Build input changed: '+$pair[0])}
}
$phase=Join-Path $WorkspaceRoot ('build\MistyOriginalLampAliasS1\source\'+$controller.phase_depot)
if((Get-FileHash -LiteralPath $phase).Hash -ne $controller.phase_sha256){throw 'Native controller source changed'}
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load();$archive=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($package.archive,$hash,[ref]$archive).ToString() -ne 'NoError'){throw 'Package cannot reopen'}
$expected=@{($alias.source_depot)=$alias.target_sha256;($controller.phase_depot)=$controller.phase_sha256}
if(@(Compare-Object @($expected.Keys|Sort-Object) @($archive.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Packed resource set changed'}
foreach($entry in $archive.Files.Values){
 $stream=[IO.MemoryStream]::new()
 try{$entry.Extract($stream);$actual=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($stream.ToArray()))}
 finally{$stream.Dispose()}
 if($actual -ne $expected[$entry.Name]){throw ('Packed resource bytes differ: '+$entry.Name)}
}
$xlText=[IO.File]::ReadAllText($package.xl)
if($xlText -notmatch [regex]::Escape($controller.phase_depot) -or $xlText -notmatch 'parent: ep1\\quest\\ep1.quest'){throw 'XL registration changed'}
if($package.original_placement_alias_writes -ne 1 -or $package.original_light_properties_changed -ne 0 -or $package.original_variant_writes -ne 0 -or $package.story_fact_writes -ne 0){throw 'Package scope changed'}
@{status='PASS_SINGLETON_PACKAGE_OFFLINE_NOT_LIVE';packed_resources=$expected.Count;packed_bytes_match=$true;alias_only=$true;native_nodes=$package.native_nodes;archive_sha256=$package.sha256}|ConvertTo-Json
