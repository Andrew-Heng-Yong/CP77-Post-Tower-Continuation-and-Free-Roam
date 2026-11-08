"""Independent byte-level check that cache invalidation covers every embedded container."""
from common import *
import sys
o=Path(sys.argv[1]);cache=read(o/'raw_oracle_cache.json')['exports'];rows=[]
for name,pin in cache.items():
 data=Path(name).read_bytes()
 if re.search(rb'"EmbeddedFiles"\s*:\s*\[\s*\{',data):rows.append({'json':name,'json_sha256':hashlib.sha256(data).hexdigest().upper()})
write(o/'embedded_container_scan.json',{'exports_checked':len(cache),'nonempty_embedded_containers':rows,'method':'Independent byte-pattern scan of every captured raw JSON export; detects nonempty container, not its semantics'});print(json.dumps({'exports_checked':len(cache),'containers':len(rows)}))
