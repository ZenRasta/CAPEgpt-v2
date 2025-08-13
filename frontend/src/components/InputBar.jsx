import React, { useRef, useState } from 'react';
import { Paperclip, Mic, Camera, Send } from 'lucide-react';

export default function InputBar({ value, onChange, onSend }) {
  const fileRef = useRef(null);
  const [file, setFile] = useState(null);

  const handleSend = () => {
    if (!value && !file) return;
    onSend(value, file);
    onChange('');
    setFile(null);
    if (fileRef.current) fileRef.current.value = '';
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex items-end gap-2 p-4 border-t border-white/10">
      <button
        type="button"
        onClick={() => fileRef.current && fileRef.current.click()}
        className="p-2 rounded hover:bg-white/20 transition"
      >
        <Paperclip size={20} />
      </button>
      <button type="button" className="p-2 rounded hover:bg-white/20 transition">
        <Mic size={20} />
      </button>
      <button type="button" className="p-2 rounded hover:bg-white/20 transition">
        <Camera size={20} />
      </button>
      <textarea
        className="flex-1 resize-none bg-transparent outline-none text-white p-2"
        rows={1}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask something..."
      />
      <button
        type="button"
        onClick={handleSend}
        className="p-2 rounded bg-gradient-to-r from-electric-cyan to-hyper-violet text-white"
      >
        <Send size={20} />
      </button>
      <input
        type="file"
        ref={fileRef}
        onChange={(e) => setFile(e.target.files[0])}
        className="hidden"
      />
    </div>
  );
}
