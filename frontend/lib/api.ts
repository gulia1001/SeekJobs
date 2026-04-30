import type { AnalysisResult, GeneratedCV, JobsResponse } from './types'

const API_BASE = 'http://127.0.0.1:8001/api/'
console.log('API_LIB_LOADED_V4_XHR')

export async function fetchJobs(params: {
  page?: number
  limit?: number
  category?: string
  level?: string
  format?: string
}): Promise<JobsResponse> {
  const query = new URLSearchParams()
  query.set('page', String(params.page ?? 1))
  query.set('limit', String(params.limit ?? 12))
  if (params.category && params.category !== 'all') query.set('category', params.category)
  if (params.level && params.level !== 'all') query.set('level', params.level)
  if (params.format && params.format !== 'all') query.set('format', params.format)

  const res = await fetch(`${API_BASE}jobs?${query}`)
  return res.json()
}

export async function analyzeProfile(formData: FormData): Promise<AnalysisResult> {
  console.log('Directly calling backend process via XHR (v4):', `${API_BASE}process`)
  
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${API_BASE}process`, true)
    
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText))
        } catch (e) {
          reject(new Error('Failed to parse server response'))
        }
      } else {
        try {
          const err = JSON.parse(xhr.responseText)
          reject(new Error(err.detail || err.error || `Server error ${xhr.status}`))
        } catch {
          reject(new Error(`Server error ${xhr.status}`))
        }
      }
    }
    
    xhr.onerror = () => {
      reject(new Error('Network error — check if the backend is running on port 8001'))
    }
    
    // XHR handles FormData correctly without setting Content-Type header manually
    xhr.send(formData)
  })
}

export async function generateCV(payload: {
  job_id: string
  job_title: string
  job_skills: string[]
  user_profile: unknown
  cv_text?: string
}): Promise<GeneratedCV> {
  const res = await fetch(`${API_BASE}cv/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return res.json()
}
