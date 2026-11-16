#include "ReplyHandoff.hpp"

#include <cstdio>

int main()
{
    ptfr::ReplyHandoff original;
    constexpr ptfr::ReplyDuration saved{6,171141};
    unsigned passed=0;
    unsigned failed=0;
    const auto check=[&](bool accepted,const char* label){
        std::printf("%s %s\n",accepted?"PASS":"FAIL",label);
        accepted ? ++passed : ++failed;
    };
    check(!original.Commit(saved),"a missing observation cannot become a checkpoint");
    original.Observe({6,172801});
    check(original.Read(6)==0,"reject a duration longer than the original timer");
    original.Observe(saved);
    check(original.Read(6)==saved.seconds && original.Read(7)==0,"observe the exact ending ticket");
    original.Invalidate();
    check(!original.Commit(saved),"an original callback invalidates an uncommitted sample");
    original.Observe(saved);
    original.Observe({6,171140});
    check(!original.Commit(saved),"slew in the clock sample is detected at commit");
    original.Observe(saved);
    check(original.Commit(saved) && original.Held(),"commit one live checkpoint");
    original.Observe({7,5});
    original.Invalidate();
    check(original.Read(6)==saved.seconds && original.Read(7)==0,"the committed checkpoint stays fixed");
    check(!original.Prepare(saved,false),"an unretired owner prevents handoff");
    check(!original.Prepare({7,saved.seconds},true),"a different ending cannot read the held wait");
    check(original.Prepare(saved,true),"an exclusive replacement owner can take the saved duration");
    check(original.ScheduledDuration(6)==saved.seconds && original.ScheduledDuration(7)==0,
          "preparation exposes a duration only to its own ticket");
    original.MarkScheduled();
    check(original.ScheduledDuration(6)==0 && !original.Prepare(saved,true),"scheduling consumes the request once");
    ptfr::ReplyHandoff reloaded;
    check(!reloaded.Prepare({6,0},true) && !reloaded.Prepare({6,172801},true),"empty or invalid saved durations defer");
    check(reloaded.Prepare(saved,true) && reloaded.ScheduledDuration(6)==saved.seconds,
          "a save-local checkpoint can be prepared again after a hospital reload");
    reloaded.Abort();
    check(reloaded.ScheduledDuration(6)==0,"aborting revokes the pending schedule");
    std::printf("%u passed, %u failed\n",passed,failed);
    return failed ? 1 : 0;
}
