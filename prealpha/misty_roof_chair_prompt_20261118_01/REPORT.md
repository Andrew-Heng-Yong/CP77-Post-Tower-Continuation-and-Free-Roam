# Misty’s rooftop chair prompt

The user saw “Couch” on V’s rooftop chair and found the Sit marker behind it. Both the Sit and Get Up choices retained the couch label from the donor scene. Sit used the couch’s interaction orientation and a point 10 cm above the roof.

The installed correction uses the localized Chair label from The Tower’s own rooftop interaction, `LocKey#85596`, on both choices. The reference for V’s chair is cooked mesh instance 334 at sector placement 2036. A vertical intersection with its highest-detail mesh put the seat surface at 45 cm above the chair origin. The marker sits 6 cm above that surface at the center of the seat width. Its interaction uses the facing of the original Tower rooftop chair prompt in the private scene’s coordinate system. [Geometry and scene checks](prompt.py)

Only the two choice nodes changed in the serialized scene. The other 1,750 archive members matched. The installation verified the full 51-file Core, the previous archive backup, and all 523 save files. The marker’s screen position and interaction from the front await in-game confirmation. [Installed manifest](installed_manifest.json) · [Installation receipt](recovery/installed.json)
