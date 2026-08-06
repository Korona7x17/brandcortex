# UI kit — Directory site

A click-through recreation of the AgenticSkills directory, composed entirely from the
primitives in `components/`. Nothing here re-implements a component; screens only
arrange them.

## Screens

| Route | File | What it shows |
|---|---|---|
| `home` | `Home.jsx` | Hero with terminal, Editor's picks, filterable index, 16-category grid, method row, platform reach |
| `skill` | `SkillDetail.jsx` | Detail hero with install panel, prose body with sticky TOC, compatibility matrix, related row |
| `category` | `CategoryBrowse.jsx` | Category hero with stats, filter bar, skill grid, adjacent categories |
| `mcp` | `McpDirectory.jsx` | MCP hero with `mcp.json` sample, featured servers, server index, integration categories |
| `submit` | `SubmitForm.jsx` | Two-column submission form with sticky criteria sidebar |

`Shell.jsx` wraps every route with the ticker, navbar, newsletter band and footer.
`App.jsx` holds the route state. `data.js` carries illustrative content on `window.DATA`.

## Interactions that work

- Navbar and footer links route between screens
- Homepage category filter chips filter the index grid in place
- Category page filters by rank and official status
- Skill cards and category cells navigate to their detail screens
- Install panel switches between CLI / Manual / Git and copies the command
- Submit form segmented controls select; submitting swaps the button label
- Newsletter form accepts a submit and confirms

## Not implemented

Search (the ⌘K trigger is a placeholder), mobile navigation, real data, and
authentication. See the Open questions section of the root `readme.md`.
