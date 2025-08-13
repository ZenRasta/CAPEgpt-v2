import { useState } from 'react';
import { useAvatar } from '../context/AvatarProvider.jsx';

const PACKS = ['classic', 'animals'];
const VARIANTS = ['math', 'science', 'language'];
const SEASONS = ['default', 'winter', 'summer'];

export default function SettingsPopover() {
  const { pack, variant, season, setPack, setVariant, setSeason } = useAvatar();
  const [open, setOpen] = useState(false);

  return (
    <div className="relative inline-block text-left">
      <button
        className="px-3 py-2 bg-white/10 rounded-md text-white text-sm hover:bg-white/20"
        onClick={() => setOpen(!open)}
      >
        Avatar Settings
      </button>
      {open && (
        <div className="absolute z-10 right-0 mt-2 w-56 rounded-md shadow-lg bg-white/90 text-gray-900">
          <div className="p-4 space-y-4">
            <div>
              <h4 className="text-xs font-semibold uppercase text-gray-500 mb-2">Pack</h4>
              <div className="flex flex-wrap gap-2">
                {PACKS.map(p => (
                  <button
                    key={p}
                    onClick={() => setPack(p)}
                    className={`px-2 py-1 rounded text-sm ${p === pack ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-900'}`}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <h4 className="text-xs font-semibold uppercase text-gray-500 mb-2">Season</h4>
              <div className="flex flex-wrap gap-2">
                {SEASONS.map(s => (
                  <button
                    key={s}
                    onClick={() => setSeason(s)}
                    className={`px-2 py-1 rounded text-sm ${s === season ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-900'}`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <h4 className="text-xs font-semibold uppercase text-gray-500 mb-2">Variant</h4>
              <div className="flex flex-wrap gap-2">
                {VARIANTS.map(v => (
                  <button
                    key={v}
                    onClick={() => setVariant(v)}
                    className={`px-2 py-1 rounded text-sm ${v === variant ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-900'}`}
                  >
                    {v}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
