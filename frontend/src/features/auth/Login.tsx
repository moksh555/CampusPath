import { config } from "@/lib/configuration";
export function Login({ error }: { error?: string }) {
  return (
    <main className="login">
      <div className="orb" />
      <section className="glass login-card">
        <div className="brand-mark">C</div>
        <p className="eyebrow">CAMPUSPATH</p>
        <h1>
          Your next chapter.
          <br />
          <span>A clearer choice.</span>
        </h1>
        <p>
          Explore universities around the world. Ask the questions that matter.
          Find your own path.
        </p>
        <a className="primary google" href={config.apiUrl + "/auth/login"}>
          Continue with Google <span>↗</span>
        </a>
        {error && <p className="muted">{error}</p>}
        <small>A space for your possibilities.</small>
      </section>
    </main>
  );
}
