# ModelVet Workbench design system

Adapted from the UI/UX design skill for the user-selected dark developer workbench. These are design requirements, not an accessibility certification.

## Visual language

- Charcoal background #0b0e13, raised panels #10151d/#151c26, borders #252e3a.
- Foreground #e7edf4; secondary text #97a3b4. Cyan #70dded for actions and active navigation.
- Decision colors: APPROVE #83dfb3; CONTROLS #b0bafc; BLOCK #f6969c; INSUFFICIENT #f0c17c. Every status also has a text label and icon.
- System sans-serif and system monospace fonts. No remote font imports or CDN resources.
- Compact left navigation, generous main-content spacing, restrained surface borders, clear evidence tables. Avoid decorative risk scores, invented metrics and fake progress.
- Motion is limited to actual loading indicators and short interaction transitions; honor prefers-reduced-motion.

## Behavior and access

- Keyboard focus is visible, navigation has accessible names/current state, dialogs use native focus management, and a skip link reaches main content.
- Coarse-pointer controls have 44px targets. Responsive coverage: 375, 768, 1024 and 1440 CSS pixels; table scrolling stays inside its container.
- Empty, loading, interrupted, failed and disconnected states explain what happened and expose a working next action.
- Demonstration reports remain visibly labeled and do not inflate saved report counts.
- Artifact strings are React text, never HTML. File/check evidence stays behind explicit drill-down.

Implementation tokens live in frontend/src/styles.css; report-workspace extensions live in workspace.css. Browser/contrast tests and visual inspection are recorded in verification/workbench.
