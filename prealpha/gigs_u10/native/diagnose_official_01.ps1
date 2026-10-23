Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly
$out=Join-Path $ws 'research/gigs_u10/native/official_variants_01';if(Test-Path -LiteralPath $out){throw 'Use successor diagnostic'};New-Item -ItemType Directory $out|Out-Null
$pins=@{};foreach($rel in @('prealpha/gigs_u10/native/build/native_05/component.json','prealpha/gigs_u10/presentation/build/presentation_03/component.json')){ $doc=Get-Content (Join-Path $ws $rel) -Raw|ConvertFrom-Json;foreach($p in $doc.source_pins.PSObject.Properties){if($p.Name -match '^research/.+/raw/((base|ep1)/.+)$'){$depot=$Matches[1].Replace('/','\');if($depot -ceq 'base\journal\cooked_journal.journal'){continue};if($pins.ContainsKey($depot) -and $pins[$depot].expected -cne $p.Value){throw 'Conflicting source pins'};$pins[$depot]=@{expected=$p.Value;source=$p.Name}}}}
$keys=@{};foreach($dep in $pins.Keys){$keys[$dep]=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($dep)}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077';$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$rows=@();$archives=@()
$files=@(Get-ChildItem (Join-Path $game 'archive/pc/content') -File -Filter '*.archive')+@(Get-ChildItem (Join-Path $game 'archive/pc/ep1') -File -Filter '*.archive')
foreach($file in $files){
 $archive=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$archive).ToString() -ne 'NoError'){throw 'Bad official archive'}
 foreach($dep in $pins.Keys){$key=$keys[$dep];if(!$archive.Files.ContainsKey($key)){continue};$entry=$archive.Files[$key];$mem=[IO.MemoryStream]::new();try{$entry.Extract($mem);$bytes=$mem.ToArray()}finally{$mem.Dispose()};$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
  $raw=$null;$json=$null
  if($hash -cne $pins[$dep].expected -or $dep -ceq 'base\open_world\street_stories\santo_domingo\arroyo\sts_std_arroyo.questphase'){
   $folder=Join-Path $out $file.BaseName;$raw=Join-Path $folder ('raw/'+$dep);$json=Join-Path $folder ('json/'+$dep+'.json');New-Item -ItemType Directory -Force (Split-Path $raw),(Split-Path $json)|Out-Null
   [IO.File]::WriteAllBytes($raw,$bytes);Export-Cr2wJson (Read-Cr2wFile $raw) $json
  }
  $rows+=,@{depot=$dep;archive=$file.FullName;expected=$pins[$dep].expected;source=$pins[$dep].source;actual=$hash;equal=($hash -ceq $pins[$dep].expected);raw=$raw;json=$json}
 }
 $archives+=,@{path=$file.FullName;length=$file.Length;last_write_utc=$file.LastWriteTimeUtc.ToString('o')}
}
$report=@{status='OFFICIAL_BYTE_VARIANT_DIAGNOSTIC_NOT_EQUIVALENCE';rows=$rows;archives=$archives;selected=$pins.Count;found=@($rows.depot|Sort-Object -Unique).Count;mismatches=@($rows|Where-Object {!$_.equal}).Count;script_sha256=(Get-FileHash $PSCommandPath).Hash}
[IO.File]::WriteAllText((Join-Path $out 'report.json'),($report|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
$rows|Where-Object {!$_.equal}|Select-Object depot,archive,expected,actual|ConvertTo-Json -Depth 4
