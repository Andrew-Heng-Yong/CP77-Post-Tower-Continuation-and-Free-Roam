# Manual cleanup — Open Beta 0.2.0

Use this guide when upgrading an older Post Tower Continuation and Free Roam
installation. No old ZIP or backup is required. Verified obsolete files are
deleted directly.

## Remove the old files

1. Close Cyberpunk 2077 and its launcher. Open the actual game folder, the one
   containing `archive`, `bin` and `r6`.
2. Open `OBSOLETE_FILES.json` from this `readme` folder. Each `path` is relative
   to your game folder. `accepted_sha256` lists the known hashes for that old
   file. The list covers 124 obsolete paths from recorded earlier builds.
   Your installation may contain fewer of them.
3. Open `FILES.json` too. Its 51 current Tower paths must stay available for
   replacement by the beta. Do not delete these paths as obsolete files.
4. For each obsolete path that exists in your game folder, check its SHA-256.
   You can use PowerShell for one file at a time:

   ```powershell
   Get-FileHash -LiteralPath 'C:\your game folder\path from OBSOLETE_FILES.json' -Algorithm SHA256
   ```

5. If the hash matches an accepted hash for that exact path, delete that file
   in File Explorer. If it is missing, skip it. If its hash differs, leave it
   alone and ask for help identifying it. Do not identify files by name prefix
   alone, and do not delete whole directories.
6. Preserve saved games, frameworks, other mods, settings, caches, quest-history
   JSON and CET user data. Create no backup copies or old-release archives.
7. Merge the beta's `archive`, `bin` and `r6` folders into the game folder and
   choose **Replace the files in the destination**. Preserve their structure;
   do not replace the game's entire folders. The `readme` folder is reference
   material and does not need to be copied into the game.

For AI assistance instead, tell the AI to read
`readme/AI_CLEANUP_INSTRUCTIONS.md` and the two JSON manifests in this folder.

## Required Atelier compatibility correction

When Virtual Atelier is installed, its page-display correction is required.
This package contains no patch or cleanup scripts. Apply the edit below
manually, or ask your AI assistant to apply it after reading this section.

Target: `r6/scripts/virtual-atelier-full/SetupNewTab.reds` in the game folder.
The reviewed Virtual Atelier 1.6.4 original has SHA-256:

`14B651576CC6D1FCEDBC11A48A96D1A2AC79DD84FCCFB90097F4169057378F80`

The corrected file has SHA-256:

`5743CDCD6F8CD46A58F9642002F75EBCA25D84BE340856C2E6D85B15DAD973F8`

If the corrected hash already matches, keep it. If the original hash matches,
replace only the following lines inside `PopulateAtelierView`:

```reds
  let root: ref<inkCompoundWidget> = this.GetWidget(n"page/linkPanel/panel") as inkCompoundWidget;
  if (!IsDefined(root)) {
    root = this.GetWidget(n"Page/linkPanel/panel") as inkCompoundWidget;
```

with:

```reds
  // Replace the complete native web page body; news widgets live outside linkPanel/panel.
  let root: ref<inkCompoundWidget> = this.GetWidget(n"page") as inkCompoundWidget;
  if !IsDefined(root) {
    root = this.GetWidget(n"Page") as inkCompoundWidget;
  };
  if !IsDefined(root) {
    root = this.GetRootCompoundWidget();
```

Keep the following `};`, `RemoveAllChildren` and `SpawnFromExternal` lines.
Preserve CRLF line endings and UTF-8 without BOM, then verify the corrected
hash. Leave an unknown or edited version unchanged for review; do not silently
skip the required correction. Virtual Atelier itself is a separate mod.

## Future updates

Installed filenames stay the same. Merge a future full update's `archive`,
`bin` and `r6` folders into your game folder and click Replace. The initial
obsolete-file cleanup normally only needs doing once. If Virtual Atelier
itself is updated, check its required correction again.
