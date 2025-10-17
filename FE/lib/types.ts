// Type definitions for MDBS Dashboard

// Database server keys
export type DBKey = "mysql" | "postgresql" | "mongodb" | "oracle"

// Server status types
export type ServerStatus = "online" | "offline" | "starting" | "restarting" | "degraded"

// Individual server state
export interface ServerState {
  status: ServerStatus
  cpu: number
  memory: number
  uptime: string
}

// All server states
export type ServerStates = {
  [K in DBKey]: ServerState
}

// Performance data point for charts
export interface PerformancePoint {
  name: string
  mysql: number
  postgresql: number
  mongodb: number
  oracle: number
}

// Connection status item
export interface ConnectionItem {
  name: string
  connections: number
  maxConnections: number
  color: string
}

// Docker stats API response types
export interface DockerContainer {
  id: string
  name: string
  image: string
  cpu: number
  mem_bytes: number
  mem_limit: number
  mem_perc: number
  state: string
  net_rx: number
  net_tx: number
  block_read: number
  block_write: number
}

export interface DockerStatsResponse {
  containers: DockerContainer[]
  ok: boolean
}
