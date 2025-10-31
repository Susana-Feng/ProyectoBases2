import React, { useEffect, useState } from "react";
import { MoonStar, Sun } from 'lucide-react';

export default function DarkToggle() {
  const [mode, setMode] = useState<'light'|'dark'>(() => {
    if (typeof window === 'undefined') return 'light';
    const saved = localStorage.getItem('theme');
    if (saved === 'dark' || saved === 'light') return saved;
    // follow system preference by default
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  useEffect(() => {
    document.documentElement.classList.toggle('dark', mode === 'dark');
    localStorage.setItem('theme', mode);
  }, [mode]);

  return (
    <button
      onClick={() => setMode(prev => prev === 'dark' ? 'light' : 'dark')}
      aria-label="Toggle dark mode"
      className="px-2 py-1 rounded border dark:border-neutral-700"
    >
      {mode === 'dark' ? <MoonStar /> :<Sun/>}
    </button>
  );
}