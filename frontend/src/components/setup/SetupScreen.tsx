/**
 * WS-C — Screen 1: Simulation configuration.
 *
 * Presents the user with three selection steps before running:
 *   1. Persona gallery — cards with demographic shorthand and source citation badge.
 *      Clicking a card shows the full first-person profile in a side panel.
 *   2. Topic selector — dropdown or card row of available topics.
 *   3. Strategy selection — 5-7 toggleable cards with citation badges.
 *      User must pick 3-5 strategies before the Run button activates.
 *
 * "Run Simulation" triggers loadScenario() (or the live API) and transitions
 * to the MindViewer screen. SetupScreen does not run the simulation itself —
 * it only collects the configuration and passes it up to App.
 *
 * Reads available personas/strategies/topics from the loaded SimulationOutput
 * metadata (or static lists when in demo mode). Owns no simulation logic.
 */

export default function SetupScreen() {
  return <div>TODO: SetupScreen</div>
}
