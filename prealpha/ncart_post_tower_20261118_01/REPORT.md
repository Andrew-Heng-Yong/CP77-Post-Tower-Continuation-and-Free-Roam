# Ride Metro after The Tower

The staged Core restores NCART boarding for post-Tower V with an existing City Pass. It builds on the staged *Welcome to Paradise!* dialogue cut. An eligible existing free-roam save can use it without repeating the ending. [Candidate manifest](candidate_01/core_manifest.json)

## What happened to the service

The base game starts the metro under the additional game elements phase, through open world content node 156 and rideable service node 6. The station loader waits for V to enter one of 19 station areas. The station scene checks V’s pass and handles boarding. The train handler coordinates the route, the ride scene, arrival and cleanup, then returns control to the station loader for the next ride.

On ManualSave-31, the original station loader had 20 registered events, including its 19 station-area waits. On post-Tower ManualSave-32, the same graph paths remained in the saved catalogue, with no registered events anywhere on the inspected metro branch. Both saves still contained one City Pass in V’s inventory and recorded delivery of the original NCART message. The post-Tower slot also recorded that The Tower retired the main game. The user has yet to try boarding on that save. [Native registrations](work/owners.json) · [Pass inventory](work/pass.json) · [Quest facts](work/facts.json)

## How the restoration works

The new phase waits for genuine Tower completion, the mod’s return to free roam, V’s own City Pass, and an idle metro. It records a single issue before starting the station listener. The first-use pass animation stays under the native station scene. The private service omits the onboarding branch that sends the NCART message and grants the pass, and the old fast-travel terminal conversion that can remove points during the Watson lockdown.

The station selector, line selection, announcements, passengers, prefetch, ride and exit still use their native logic. The service requests the original metro prefab. Train preparation retains its own nested reference to that prefab. The district ambient-train controller has no new owner. The private train scene sends the two Johnny encounters to their original alternate selections and disables the Johnny actor. The graph preserves the other passenger encounters and the native English lip-sync mapping.

## Verification and playtest

The build verified four private resource paths against 135 installed archives and checked the new ArchiveXL phase ID against the native EP1 root and existing registrations. All 1,772 packed members passed byte readback. The verifier traced 22 phases and scenes, counted all 19 station areas, checked the retained nodes and edges against stock, and tested admission with missing prerequisites, a missing pass, an active ride, and an existing issue receipt. The staged package contains 51 Core files. [Verification](candidate_01/verification.json)

The first in-game check is to load ManualSave-32 after installation, approach the street entrance at Metro: Med Center, select **Ride Metro**, and exit at another station. Boarding again there tests whether the listener returns after the first trip. Save and reload on foot after disembarking to check persistence. Physical trigger placement, train movement, exit control, and playback in other voice languages remain unverified. For diagnosis, the read-only CET expression `print(Game.GetQuestsSystem():GetFactStr("PTFRNCART_Issued"))` reports whether the mod started the station listener.
