function App() {
  return (
    <main className="shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="FRIS home">
          <span className="brand-mark">F</span>
          <span>FRIS</span>
        </a>
        <span className="environment">Research intelligence</span>
      </header>
      <section className="welcome" aria-labelledby="welcome-title">
        <p className="eyebrow">FACULTY RESEARCH INTELLIGENCE SYSTEM</p>
        <h1 id="welcome-title">A clear view of faculty research.</h1>
        <p className="intro">
          Search across trusted scholarly sources, review author evidence, and
          bring each faculty member’s publications together.
        </p>
        <div className="foundation-card">
          <span className="status-dot" aria-hidden="true" />
          <div>
            <strong>Project foundation is ready</strong>
            <p>The faculty directory and publication workspace are coming next.</p>
          </div>
        </div>
      </section>
      <footer>Source-linked metadata · Explainable matching · Human review</footer>
    </main>
  );
}

export default App;
