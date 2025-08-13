import React from 'react';

export default function MessageBubble({ role = 'user', children }) {
  const isUser = role === 'user';
  const base = 'max-w-[75%] px-4 py-2 rounded-lg text-sm whitespace-pre-wrap';
  const userStyles = 'self-end bg-gradient-to-r from-electric-cyan to-hyper-violet text-white';
  const aiStyles = 'self-start bg-white/10 text-white';
  return <div className={`${base} ${isUser ? userStyles : aiStyles}`}>{children}</div>;
}
