export async function client<T>(
  url: string,
  options?: RequestInit,
): Promise<{ data: T | null; error: string | null }> {
  try {
    const response = await fetch(url, options)
    if (!response.ok) {
      return { data: null, error: response.statusText }
    }
    try {
      const data = await response.json() as T
      return { data, error: null }
    } catch {
      return { data: null, error: 'Invalid response' }
    }
  } catch {
    return { data: null, error: 'Network error' }
  }
}
