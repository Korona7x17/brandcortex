/**
 * Dashboard (spec §9).
 *
 * The slices Facebook's own insights cannot give: swimmer vs event, best time, which intro line, which
 * age groups travel.
 *
 * Show UTM sessions and the channel's link clicks side by side rather than picking one. They will not
 * agree — sessions are the truth, and the size of the gap is itself the anti-reward-hacking signal.
 */
export default function AnalyticsPage() {
  // TODO(phase-2): dimension picker + breakdown table + hour x weekday timing matrix.
  return (
    <section>
      <h1>Analytics</h1>
      <p>Not implemented yet (Phase 2).</p>
    </section>
  );
}
