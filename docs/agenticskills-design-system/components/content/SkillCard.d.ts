import * as React from 'react';

/**
 * Standard index card for a skill or MCP server.
 * @startingPoint section="Content" subtitle="Skill index card" viewport="700x280"
 */
export interface SkillCardProps extends React.HTMLAttributes<HTMLElement> {
  name: string;
  author?: string;
  description?: string;
  /** Rendered as the single solid tag. */
  category?: string;
  /** Platform labels, rendered as hairline tags. Cap at ~4 plus a '+N'. */
  platforms?: string[];
  installs?: string;
  stars?: string;
  /** Shows the verified check beside the name. */
  official?: boolean;
  rank?: 'S' | 'A' | 'B' | 'C';
  href?: string;
  /** Foot-right affordance text. Default 'Open \u2197'. */
  action?: string;
}
export function SkillCard(props: SkillCardProps): JSX.Element;