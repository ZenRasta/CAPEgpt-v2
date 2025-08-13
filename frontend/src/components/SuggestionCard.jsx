import React from 'react';

export default function SuggestionCard({ avatar, prompt, onSelect }) {
  return (
    <div
      className="flex items-center gap-3 p-4 bg-white/10 rounded-lg cursor-pointer hover:bg-white/20 transition"
      onClick={() => onSelect(prompt)}
    >
      {avatar && (
        <div className="w-10 h-10 rounded-full overflow-hidden flex-shrink-0">
          {avatar}
        </div>
      )}
      <p className="text-sm text-white/90">{prompt}</p>
    </div>
  );
}
