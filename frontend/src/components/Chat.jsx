import React, { useState } from 'react';
import SuggestionCard from './SuggestionCard';
import MessageBubble from './MessageBubble';
import InputBar from './InputBar';
import { useAuth } from '../context/AuthProvider';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export default function Chat() {
  const { session } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  const sendMessage = async (text, file) => {
    if (!text && !file) return;
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    try {
      const authHeaders = {};
      if (session && session !== 'guest') {
        authHeaders['Authorization'] = `Bearer ${session.access_token}`;
      }

      let res;
      if (file) {
        const formData = new FormData();
        formData.append('file', file);
        res = await fetch(`${API_BASE_URL}/upload`, {
          method: 'POST',
          headers: authHeaders,
          body: formData
        });
      } else {
        res = await fetch(`${API_BASE_URL}/solve`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...authHeaders },
          body: JSON.stringify({ prompt: text })
        });
      }
      if (!res.ok) throw new Error('Network response was not ok');
      const data = await res.json();
      const answer = data.answer || data.result || data.response || 'No response';
      setMessages(prev => [...prev, { role: 'assistant', content: answer }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Failed to fetch answer.' }]);
    }
  };

  const suggestions = [
    'Differentiate x^2 e^x',
    'What is the derivative of sin(x)?',
    'Solve for x: 2x + 3 = 7',
    'Explain the chain rule in calculus'
  ];

  return (
    <div className="flex flex-col h-full">
      <header className="p-4 border-b border-white/10 text-lg font-bold">Chat</header>
      <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        {suggestions.map((s) => (
          <SuggestionCard key={s} prompt={s} onSelect={setInput} />
        ))}
      </div>
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
        {messages.map((m, i) => (
          <MessageBubble key={i} role={m.role}>
            {m.content}
          </MessageBubble>
        ))}
      </div>
      <InputBar value={input} onChange={setInput} onSend={sendMessage} />
    </div>
  );
}
