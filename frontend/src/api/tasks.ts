import { client } from '@/api/client'
import { FORKLIFT_ID } from '@/config'
import type { Task, CreateTaskPayload } from '@/types/api'

export function getTasks(): Promise<{ data: Task[] | null; error: string | null }> {
  return client<Task[]>(`/api/tasks/?forklift=${FORKLIFT_ID}`)
}

export function createTask(
  payload: CreateTaskPayload,
): Promise<{ data: Task | null; error: string | null }> {
  return client<Task>('/api/tasks/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function cancelTask(
  taskId: number,
): Promise<{ data: Task | null; error: string | null }> {
  return client<Task>(`/api/tasks/${taskId}/cancel/`, {
    method: 'POST',
  })
}
