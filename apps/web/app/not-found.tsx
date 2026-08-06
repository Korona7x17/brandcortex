import Link from "next/link";

export default function NotFound() {
  return (
    <div className="empty">
      <p>No such post.</p>
      <p className="note">
        <Link href="/">Back to the queue</Link>
      </p>
    </div>
  );
}
