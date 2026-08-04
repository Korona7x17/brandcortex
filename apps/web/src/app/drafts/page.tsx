/**
 * The review queue — the human-in-the-loop gate (spec §7 step 4).
 *
 * Phase 1 is deliberately minimal: list drafts, edit, approve. The gate stays until the generation
 * engine has earned trust.
 *
 * The editor shows caption and first comment as separate fields because they are separate publishes:
 * the caption is the photo post, the first comment carries the link. Merging them in the UI would
 * invite someone to paste the link into the caption, which is exactly what costs reach.
 */
export default function DraftsPage() {
  // TODO(phase-1): fetch api.listPosts({ status: "draft" }), render the card image alongside the
  // editable caption and first comment, with approve / publish actions.
  return (
    <section>
      <h1>Drafts</h1>
      <p>Not implemented yet (Phase 1).</p>
    </section>
  );
}
