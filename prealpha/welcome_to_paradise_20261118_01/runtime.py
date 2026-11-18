"""Extend the installed S30 entry registry with the unstarted 2.5 tour."""
import json
import re
import sys
from prepare import BASE, ROOT, S29, TAG, WORK, read, sha
from pathlib import Path


def once(text, before, after):
    assert text.count(before) == 1, before
    return text.replace(before, after, 1)


def main():
    baseline = read(BASE)
    installed = Path(baseline["game_root"]) / S29
    assert sha(installed) == next(r["sha256"] for r in baseline["core_files"] if r["path"] == S29)
    contract = read(WORK / "contract_02.json")
    original = installed.read_bytes()
    code = original.decode("utf-8").replace("\r\n", "\n")
    prefix, klass = code.split("public abstract class SideJobDataS30 {")
    klass = once(klass, "func Count() -> Int32 { return 3;", "func Count() -> Int32 { return 4;")
    fields = {"ID": "mq061", "Title": "Welcome to Paradise!", "Tag": TAG}
    for name, value in fields.items():
        marker = klass.index("    return \"\";", klass.index("func " + name + "("))
        klass = klass[:marker] + f'    if i == 3 {{ return "{value}"; }}\n' + klass[marker:]
    marker = klass.index("    return -1;", klass.index("func Index("))
    klass = klass[:marker] + f'    if Equals(id, "mq061") || Equals(id, "{TAG}") {{ return 3; }}\n' + klass[marker:]
    journals = contract["journals"]
    arrays = {"Paths": list(journals), "Classes": list(journals.values()), "StatesA": [1]*len(journals),
              "StatesB": [1]*len(journals), "FactNames": contract["facts"], "FactMin": [0]*len(contract["facts"]),
              "FactMax": [0]*len(contract["facts"])}
    for method, values in arrays.items():
        branch = f"    if i == 2 {{ return SideJobDataS30.{method}2(); }}"
        klass = once(klass, branch, branch + "\n" + branch.replace("== 2", "== 3").replace("2();", "3();"))
        old = re.search(rf"  public static func {method}2\(\) -> array<(\w+)> [^\n]+", klass)
        assert old
        new = f"  public static func {method}3() -> array<{old[1]}> {{ return {json.dumps(values)}; }}"
        klass = once(klass, old[0], old[0] + "\n" + new)
    anchor = "    if ArraySize(items) > 0 {"
    head, runtime = prefix.split("public class SideJobsS30 extends ScriptableSystem {")
    runtime = once(runtime, anchor, """    if i == 3 {
      if !IsDefined(players) || !IsDefined(transaction) {
        sample.valid = false; sample.reason = "Tour inventory unavailable."; return sample;
      }
      let player = players.GetLocalPlayerMainGameObject() as PlayerPuppet;
      if !IsDefined(player) || player.IsReplacer() {
        sample.valid = false; sample.reason = "Waiting for V's inventory."; return sample;
      }
      let rewards: array<TweakDBID> = [""" + ", ".join(f"TDBID.FromNumber({n}ul)" for n in contract["items"]) + """];
      for reward in rewards {
        actual = transaction.GetItemQuantity(player, ItemID.CreateQuery(reward));
        ArrayPush(sample.inventory, actual);
        if actual != 0 { sample.valid = false; sample.reason = "An existing tour item is protected."; }
      }
    }
""" + anchor)
    header = "  private func FreshOwner(i: Int32) -> Bool {"
    runtime = once(runtime, header, header + """
    if i == 3 {
      if this.Own(i, "Ready") != 1 || this.Own(i, "Issued") != 0 { return false; }
      let history = CaptureArchiveHS3.Get(this.GetGameInstance());
      let content = GameInstance.GetQuestsContentSystem(this.GetGameInstance());
      if !IsDefined(history) || !IsDefined(content) || content.IsTokensActivationBlockedBySource(n"mq061_BlockToken_Temp") ||
        NotEquals(SnapshotDataHS3.FactName(10489), "mq061_start") || history.FactValue(10489) != 0 ||
        NotEquals(SnapshotDataHS3.FactName(10488), "mq061_07_rancho_done") || history.FactValue(10488) != 0 {
        return false;
      }
    }""")
    result = head + "public class SideJobsS30 extends ScriptableSystem {" + runtime + "public abstract class SideJobDataS30 {" + klass
    out = WORK / "runtime" / Path(S29).name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((result.replace("\n", "\r\n") if b"\r\n" in original else result).encode())
    sys.path.insert(0, str(ROOT.parent / "misty_rooftop_seat_20261117_01"))
    import build
    build.REDS = S29
    proof = build.compile_overlay(out, WORK / (sys.argv[1] if len(sys.argv) > 1 else "compile_01"))
    print("Compiled against", proof["registered_sources"], "registered sources")


if __name__ == "__main__":
    main()
