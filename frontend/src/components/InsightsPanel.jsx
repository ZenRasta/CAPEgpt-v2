import React, { useEffect, useState } from 'react';
import GlassCard from './GlassCard';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export default function InsightsPanel() {
  const [activeTab, setActiveTab] = useState('popular');
  const [popular, setPopular] = useState([]);
  const [leaders, setLeaders] = useState([]);
  const [isMobile, setIsMobile] = useState(false);
  const [isOpen, setIsOpen] = useState(true);

  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 800;
      setIsMobile(mobile);
      setIsOpen(!mobile); // hide panel by default on mobile
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        if (activeTab === 'popular' && popular.length === 0) {
          const res = await fetch(`${API_BASE_URL}/questions/popular`);
          const data = await res.json();
          setPopular(data.popular_questions || data);
        }
        if (activeTab === 'leaderboard' && leaders.length === 0) {
          const res = await fetch(`${API_BASE_URL}/leaderboard`);
          const data = await res.json();
          setLeaders(data.leaderboard || data);
        }
      } catch (err) {
        console.error('Failed to load insights', err);
      }
    };
    fetchData();
  }, [activeTab]);

  const tabButton = (tab, label) => (
    <button
      onClick={() => setActiveTab(tab)}
      className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
        activeTab === tab
          ? 'bg-electric-cyan text-black'
          : 'bg-white/10 text-white hover:bg-white/20'
      }`}
    >
      {label}
    </button>
  );

  const renderPopular = () => (
    popular.map((q) => (
      <GlassCard key={q.id} className="p-4">
        <p className="text-sm text-white/90">{q.content || q.question}</p>
      </GlassCard>
    ))
  );

  const renderLeaderboard = () => (
    leaders.map((l, idx) => (
      <GlassCard key={l.id || idx} className="p-4">
        <p className="text-sm text-white/90">
          {l.name || l.user || `#${idx + 1}`}: {l.score ?? l.points}
        </p>
      </GlassCard>
    ))
  );

  return (
    <div className="relative">
      {isMobile && (
        <button
          className="mb-2 px-3 py-1 bg-electric-cyan text-black rounded-md text-sm font-semibold"
          onClick={() => setIsOpen((o) => !o)}
        >
          {isOpen ? 'Hide Insights' : 'Show Insights'}
        </button>
      )}
      {(!isMobile || isOpen) && (
        <div className="flex flex-col h-full">
          <div className="flex gap-2 mb-3">
            {tabButton('popular', 'Popular')}
            {tabButton('leaderboard', 'Leaderboard')}
          </div>
          <div className="grid gap-3 overflow-auto">
            {activeTab === 'popular' ? renderPopular() : renderLeaderboard()}
          </div>
        </div>
      )}
    </div>
  );
}

