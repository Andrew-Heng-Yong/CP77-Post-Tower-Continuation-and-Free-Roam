  private func FlagHS4(v: Int32) -> Bool { return v==0 || v==1; }
  private func JournalValuesHS4(state: Int32,counter: Int32,optional: Int32,tracked: Int32) -> Bool {
    return state>=-1 && state<=4 && counter>=-1 && optional>=-1 && optional<=1 && tracked>=-1 && tracked<=1;
  }
  private func OnFilePacketRequestHS4(r: ref<FilePacketRequestHS4>) -> Void {
    if !this.ImportCurrentHS4(r.epoch,r.lease,r.transaction) { return; }
    if r.start!=this.ImportCursorHS4(r.channel) { return; }
    if r.channel==1 { this.ReadLegacyPacketHS4(r);return; }
    if r.channel!=3 || r.start<0 || r.count<=0 || r.count>128 || r.start+r.count>SnapshotDataHS3.Count() {
      this.importFaultHS4=true;return;
    }
    let offset=0;let index=r.start;let end=r.start+r.count;let width: Int32;let journal: CaptureJournalHS3;let value: CaptureValueHS3;
    while index<end {
      width=index<SnapshotDataHS3.JournalCount()?5:2;
      if offset+width>ArraySize(r.data) || !this.FlagHS4(r.data[offset+width-1]) { this.importFaultHS4=true;return; }
      if width==5 {
        if !this.JournalValuesHS4(r.data[offset],r.data[offset+1],r.data[offset+2],r.data[offset+3]) { this.importFaultHS4=true;return; }
        journal.state=r.data[offset];journal.counter=r.data[offset+1];journal.optional=r.data[offset+2];journal.tracked=r.data[offset+3];journal.stable=r.data[offset+4]==1;
        ArrayPush(this.importedJournalsHS4,journal);
      } else {
        value.value=r.data[offset];value.stable=r.data[offset+1]==1;
        if index<SnapshotDataHS3.JournalCount()+SnapshotDataHS3.FactCount() { ArrayPush(this.importedFactsHS4,value); }
        else { if value.value< -1 { this.importFaultHS4=true;return; };ArrayPush(this.importedItemsHS4,value); }
      }
      offset+=width;index+=1;
    }
    if offset!=ArraySize(r.data) { this.importFaultHS4=true;return; }
    this.extendedCursorHS4=end;
  }
  private func ReadLegacyPacketHS4(r: ref<FilePacketRequestHS4>) -> Void {
    if r.start<0 || r.start>=SnapshotDataHS1.Count() || r.count!=1 { this.importFaultHS4=true;return; }
    let paths=SnapshotDataHS1.Paths(r.start);let names=SnapshotDataHS1.Facts(r.start);
    let n=ArraySize(paths);let f=ArraySize(names);
    if ArraySize(r.data)!=2+4*n+f || !this.FlagHS4(r.data[0]) || !this.FlagHS4(r.data[1]) { this.importFaultHS4=true;return; }
    let row: SnapshotRowHS1;row.stable=r.data[0]==1;row.legacyCertified=r.data[1]==1;
    let i=0;
    while i<n {
      if !this.JournalValuesHS4(r.data[2+i],r.data[2+n+i],r.data[2+2*n+i],r.data[2+3*n+i]) { this.importFaultHS4=true;return; }
      ArrayPush(row.states,r.data[2+i]);ArrayPush(row.counters,r.data[2+n+i]);
      ArrayPush(row.optional,r.data[2+2*n+i]);ArrayPush(row.tracked,r.data[2+3*n+i]);i+=1;
    }
    i=0;while i<f { ArrayPush(row.facts,r.data[2+4*n+i]);i+=1; }
    ArrayPush(this.importedLegacyHS4,row);this.legacyCursorHS4+=1;
  }
