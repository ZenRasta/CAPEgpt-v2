import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import Login from './pages/Login';
import UploadQA from './pages/UploadQA';

function Popular() {
  return (
    <div className="bg-brand-bg">
      <div className="container py-12">
        <h1 className="text-3xl font-bold text-center mb-8 text-brand-blue">Popular Questions 🔥</h1>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <div className="bg-white rounded-3xl p-6 shadow-card">
            <h4 className="text-xl font-semibold mb-2">Differentiate f(x) = x²eˣ 🧮</h4>
            <p className="text-gray-600 text-sm mb-4">Asked 234 times</p>
            <button className="text-brand-blue font-semibold hover:underline">View Solution ✨</button>
          </div>
          <div className="bg-white rounded-3xl p-6 shadow-card">
            <h4 className="text-xl font-semibold mb-2">Projectile Motion: Max Height 🚀</h4>
            <p className="text-gray-600 text-sm mb-4">Asked 189 times</p>
            <button className="text-brand-blue font-semibold hover:underline">View Solution ✨</button>
          </div>
          <div className="bg-white rounded-3xl p-6 shadow-card">
            <h4 className="text-xl font-semibold mb-2">Solve ∫x³dx 📊</h4>
            <p className="text-gray-600 text-sm mb-4">Asked 156 times</p>
            <button className="text-brand-blue font-semibold hover:underline">View Solution ✨</button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Scoreboard() {
  return (
    <div className="bg-brand-bg">
      <div className="container py-12">
        <h1 className="text-3xl font-bold text-center mb-8 text-brand-blue">Scoreboard 🏆</h1>
        <div className="grid gap-8 md:grid-cols-2">
          <div className="bg-white rounded-3xl p-6 shadow-card">
            <h3 className="text-xl font-bold mb-4">Top Students 🥇</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span>John D. 🔥</span>
                <span className="font-bold">950 pts</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Sarah K. 💪</span>
                <span className="font-bold">920 pts</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Michael T. 🌟</span>
                <span className="font-bold">890 pts</span>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-3xl p-6 shadow-card">
            <h3 className="text-xl font-bold mb-4">Top Schools 🏫</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span>St. Mary's College 📚</span>
                <span className="font-bold">2500 pts</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Hillview College 🏆</span>
                <span className="font-bold">2300 pts</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Presentation College ⭐</span>
                <span className="font-bold">2100 pts</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/upload" element={<UploadQA />} />
          <Route path="/popular" element={<Popular />} />
          <Route path="/scoreboard" element={<Scoreboard />} />
          <Route path="/login" element={<Login />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}