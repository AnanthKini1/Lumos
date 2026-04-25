# Workstream C — Incremental Implementation Plan

Workstream C owns the complete frontend: 3-screen React app reading cached SimulationOutput JSON.
Each step below is implemented on its own git branch.

Tech stack: React 18 + Vite + TypeScript (strict) + Tailwind CSS + Framer Motion + Recharts.
Mock data: `frontend/src/data/mock_simulation.json` (schema-valid, 2 strategies, 6 turns).
All types locked at: `frontend/src/types/simulation.ts` — do not modify.

---

## Design Language

**Palette (light, clean):**
- Base background:     `slate-50`
- Public panel:        `white` / `slate-100` borders
- Private panel:       `violet-50` (#f5f3ff) + `violet-200` border accent
- Accent (warnings):   `amber-500`
- Success:             `emerald-600`
- Danger:              `rose-500`
- Primary text:        `slate-900`
- Muted text:          `slate-500`
- Interactive/focus:   `violet-600`

**Verdict color map (light-bg):**
- GENUINE_BELIEF_SHIFT → emerald-100 bg / emerald-700 text
- PARTIAL_SHIFT        → sky-100 bg / sky-700 text
- SURFACE_COMPLIANCE   → amber-100 bg / amber-700 text
- BACKFIRE             → rose-100 bg / rose-700 text
- NO_MOVEMENT          → slate-100 bg / slate-600 text

**Emotion color map (light-bg):**
- defensive / threatened: rose-500 / red-500
- curious / engaged:      sky-500 / emerald-600
- intrigued:              violet-500
- warm:                   amber-500
- frustrated:             orange-500
- dismissed / bored:      slate-400

**Typography:**
- Public panel:     system-ui, normal weight, slate-900
- Monologue:        italic, text-violet-900 (inner voice feel on violet-50 bg)
- Badges/verdicts:  font-mono, uppercase

---

## Steps (optimal order)

### Step 1 — `feature/design-system-app-shell`
Foundation. Tailwind theme, CSS vars, App.tsx state machine, screen routing.
- tailwind.config.ts: extend theme with palette + verdict/emotion color maps
- index.css: CSS custom properties, light color-scheme, thin scrollbar
- App.tsx: Screen state machine (setup | mindviewer | report), SimulationOutput state,
  deepLinkStrategyId for report→mindviewer navigation, AnimatePresence screen fade

### Step 2 — `feature/setup-screen`
Screen 1. Persona gallery + side panel + topic cards + Run button.
- Persona cards: display_name, demographic_shorthand, core_values pills, citation badge.
  Selected: amber ring. Hover: scale 1.02 (Framer Motion whileHover).
- Side panel: slides in from right (Framer Motion x: 100%→0). Full persona profile +
  predicted_behavior_under_strategies + citation link.
- Topic cards: horizontal row. display_name + context_briefing preview +
  predicted starting stance for selected persona.
- Run button: disabled until persona+topic selected. Amber bg when active.
  Calls loadScenario('demo_v1'), transitions to MindViewer.

### Step 3 — `feature/mind-viewer-shell`
Screen 2 skeleton. Strategy tabs, turn navigation, layout. Child panels = stubs.
- Strategy tabs: one tab per outcome. Colored verdict dot. Framer Motion layoutId underline.
- Turn controls: prev/next buttons, play/pause. useEffect setInterval(2000ms) auto-advance.
- Layout: side-by-side on lg breakpoint (PublicConversation left, InternalMind right).
- AnimatePresence crossfade on strategy tab switch (150ms).
- Top bar: persona name, topic, "View Report →" button.
- strategyDisplayName helper: snake_case id → Title Case fallback.

### Step 4 — `feature/public-conversation`
Left panel: chat bubble transcript with typing animation.
- Renders turns.slice(0, currentTurn+1) only.
- Interviewer bubble: slate-100 bg. Persona bubble: white + slate-200 border.
- Current turn public_response: character-reveal typing (20ms/char, useEffect).
- Strategy note annotation below interviewer bubble (italic, slate-500, sm).
- Auto-scroll to bottom anchor on currentTurn change.
- Turn number badge above each exchange.

### Step 5 — `feature/internal-mind`
Right panel: THE HERO VIEW. Make-or-break component.
- Panel bg: violet-50 + border-l-2 border-violet-200. Header: "INTERNAL MONOLOGUE",
  text-violet-400, tracking-widest, text-xs.
- Monologue text: current turn italic text-violet-900 with 15ms/char typing reveal.
  Prior turns: opacity-40 text-violet-700, 2-line truncation with gradient fade.
- Emotion badge: pill top-right. Color from emotion map (-100 bg / -700 text).
  Framer Motion color transition 300ms. Shows trigger text below.
- Identity threat: threatened=true → border-l-4 border-rose-400 + bg-rose-50 shift.
  Framer Motion animate border+bg. Badge: "Identity threatened: X" in rose-100/rose-600.
- Private stance ticker: "Private Stance: N.N / 10". Framer Motion useMotionValue
  smooth animation. Direction arrow: ↓ emerald-600 / ↑ rose-500 / → slate-400.
  private_stance_change_reason below in text-sm italic text-violet-600.
- Memory residue cards: ALL prior turns stack. Current: amber-50 + amber-200 border.
  Prior: white + slate-200. Framer Motion layout for smooth insertion.

### Step 6 — `feature/comparison-report-grid`
Screen 3: insight synthesis + comparison table.
- Insight Synthesis: white card, border-l-4 amber-400. overall_synthesis in text-slate-900.
- Table: bg-white border border-slate-200 rounded-lg. Columns: Strategy | Verdict |
  Public Δ | Private Δ | Max Gap | Threats | Persistence.
- Δ computed from trajectory arrays. Max gap from gap_per_turn.
- Verdict badges: light-bg color map (emerald-100/emerald-700 etc).
- Row hover: bg-slate-50. Sorted: GENUINE_BELIEF_SHIFT first, BACKFIRE last.
- "← Back to Mind Viewer" link top-left.

### Step 7 — `feature/trajectory-chart`
TrajectoryChart in ComparisonReport. The Devpost hero image.
- ComposedChart: Area (gap fill amber/30), Line solid sky-400 (public),
  Line dashed violet-400 (private). Final "Cool" point from cooling_off stance.
- Chart bg: white. Border-top-2: emerald-400 (GENUINE), rose-400 (BACKFIRE), slate-300 (other).
- Tooltip: white bg, slate-200 border, slate-900 text.
- Small-multiples grid: grid-cols-1 lg:grid-cols-2 gap-4.

### Step 8 — `feature/strategy-cards`
Expandable StrategyCards wired into ComparisonReport.
- Collapsed: verdict-colored left border + verdict badge + verdict_reasoning line.
- Expanded (Framer Motion height animation): cognitive_scores mini-badges row,
  standout_quotes blockquotes (violet-50 + violet-300 left border), synthesis_paragraph
  (amber-300 left border), "Watch Transcript →" in violet-600.
- GENUINE_BELIEF_SHIFT: border-emerald-200 card + border-l-4 border-emerald-400.
- BACKFIRE: border-rose-200 + border-l-4 border-rose-400 + identity threat warning badge.

### Step 9 — `feature/sources-panel`
Persistent "Sources & Methodology" drawer. Credibility layer.
- Fixed bottom-left trigger link (slate-400 → slate-600 hover).
- Framer Motion right drawer (x: 100%→0). White bg, border-l slate-200, shadow-xl.
- Sections: Personas (citations+links), Strategies (academic citations+links),
  Measurement Methodology (one paragraph per cognitive dimension), Validation note.
- Add as persistent overlay in App.tsx (always rendered, isOpen controlled).

### Step 10 — `feature/pitch-mode-polish`
Demo-ready. Pitch mode + final polish.
- ?pitch=1 param: skip setup, auto-load demo_v1, auto-play through all screens.
- Polish order: spacing → hover/focus states → color transitions → loading skeletons
  → breadcrumb nav → error boundary.
- STOP adding features after this step.

---

## Verification (End-to-End)

1. npm run dev → localhost:5173 shows light SetupScreen (Karen M. + RTO topic)
2. Select persona → slide-in side panel with Pew citation
3. Select topic → Run activates → transitions to MindViewer
4. Tab 1 (Personal Narrative): 6 turns, monologue types, memory cards stack
5. Tab 2 (Authority Expert): emotion badge → defensive, identity threat fires
6. "View Report" → grid, two charts, two strategy cards
7. Expand GENUINE_BELIEF_SHIFT card → quotes, synthesis, deep-link back
8. npm run build → zero TS errors
9. ?pitch=1 → auto-plays demo
