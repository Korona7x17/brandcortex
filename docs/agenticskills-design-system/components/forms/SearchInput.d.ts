import * as React from 'react';

/** Inline search field with a leading glyph and an optional result count. */
export interface SearchInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Result count shown at the right edge. */
  count?: number | string;
}
export function SearchInput(props: SearchInputProps): JSX.Element;