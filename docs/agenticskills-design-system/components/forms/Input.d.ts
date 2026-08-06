import * as React from 'react';

/** Square hairline text input. Focus darkens the border to ink — no glow, no ring. */
export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement & HTMLTextAreaElement> {
  /** Render a resizable <textarea> instead of an <input>. */
  multiline?: boolean;
}
export function Input(props: InputProps): JSX.Element;