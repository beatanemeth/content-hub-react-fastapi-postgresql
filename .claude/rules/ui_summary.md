---
paths:
  - 'frontend/src/components/**'
  - 'frontend/src/pages/**'
  - 'frontend/src/**/*.css'
---

# UI rules in short

The full specification is [ui_specifications.md](../../docs/claude/ui_specifications.md). Read the section for the page or component you build; do not rely on this summary alone.

- **Hand-written components:** no component library.
- **Files:** shared parts in `src/components/`, the five page components in `src/pages/`: `Home`, `BlogList`, `Post`, `PostForm` and `NotFound`.
- **Buttons:** three variants (`primary`, `secondary`, `tertiary`) from a `BUTTON_STYLE` lookup object. Navigation is a link, an action is a button.
- **Styling:** only the tokens in `src/globals.css` (`@theme`); colours and fonts are in [ui_visual_identity.md](./ui_visual_identity.md).
