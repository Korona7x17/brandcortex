import * as React from 'react';

export interface InstallStat { v: React.ReactNode; l: string }
export interface InstallMethod { label: string; command: string; note?: string }

/**
 * Ink-bordered distribution panel on skill detail pages:
 * status row, stat quad, copyable command, and method switcher.
 * @startingPoint section="Code" subtitle="Skill install panel" viewport="700x400"
 */
export interface InstallPanelProps extends React.HTMLAttributes<HTMLElement> {
  status?: string;
  statusLabel?: string;
  /** Typically four: installs, stars, compatibility, version. */
  stats?: InstallStat[];
  /** One entry per install route. More than one renders the switcher. */
  methods: InstallMethod[];
  label?: string;
  note?: string;
}
export function InstallPanel(props: InstallPanelProps): JSX.Element;