# Session Log – 2026-08-06_07
Tags: [Seed-on-boot][Railway][Logging][Verification-method]
Repo: brandcortex@bb44820 on **main** (pushed)
Context loaded: continuation of session 06 (same day)

## Notes

User supplied the Railway deployment log (`docs/log/logs.1786034205210.json`, deployment 265d2713).
Reading it produced two fixes and one lesson about how I verify things.

**What the log said.** The deploy landed, boot-seeding ran, and refused:

    file=34b942d201fc row=34b942d201fc expected=(none)

Identical hashes. The row already held exactly what the file said, and was refused on *provenance*
alone — it had been seeded by hand an hour earlier, before stamping existed. Refusing every unstamped
row means boot-seeding sits inert until someone runs the manual command it was built to replace: the
gap it exists to close, reintroduced as a policy.

**Fix 1 — the adopt rule.** An unstamped row is now adopted and stamped when applying the file would
change nothing. Nothing is overwritten, no conflict to arbitrate, and the stamp arms every deploy
after it. An unstamped row that *differs* is still refused: unknown provenance could be anyone's
tuning. A test then caught the first version of this too — I compared the row to the raw file, which
only works because the real seed happens to name every column. `store.save` overwrites only the
columns a document *names*, so for a partial seed file "equals the file" and "applying it changes
nothing" are different questions. Now computed via `_projected(current, document)`, which mirrors
`save`'s semantics without writing. `brand_config._COLUMNS` became public `COLUMNS` for it.

**Fix 2 — logging was invisible.** The next boot logged *nothing* about `brand_config`. uvicorn
configures its own loggers and leaves the root one at default, so every `INFO` from `brandcortex.*`
was dropped — the earlier refusal was only visible because `WARNING` clears the default bar. A
subsystem whose entire purpose is preventing silent no-ops was silent when it worked. Root level now
comes from `BRANDCORTEX_LOG_LEVEL` (`force=True`; uvicorn may have installed a handler first).
Confirmed in production:

    INFO [brandcortex.main] brand_config bootstrap: unchanged thaiswim

**The method lesson (the part worth keeping).** Twice I claimed a deployment state from a signal that
cannot distinguish old container from new:

* polled `/health` — the *old* container was already answering, so the loop returned instantly and I
  read the pre-boot row, then reported "the fix didn't trigger". It had;
* `until railway logs | grep "Application startup complete"` — matched that line in the *previous*
  deployment's log, returned immediately, same false conclusion.

The reliable check is trivial and I should have reached for it first: `railway ssh --service api
"grep -c '<symbol only the new code has>' <file>"`. Verify the artifact, not a side effect that both
versions produce. `railway ssh` also returns "application is not running or in an unexpected state"
mid-restart, which is itself a usable signal.

## Artifacts

- `db/bootstrap_config.py@34dac7` — `_projected`, the adopt branch, docstring case list
- `main.py@10632c` — `_configure_logging(settings.log_level)` in `create_app`
- `core/brand_config.py@b653b6` — `_COLUMNS` → public `COLUMNS`
- `apps/api/tests/unit/test_bootstrap_config.py` — adopt-identical, refuse-differing (9 tests)
- `.gitignore` — `docs/log/` (exported platform logs, not source)
- Commits: ffdfd9e adopt rule · bb44820 logging

C: Verify a deploy by an artifact only the new build contains, never by /health or a log line the old
   build also produced — both answered "yes" while the old container was still serving
C: Railway classifies all stderr as severity=error; Python logging defaults there, so `INFO:
   Application startup complete` appears red. Not a signal
C: An unstamped brand_config row is adopted only when applying the file is a no-op; a differing
   unstamped row still belongs to a human
D: D-2026-08-06-08 amended in place with the adopt rule (same decision, corrected policy)
Δ: PRODUCTION verified end to end: stamp present, `apply_seed -> unchanged`, honorific คุณ,
   max_emoji 2, and the bootstrap line now visible in the deploy log
Q: Railway git connection still has not produced a deploy on push — every API change needs
   `railway up`. Check root directory (`apps/api`) and watch paths in the dashboard
Q: Existing draft rows keep frozen `post_text`; old queue items still show old copy by design
→: Verify/repair the Railway git connection, then R2 → cron worker → insights fetcher
→: First production compose still pending the user
