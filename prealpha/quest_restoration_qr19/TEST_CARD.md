# QR19 retained-message test

## Baseline observation

On November 6 the user reported the following read-only CET result after the request to check the November 4 AutoSave-8 fixture.

```text
Quest=1 Website=1 01=2 02=2 05=2 06=2 07=2
```

The quest and website objective were Inactive. The five original Bartmoss messages were Active. This confirms the intended journal stage in the observed session. The slot identity was requested and was not separately included in the reply. The exact on-disk AutoSave-8 independently contains the MQ018 reservation and lacks both original final-message registrations. Other objectives, exact runtime ownership, and whether the final text was already read were outside the user's observation. This is a qualified test lead, with full admission and delivery checked after deployment. [Offline evidence](evidence_01.json)

## First gameplay check after QR19 deployment

1. Launch normally and load the same post-Tower save. Keep the original save as the baseline.
2. Give free roam a few seconds to settle. Check whether the website objective has appeared. If it has, record that it appeared on load.
3. Otherwise, open the existing Bartmoss conversation and read the final text. Check whether Killing in the Name starts and points to the website.
4. Report whether the objective appeared before or after opening the thread, and whether any duplicate Bartmoss notifications appeared. Stop at the first clear result.

The expected result is one native website objective transition without resent messages. If the thread is missing, the existing facts or objectives changed, or a mod startup failure is visible, record the observed state separately. Nancy’s later call and the router objectives are a separate test.
