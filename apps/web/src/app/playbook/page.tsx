/**
 * Playbook view and approval gate (spec §10.3).
 *
 * A system that rewrites its own instructions has to keep them legible: what is active, what the
 * reflection agent proposed and on what evidence, and one click to approve or roll back.
 *
 * Every rule shows its sample size and confidence next to it — a rule drawn from four posts should
 * look as thin on screen as it is.
 */
export default function PlaybookPage() {
  // TODO(phase-2): active rules, proposals with evidence, "what I learned" reports, rollback.
  return (
    <section>
      <h1>Playbook</h1>
      <p>Not implemented yet (Phase 2).</p>
    </section>
  );
}
