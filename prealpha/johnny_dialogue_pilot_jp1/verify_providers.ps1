Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$plan=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'input_03/plan.json') -Raw | ConvertFrom-Json -Depth 100
$installed=Get-Content -LiteralPath $plan.installed_baseline -Raw | ConvertFrom-Json -Depth 30
$game=$installed.game_root
$targets=@{}
foreach($edit in $plan.edits){$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($edit.resource.depot).ToString();$targets[$key]=$edit}
$hashService=[WolvenKit.Common.Services.HashService]::new();$hashService.Load()
$reader=[WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
$rows=[Collections.Generic.List[object]]::new()
$count=0
foreach($path in Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc') -Recurse -File -Filter '*.archive'){
    if($path.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Archive provider link requires review'}
    $archive=$null
    if($reader.ReadArchive($path.FullName,$hashService,[ref]$archive).ToString() -cne 'NoError'){throw "Provider index cannot be read: $path"}
    $count++
    foreach($key in $targets.Keys){
        $number=[uint64]::Parse($key)
        if(-not $archive.Files.ContainsKey($number)){continue}
        $memory=[IO.MemoryStream]::new()
        try{[void]$archive.Files[$number].Extract($memory);$digest=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray()))}
        finally{$memory.Dispose()}
        $rows.Add(@{depot=$targets[$key].resource.depot;key=$key;archive=$path.FullName;sha256=$digest})
    }
}
foreach($key in $targets.Keys){
    $found=@($rows | Where-Object {$_.key -ceq $key})
    if($found.Count -ne 1 -or $found[0].archive -ine (Join-Path $game 'archive/pc/mod/zzzz_PTFR_Combined.archive') -or $found[0].sha256 -cne $targets[$key].resource.raw_sha256){throw 'Private scene provider ambiguity or source drift'}
}
$xl='archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
if((Get-FileHash -LiteralPath (Join-Path $game $xl)).Hash -cne (Get-FileHash -LiteralPath (Join-Path (Join-Path $plan.candidate_directory 'package') $xl)).Hash){throw 'Unexpected XL registration change'}
$proof=Join-Path $PSScriptRoot 'validation_05/provider_collisions.json'
if(Test-Path -LiteralPath $proof){throw 'Fresh provider proof required'}
@{status='PASS_EXACT_PRIVATE_PROVIDERS_NO_NEW_NAMESPACES';archives_checked=$count;providers=@($rows);
  new_depots=0;new_ArchiveXL_phase_ids=0;registration_delta='Exact existing XL bytes and private scene paths preserved';
  game_writes=0;save_writes=0} | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $proof -Encoding utf8NoBOM
Write-Output "Verified three unique private scene providers across $count archives; no new depot or ArchiveXL registration IDs"
