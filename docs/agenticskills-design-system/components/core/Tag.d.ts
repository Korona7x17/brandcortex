import * as React from 'react';

/** Mono uppercase metadata chip — platforms, categories, licences. */
export interface TagProps extends React.HTMLAttributes<HTMLSpanElement> {
  children: React.ReactNode;
  /** 'default' hairline · 'solid' grey fill (category) · 'ink' black fill (emphasis). */
  variant?: 'default' | 'solid' | 'ink';
}
export function Tag(props: TagProps): JSX.Element;