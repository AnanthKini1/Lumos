/**
 * WS-C — Simulation data loader.
 *
 * Abstracts where simulation output comes from so the rest of the frontend
 * never knows whether it's reading the mock fixture or a real cached file.
 *
 * In dev/demo mode: imports mock_simulation.json directly (instant, no server).
 * In live mode: fetches from the backend GET /api/scenarios/{id} endpoint.
 *
 * All other components import from this file — never import JSON or fetch
 * simulation data directly in a component.
 */

import type { SimulationOutput } from '../types/simulation'
import mockData from './mock_simulation.json'

const LIVE_MODE = false // flip to true to hit the backend API

export async function loadScenario(scenarioId: string): Promise<SimulationOutput> {
  if (!LIVE_MODE) {
    // Return mock regardless of scenarioId during development
    return mockData as SimulationOutput
  }
  const res = await fetch(`/api/scenarios/${scenarioId}`)
  if (!res.ok) throw new Error(`Scenario '${scenarioId}' not found`)
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
