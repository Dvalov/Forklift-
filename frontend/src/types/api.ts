export interface Forklift {
  id: number
  name: string
  charge_level: number
  status: 'idle' | 'busy' | 'charging' | 'error'
  position_x: number
  position_y: number
  position_z: number
  updated_at: string
}

export interface Task {
  id: number
  forklift_id: number
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  origin_x: number
  origin_y: number
  origin_z: number
  dest_x: number
  dest_y: number
  dest_z: number
  dest_cell_x: number
  dest_cell_y: number
  dest_cell_z: number
  created_at: string
  updated_at: string
}

export interface Cell {
  id: number
  x: number
  y: number
  z: number
  available: boolean
}

export interface Coordinates {
  x: number
  y: number
  z: number
}

export interface CreateTaskPayload {
  forklift_id: number
  dest_x: number
  dest_y: number
  dest_z: number
  dest_cell_x: number
  dest_cell_y: number
  dest_cell_z: number
}
