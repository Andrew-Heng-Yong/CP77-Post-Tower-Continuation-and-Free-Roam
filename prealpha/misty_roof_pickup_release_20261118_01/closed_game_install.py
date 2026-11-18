"""Use a fresh preservation snapshot after the player finished the rooftop test."""

import argparse

import delivery


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "install", "verify", "recover"))
    parser.add_argument("--plan-sha")
    args = parser.parse_args()

    previous = delivery.PLAN
    assert delivery.sha(previous) == "E30647A25C123669D95613F007A70A2426B22B61DEB9F39B846F7234B0D7973E"
    delivery.PLAN = delivery.ROOT / "closed_game_plan.json"
    if args.action == "prepare":
        delivery.prepare()
    old = delivery.read(previous)
    new = delivery.read(delivery.PLAN)
    assert new.keys() == old.keys()
    assert all(new[key] == old[key] for key in old.keys() - {"saved_files", "preferences"})
    assert [row["path"] for row in new["preferences"]] == [row["path"] for row in old["preferences"]]
    if args.action != "prepare":
        delivery.live(args.action, args.plan_sha)


if __name__ == "__main__":
    main()
