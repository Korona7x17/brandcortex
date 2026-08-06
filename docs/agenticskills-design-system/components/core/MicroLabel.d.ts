import * as React from 'react';

/** Mono uppercase label — eyebrows, stat captions, column headers, meta rows. */
export interface MicroLabelProps extends React.HTMLAttributes<HTMLElement> {
  children: React.ReactNode;
  /** 'micro' 11px (default) · 'nano' 10px for in-card metadata. */
  size?: 'micro' | 'nano';
  as?: keyof JSX.IntrinsicElements;
}
export function MicroLabel(props: MicroLabelProps): JSX.Element;