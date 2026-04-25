/**
 * WS-C — Screen 1: Simulation configuration.
 *
 * Two selection steps only — strategies run automatically:
 *   1. Persona gallery — cards with demographic shorthand and source citation badge.
 *      Clicking a card shows the full first-person profile in a side panel.
 *   2. Topic selector — dropdown or card row of available topics.
 *
 * ALL configured strategies run in parallel automatically once the user hits
 * "Run Simulation." There is no strategy selection step.
 *
 * "Run Simulation" triggers loadScenario() (or the live API) and transitions
 * to the MindViewer screen. SetupScreen does not run the simulation itself —
 * it only collects persona + topic and passes the config up to App.
 *
 * Owns no simulation logic.
 */

export default function SetupScreen() {
  return <div>TODO: SetupScreen</div>
}
