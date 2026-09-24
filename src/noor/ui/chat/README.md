# Noor Chat UI

Static HTML5/CSS3/JavaScript interface for the Noor Unified Automation Orchestra.

## Current scope

- Floating rounded Noor orb
- Click-to-open chat panel
- Responsive chat layout
- Message composer
- Enter-to-send and Shift+Enter for multiline input
- Suggested next-step actions
- Context-aware next-step suggestions for Excel, profiling, analysis, and formulas
- Keyboard accessibility including Escape-to-close
- Reduced-motion support

## Integration boundary

The current interface is intentionally frontend-only. `app.js` contains a small deterministic response layer so the interaction can be tested without a backend. The next integration step is to replace that response layer with a Noor orchestration endpoint that submits the user's request to the Unified Orchestra and renders its streamed/task-aware response.

## Files

- `index.html` — chat structure
- `styles.css` — responsive visual system and floating-orb interaction
- `app.js` — interaction, message handling, and next-step suggestion behavior
