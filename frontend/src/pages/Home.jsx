import { Link } from 'react-router-dom';

function Hero() {
  return (
    <section className="relative bg-hero-gradient text-white">
      <div className="container min-h-[420px] lg:min-h-[480px] flex flex-col items-center justify-center text-center">
        <h1 aria-hidden
            className="select-none pointer-events-none absolute inset-x-0 top-10 hidden md:block
                       text-6xl lg:text-7xl font-extrabold opacity-10 tracking-tightish">
          Your AI Buddy for CAPE Exams!
        </h1>

        <h2 className="relative text-3xl lg:text-4xl font-extrabold tracking-tightish">
          Your AI Buddy for CAPE Exams! ✨
        </h2>
        <p className="mt-3 text-lg lg:text-xl opacity-95 max-w-2xl">
          Snap questions, get lit solutions, and level up your game! 🎮
        </p>

        <div className="mt-6">
          <Link
            to="/upload"
            className="inline-flex items-center justify-center rounded-full bg-white text-brand-blue
                       font-semibold px-8 py-3 shadow-pill hover:shadow-lg hover:opacity-95 transition">
            Let's Go! 🚀
          </Link>
        </div>
      </div>
    </section>
  );
}

function Section({ title, children }) {
  return (
    <section className="bg-brand-bg">
      <div className="container py-12 lg:py-16">
        <h3 className="text-2xl lg:text-3xl font-extrabold text-brand-blue text-center">{title} 🔮</h3>
        <div className="mt-6 grid gap-6 md:grid-cols-2">{children}</div>
      </div>
    </section>
  );
}

function Card({ children }) {
  return (
    <div className="bg-white rounded-3xl p-6 shadow-card hover:-translate-y-0.5 hover:shadow-xl transition">
      {children}
    </div>
  );
}

export default function Home() {
  return (
    <>
      <Hero />
      <Section title="Quick Vibes Examples">
        <Card>
          <h4 className="text-xl font-semibold">Differentiate f(x) = x²eˣ 🧮</h4>
          <Link to="/popular" className="mt-3 inline-block text-brand-blue font-semibold">View Solution ✨</Link>
        </Card>
        <Card>
          <h4 className="text-xl font-semibold">Projectile Motion: Max Height 🚀</h4>
          <Link to="/popular" className="mt-3 inline-block text-brand-blue font-semibold">View Solution ✨</Link>
        </Card>
      </Section>
      <Section title="Drop Your Question">
        <Card>
          <p className="text-gray-700">
            Snap a past-paper question and we'll analyze it for strengths & weaknesses.
          </p>
          <Link
            to="/upload"
            className="mt-4 inline-flex items-center justify-center rounded-full bg-brand-blue text-white
                       font-semibold px-6 py-2 hover:bg-[#2f6fdb] transition">
            Upload 📸
          </Link>
        </Card>
      </Section>
    </>
  );
}