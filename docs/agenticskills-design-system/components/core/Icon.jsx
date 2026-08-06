import React from 'react';

export const ICONS = {
  search:'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14M20 20l-3.5-3.5',
  download:'M12 3v14m-5-5 5 5 5-5M5 21h14',
  star:'M12 2 15 9 22 9.5 17 14.5 18.5 22 12 18 5.5 22 7 14.5 2 9.5 9 9Z',
  check:'M9 12l2 2 4-4M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z',
  terminal:'M4 17l6-6-6-6M12 19h8',
  rocket:'M5 19l7-14 7 14M9 14h6',
  layout:'M3 9.5h18M3 14.5h18M9 3.5v17M15 3.5v17',
  server:'M2 5h20v6H2zM2 13h20v6H2zM6 8h.01M6 16h.01',
  shield:'M12 2l8 4v6c0 5-3.5 9-8 10-4.5-1-8-5-8-10V6z',
  flask:'M9 2h6M12 2v8M5 12c0 5 3 8 7 8s7-3 7-8Z',
  brain:'M9 8a3 3 0 1 1 6 0c0 1.5-1 2.5-2 3.5M12 17h.01M5 20h14M9 4h6',
  chart:'M3 3v18h18M7 14l4-4 4 4 5-7',
  pen:'M4 4h16v16H4zM4 9h16M9 4v16',
  trend:'M3 17l6-6 4 4 8-8M14 7h7v7',
  palette:'M3 12a9 9 0 1 0 18 0 9 9 0 0 0-18 0zM12 3v18M3 12h18',
  zap:'M13 2 4 14h7l-1 8 9-12h-7z',
  file:'M14 2H6v20h12V8zM14 2v6h4M9 13h6M9 17h6',
  database:'M4 6c0-2 4-3 8-3s8 1 8 3v12c0 2-4 3-8 3s-8-1-8-3zM4 12c0 2 4 3 8 3s8-1 8-3',
  mobile:'M7 2h10v20H7zM10 19h4',
  blocks:'M5 5h6v6H5zM13 5h6v6h-6zM5 13h6v6H5zM13 13h6v6h-6z',
  arrowRight:'M5 12h14M13 5l7 7-7 7',
  arrowUpRight:'M7 17 17 7M7 7h10v10'
};

export function Icon({name,size=18,strokeWidth=1.6,...rest}){
  const d = ICONS[name];
  if(!d) return null;
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"
         aria-hidden="true" {...rest}><path d={d} /></svg>
  );
}