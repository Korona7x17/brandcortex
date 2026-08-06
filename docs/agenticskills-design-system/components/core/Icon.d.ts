import * as React from 'react';

export declare const ICONS: Record<string, string>;
export type IconName = keyof typeof ICONS;

/**
 * Line-glyph icon. Stroke-only, currentColor, no fills.
 * Intentional addition — the source hand-codes these paths inline; this wraps them.
 */
export interface IconProps extends React.SVGAttributes<SVGSVGElement> {
  /** One of the keys in ICONS. */
  name: string;
  /** Square edge in px. 18 in cards, 22 in step glyphs, 14 inline. Default 18. */
  size?: number;
  /** 1.6 for display glyphs, 2 for small inline marks. Default 1.6. */
  strokeWidth?: number;
}
export function Icon(props: IconProps): JSX.Element | null;