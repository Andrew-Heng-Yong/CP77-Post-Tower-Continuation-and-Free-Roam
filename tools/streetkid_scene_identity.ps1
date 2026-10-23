# Dot-source after build_phase2a.ps1 -HelpersOnly. This function returns a new
# CR2W file; callers must use the result and refresh any cached RootChunk refs.
# JSON traversal is typed: unrelated numeric node IDs/times remain untouched.
function Repair-StreetkidSceneIdentity {
    param([Parameter(Mandatory=$true)]$File)

    $dto = [WolvenKit.Common.Conversion.RedFileDto]::new($File, $false)
    $options = [WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
    $text = [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($dto, $options)
    $document = ConvertFrom-Json -InputObject $text -AsHashtable -Depth 100
    $root = $document['Data']['RootChunk']
    if ($root['$type'] -ne 'scnSceneResource') { throw 'Expected a scene resource' }
    $actors = @($root['actors'])
    $players = @($root['playerActors'])
    if ($actors.Count -ne 2 -or $players.Count -ne 1 -or
        $actors[0]['actorId']['id'] -ne 0 -or $actors[1]['actorId']['id'] -ne 1 -or
        $players[0]['actorId']['id'] -notin 2,3) {
        throw 'Expected the bounded Streetkid V-only cast: actors 0,1 and player 2 or 3'
    }

    $changes = [Collections.Generic.List[object]]::new()
    function Repair-IdentityValue($value, [string]$path) {
        if ($value -is [Collections.IDictionary]) {
            # Original V female idle animation asset has this historical name.
            # Permit only this inert resource path, never actor/story metadata.
            if ($value['$type'] -eq 'ResourcePath' -and $value['$value'] -eq 'base\animations\player\female\body\player_locomotion_johnny_guitar.anims') { return }
            if ($value.Contains('$type') -and $value.Contains('id') -and
                $value['$type'] -in 'scnActorId','scnPerformerId') {
                $from = [uint32]$value['id']
                $to = $null
                if ($value['$type'] -eq 'scnActorId' -and $from -eq 3) { $to = [uint32]2 }
                if ($value['$type'] -eq 'scnPerformerId' -and $from -eq 769) { $to = [uint32]513 }
                if ($null -ne $to) {
                    $value['id'] = $to
                    $changes.Add([PSCustomObject]@{path=$path;type=$value['$type'];from=$from;to=$to})
                }
            }
            foreach ($key in @($value.Keys)) { Repair-IdentityValue $value[$key] ($path+'.'+$key) }
        } elseif ($value -is [Collections.IEnumerable] -and $value -isnot [string]) {
            $index=0
            foreach ($item in $value) { Repair-IdentityValue $item ($path+'['+$index+']'); $index++ }
        } elseif ($value -is [string] -and $value -match '(?i)johnny') {
            throw "Unexpected Johnny metadata at $path"
        }
    }
    Repair-IdentityValue $root '$.Data.RootChunk'
    $json = ConvertTo-Json -InputObject $document -Depth 100 -Compress
    $repairedDto = [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize(
        [WolvenKit.Common.Conversion.RedFileDto], $json, $options)
    $repaired = $repairedDto.Data
    $ids = @($repaired.RootChunk.Actors | ForEach-Object {[uint32]$_.ActorId.Id.ToString()}) +
           @($repaired.RootChunk.PlayerActors | ForEach-Object {[uint32]$_.ActorId.Id.ToString()})
    if (($ids -join ',') -ne '0,1,2') { throw 'Dense Streetkid actor identity repair failed' }
    return [PSCustomObject]@{File=$repaired;Changes=@($changes.ToArray())}
}
