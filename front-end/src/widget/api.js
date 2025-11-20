const RAW_BASE = import.meta.env.VITE_WIDGET_API || window.CS_WIDGET_API || ''
const BASE_URL = RAW_BASE ? RAW_BASE.replace(/\/$/, '') : ''
const DEFAULT_ORIGIN = typeof window !== 'undefined' ? window.location.origin : ''

let API_ORIGIN = DEFAULT_ORIGIN
if (BASE_URL) {
  try {
    API_ORIGIN = new URL(BASE_URL, DEFAULT_ORIGIN).origin
  } catch {
    API_ORIGIN = DEFAULT_ORIGIN
  }
}

const getWsOrigin = () => API_ORIGIN.replace(/^http/, 'ws')

const request = async (url, options = {}) => {
  const base = BASE_URL || ''
  const res = await fetch(base + url, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    credentials: 'include',
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || '请求失败')
  }
  return res.json()
}

export const initGuestSession = (payload) =>
  request('/api/customer-service/guest/session/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })

export const sendGuestMessage = (payload) =>
  request('/api/customer-service/guest/messages/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })

export const fetchGuestHistory = (params) =>
  request(`/api/customer-service/guest/messages/history/?${new URLSearchParams(params).toString()}`, {
    method: 'GET',
  })

export const buildGuestWsUrl = (sessionId, token) => {
  const origin = getWsOrigin()
  return `${origin}/ws/customer-service/guest/${sessionId}/${token}/`
}



