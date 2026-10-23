# Read-only validation helpers; no deployment/build on import.
. (Join-Path $PSScriptRoot 'gig_family_b7_1_xl.ps1')
function B72OldPath { 'towercontinued\family_b7\sts_wat_kab_06\boot.questphase' }
function B72NewPath { 'towercontinued\family_b7\sts_wat_kab_06\boot_b7_2.questphase' }
function B72Id([string]$Key) {
    # ArchiveXL v1.27.1 QuestPhaseExtension::GeneratePhaseNodeID.
    $crc=65535
    foreach($b in [Text.Encoding]::UTF8.GetBytes($Key)) {
        $x=($crc -shr 8) -bxor $b
        $x=$x -bxor ($x -shr 4)
        $crc=(($crc -shl 8) -bxor ($x -shl 12) -bxor ($x -shl 5) -bxor $x) -band 65535
    }
    return $crc
}
function B72IdIndependent([string]$Key) {
    # Independent bitwise CRC-CCITT-FALSE implementation for regression checks.
    $crc=65535
    foreach($b in [Text.Encoding]::UTF8.GetBytes($Key)) {
        $crc=$crc -bxor ([int]$b -shl 8)
        for($bit=0;$bit -lt 8;$bit++) {
            $crc=if($crc -band 32768){(($crc -shl 1) -bxor 0x1021) -band 65535}else{($crc -shl 1) -band 65535}
        }
    }
    return $crc
}
function B72ValidateXl([string]$Text,[string]$Workspace) {
    $m=B71Manifest $Workspace
    $indices=@(0..75 | Where-Object { $m.boots[$_] -ceq (B72OldPath) })
    if($indices.Count -ne 1){throw 'Shark binding missing from pinned manifest'}
    $m.boots[$indices[0]]=B72NewPath
    B71Validate $Text $m|Out-Null
}
function B72Inventory([string]$Game) {
    $result=[Collections.Generic.List[object]]::new()
    foreach($f in Get-ChildItem -LiteralPath (Join-Path $Game 'archive/pc/mod') -Filter '*.xl' -File) {
        $y=B71Parse (Get-Content -LiteralPath $f.FullName -Raw)
        $q=B71Child $y 'quest';if($null -eq $q){continue}
        $ph=B71Child $q 'phases';if($null -eq $ph){continue}
        foreach($e in $ph.Children) {
            $parent=B71Child $e 'parent'
            if($parent.Value -cne 'ep1\quest\ep1.quest'){continue}
            $inputNode=B71Child $e 'input'
            if($null -eq $inputNode){throw "Unaudited ep1 input: $($f.Name)"}
            $nodes=B71Child $inputNode 'node'
            if($nodes.Children.Count -ne 1 -or $nodes.Children[0].Value -cne '1'){throw "Unaudited ep1 graph connection: $($f.Name)"}
            $path=(B71Child $e 'path').Value
            $result.Add([ordered]@{path=$path;node=1;id=B72Id ($path+':1');source=$f.Name;source_sha256=R5Hash $f.FullName})
        }
    }
    return $result.ToArray()
}
function B72CollisionCheck($Inventory,[string]$Workspace,[string]$Candidate) {
    $rootPath=Join-Path $Workspace 'research/q307_extracted/json/ep1/quest/ep1.quest.json'
    R5Match $rootPath 'A8B4FB283FB1CDD4ABCD4618C078E25783687C92DE299FDF1E9EB8D7154CE468'
    $native=Get-Content -LiteralPath $rootPath -Raw|ConvertFrom-Json
    $ids=@($native.Data.RootChunk.graph.Data.nodes.Data.id)
    $newId=B72Id ($Candidate+':1')
    if($newId -in $ids){throw 'Candidate collides with native root node'}
    $oldOrNew=@($Inventory|Where-Object { $_.path -ceq (B72OldPath) -or $_.path -ceq (B72NewPath) })
    if($oldOrNew.Count -ne 1 -or $oldOrNew[0].source -cne 'TowerContinued_FamilyB7.archive.xl'){throw 'Expected exactly one original/repaired Shark registration'}
    foreach($e in $Inventory) {
        if((B72IdIndependent ($e.path+':1')) -ne $e.id){throw 'Independent ID calculation mismatch'}
        if($e.path -cne (B72OldPath) -and $e.path -cne (B72NewPath) -and $e.id -eq $newId){throw 'Candidate collides with installed root injection'}
    }
    if((B72IdIndependent ($Candidate+':1')) -ne $newId){throw 'Candidate ID mismatch'}
    return [ordered]@{old_id=B72Id ((B72OldPath)+':1');new_id=$newId;native_root_ids=$ids;installed_root_entries=@($Inventory).Count;collision_free=$true;independent_crc_match=$true}
}
