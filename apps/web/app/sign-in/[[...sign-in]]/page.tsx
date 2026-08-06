import { SignIn } from "@clerk/nextjs";

/** Just the lockup and the box. No header, no tenant — nothing that needs a session to render. */
export default function SignInPage() {
  return (
    <main className="auth">
      <div className="mark" aria-hidden>
        <span className="mark-dot" />
        <span>
          Brand<span style={{ color: "var(--mute-2)" }}>Cortex</span>
        </span>
      </div>
      <SignIn />
    </main>
  );
}
