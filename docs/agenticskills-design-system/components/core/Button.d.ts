import * as React from 'react';

/**
 * Primary action control. Square, ink-filled, no radius, no shadow.
 * @startingPoint section="Core" subtitle="Ink and ghost action buttons" viewport="700x150"
 */
export interface ButtonProps extends React.HTMLAttributes<HTMLElement> {
  children: React.ReactNode;
  /** 'primary' = ink fill; 'ghost' = transparent with ink hairline. Default 'primary'. */
  variant?: 'primary' | 'ghost';
  /** true renders a right arrow that nudges 2px on hover; or pass a custom glyph. */
  arrow?: boolean | string;
  /** Renders an <a> instead of a <button>. */
  href?: string;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
}
export function Button(props: ButtonProps): JSX.Element;