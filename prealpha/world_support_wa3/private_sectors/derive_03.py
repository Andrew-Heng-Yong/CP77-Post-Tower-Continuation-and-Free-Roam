from pathlib import Path
H=Path(__file__).resolve().parent
build=(H/'build_01.ps1').read_text(encoding='utf-8-sig').replace('_01','_03')
# Keep the audited native inputs at their existing paths.
for name in ['census','extracted','report','extract']:
    build=build.replace(name+'_03',name+'_01')
build=build.replace('# This independent custom block index is checked against the previous package in verification.\n$nativeBlock.RootChunk.Index.RldGridCell=[uint32]8425360','# Preserve the native block index; descriptor blockIndex and root index remain coherent.')
assert '8425360' not in build
verify=(H/'verify_01.ps1').read_text(encoding='utf-8-sig')
verify=verify.replace("'source_01'","'source_03'").replace("'verification_01.json'","'verification_03.json'").replace("'verify_01.ps1'","'verify_03.ps1'").replace("'build_01.ps1'","'build_03.ps1'")
start=verify.index("Check 'Private block has explicit unique namespace index'")
end=verify.index('$rows=@();',start)
verify=verify[:start]+"Check 'Private block preserves exact native root index' ((Json $block.RootChunk.Index) -ceq (Json $nativeBlock.RootChunk.Index))\n"+verify[end:]
verify=verify.replace("$d=$privateDescriptor[0];Check", "$d=$privateDescriptor[0];Check ($spec.id.ToString()+': descriptor preserves exact native block index') ((Json $d.BlockIndex) -ceq (Json $originalDescriptor[0].BlockIndex));Check")
for name,text in [('build_03.ps1',build),('verify_03.ps1',verify)]:
    assert not (H/name).exists()
    (H/name).write_text(text,encoding='utf-8',newline='\n')
