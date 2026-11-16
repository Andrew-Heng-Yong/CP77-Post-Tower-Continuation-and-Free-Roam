"""Compile the Claire handoff against RD10's exact registered source inventory."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "universal_resume_handoff_20261114_01"))
import compile_cutoff as compiler


def overlay(source):
    newline = "\r\n" if b"\r\n" in source else "\n"
    original = source.decode("utf-8").replace("\r\n", "\n")
    anchor = "public class CaptureArchiveHS3 extends ScriptableSystem {\n"
    methods = (HERE / "claire_members.reds").read_text(encoding="utf-8")
    declaration = (
        "public static native func ReadClaireReplyWait(quests: ref<QuestsSystem>,ticket: Int32) -> Int32\n"
        "public static native func CommitClaireReplyWait(quests: ref<QuestsSystem>,ticket: Int32,seconds: Int32) -> Bool\n"
        "public static native func PrepareClaireReplyOwner(quests: ref<QuestsSystem>,ticket: Int32,seconds: Int32) -> Bool\n"
    )
    commit = '    this.detail="Save-local history committed before native cleanup; recovery export pending.";'
    poll = '    this.observedTicket=ticket;\n    let legacy=SnapshotStateHS1.Get(this.GetGameInstance());'
    closed = '      this.ResetCapture();this.PrepareJSON();return;\n    }\n' + poll
    replace = compiler.replace_once
    altered = replace(original, anchor, declaration + anchor + methods)
    altered = replace(altered, commit, "    this.CaptureClaireReply(ticket,route,jm);\n" + commit)
    altered = replace(altered, closed, "      this.PollClaireReply(jm);\n" + closed)
    assert altered.replace(declaration + anchor + methods, anchor, 1).replace(
        "    this.CaptureClaireReply(ticket,route,jm);\n" + commit, commit, 1
    ).replace("      this.PollClaireReply(jm);\n" + closed, closed, 1) == original
    return altered.replace("\n", newline).encode("utf-8")


if __name__ == "__main__":
    compiler.HERE = HERE
    compiler.overlay = overlay
    compiler.main()
