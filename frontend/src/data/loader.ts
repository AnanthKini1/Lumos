/**
 * WS-C — Simulation data loader.
 *
 * Abstracts where simulation output comes from so the rest of the frontend
 * never knows whether it's reading a bundled file or a live backend response.
 *
 * LIVE_MODE = false  → persona/topic catalog served from bundled catalog.json;
 *                      scenario loads fall back to mock_simulation.json.
 * LIVE_MODE = true   → all data fetched from the backend API.
 *
 * All other components import from this file exclusively — never import JSON
 * or fetch data directly in a component.
 */

import type { SimulationOutput, PersonaProfile, TopicProfile, StrategyDefinition } from '../types/simulation'
import mockData from './mock_simulation.json'
import catalogData from './catalog.json'

const LIVE_MODE = false // flip to true to hit the backend API

// ---------------------------------------------------------------------------
// Catalog — personas, topics, strategies (real data from backend JSON files)
// ---------------------------------------------------------------------------

interface Catalog {
  personas: PersonaProfile[]
  topics: TopicProfile[]
  strategies: StrategyDefinition[]
}

export async function loadCatalog(): Promise<Catalog> {
  if (!LIVE_MODE) {
    return catalogData as Catalog
  }
  const res = await fetch('/api/catalog')
  if (!res.ok) throw new Error('Failed to load catalog')
  return res.json() as Promise<Catalog>
}

// ---------------------------------------------------------------------------
// Scenarios — simulation output
// ---------------------------------------------------------------------------

export async function loadScenario(scenarioId: string): Promise<SimulationOutput> {
  if (!LIVE_MODE) {
    // Return mock regardless of scenarioId — swap for a real cached file per scenario
    // as pre-generated scenario JSONs are added to this directory.
    return mockData as SimulationOutput
  }
  const res = await fetch(`/api/scenarios/${scenarioId}`)
  if (!res.ok) {
    // Scenario not cached yet — trigger a new run
    const [personaId, topicId] = scenarioId.split('__')
    const runRes = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario_id: scenarioId, persona_id: personaId, topic_id: topicId }),
    })
    if (!runRes.ok) throw new Error(`Failed to run scenario '${scenarioId}'`)
    return runRes.json() as Promise<SimulationOutput>
  }
  return res.json() as Promise<SimulationOutput>
}

export async function listScenarios(): Promise<string[]> {
  if (!LIVE_MODE) {
    return [(mockData as SimulationOutput).metadata.scenario_id]
  }
  const res = await fetch('/api/scenarios')
  if (!res.ok) throw new Error('Failed to list scenarios')
  return res.json() as Promise<string[]>
}
