param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$WolvenKitRoot='C:\Users\Ayong\Documents\WolvenKit-8.20.0',[string[]]$References=@(),[string]$OutputPath='')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot -HelpersOnly
$audit=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_ordinary_vendor_batch\owner_audit.json') -Raw | ConvertFrom-Json
$wanted=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
foreach($s in @($audit | Where-Object disposition -eq 'review')) {
    [void]$wanted.Add($s.scene_marker);[void]$wanted.Add($s.outer_distance.reference);[void]$wanted.Add($s.far.reference)
}
if($References.Count){$wanted.Clear();foreach($ref in $References){[void]$wanted.Add($ref)}}
$hashes=[WolvenKit.Common.Services.HashService]::new();$hashes.Load()
$handler=[WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e)
    return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])
}
$found=[Collections.Generic.List[object]]::new()
$archiveRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc'
foreach($relative in @('content\basegame_3_nightcity.archive','ep1\ep1_1_nightcity.archive')) {
    $archive=$null;$path=Join-Path $archiveRoot $relative
    if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hashes,[ref]$archive).ToString() -ne 'NoError'){throw 'Archive read failed'}
    $entries=@($archive.Files.Values | Where-Object {$_.Name -match '^base\\worlds\\03_night_city\\_compiled\\default\\always_loaded_[012]\.streamingsector$'})
    foreach($entry in $entries) {
        $stream=[IO.MemoryStream]::new()
        try {
            $entry.Extract($stream);$rawHash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($stream.ToArray()));$stream.Position=0
            $file=$null
            $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream);$reader.add_ParsingError($handler)
            if($reader.ReadFile([ref]$file,$true).ToString() -ne 'NoError'){throw 'Sector read failed'}
            foreach($d in $file.RootChunk.NodeData.Data) {
                $ref=$d.QuestPrefabRefHash.ToString()
                $suffix=($ref -split '/')[-1]
                if(-not $wanted.Contains($suffix) -and -not $wanted.Contains($ref)){continue}
                $key=if($wanted.Contains($suffix)){$suffix}else{$ref}
                $idx=[int]$d.NodeIndex.ToString()
                $found.Add([pscustomobject]@{reference=$key;full_reference=$ref;archive=$relative;sector=$entry.Name;sector_sha256=$rawHash;node_index=$idx;node_type=$file.RootChunk.Nodes[$idx].Chunk.GetType().Name;x=[double]$d.Position.X.ToString();y=[double]$d.Position.Y.ToString();z=[double]$d.Position.Z.ToString()})
            }
        } finally {$stream.Dispose()}
    }
}
$out=Join-Path $WorkspaceRoot 'research\b0_ordinary_vendor_batch\marker_evidence.json'
if($OutputPath){$out=$OutputPath}
[IO.File]::WriteAllText($out,($found.ToArray() | ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
$missing=@($wanted | Where-Object {$_ -notin $found.reference})
[pscustomobject]@{wanted=$wanted.Count;foundReferences=@($found.reference | Sort-Object -Unique).Count;records=$found.Count;missing=$missing} | ConvertTo-Json -Depth 4
