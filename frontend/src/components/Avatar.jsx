import React from 'react';
import { useAvatar } from '../context/AvatarProvider.jsx';

const PACKS = {
  classic: '#3b82f6',
  animals: '#10b981',
};

const VARIANTS = {
  math: '#f59e0b',
  science: '#14b8a6',
  language: '#ef4444',
};

const SEASONS = {
  default: null,
  winter: '#e0f2fe',
  summer: '#fde68a',
};

export default function Avatar({ pack: packProp, variant: variantProp, season: seasonProp, size = 64 }) {
  const ctx = useAvatar();
  const pack = packProp || ctx.pack;
  const variant = variantProp || ctx.variant;
  const season = seasonProp || ctx.season;

  const base = PACKS[pack] || PACKS.classic;
  const accent = VARIANTS[variant] || VARIANTS.math;
  const overlay = SEASONS[season];

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      xmlns="http://www.w3.org/2000/svg"
      className="inline-block"
    >
      <circle cx="32" cy="32" r="30" fill={base} />
      <circle cx="22" cy="26" r="5" fill="#fff" />
      <circle cx="42" cy="26" r="5" fill="#fff" />
      <path
        d="M22 40c4 4 16 4 20 0"
        stroke={accent}
        strokeWidth="4"
        strokeLinecap="round"
        fill="none"
      />
      {overlay && <circle cx="32" cy="32" r="30" fill={overlay} opacity="0.3" />}
    </svg>
  );
}
