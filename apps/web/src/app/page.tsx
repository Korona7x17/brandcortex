import Link from "next/link";

/** Overview: what needs a human right now. */
export default function HomePage() {
  return (
    <section>
      <h1>BrandCortex</h1>
      <p>
        Cards come in from a brand, copy gets drafted in that brand&apos;s voice, a human approves, and
        the channel adapter publishes the photo with its link in the first comment.
      </p>
      <p>
        <Link href="/drafts">Review drafts &rarr;</Link>
      </p>
      {/* TODO(phase-1): counts by status, next scheduled slot, and any failed publishes. */}
    </section>
  );
}
