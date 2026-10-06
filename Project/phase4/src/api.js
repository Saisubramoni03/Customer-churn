import axios from 'axios'

const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const apiKey = import.meta.env.VITE_API_KEY || 'mysecret123'

const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  if (!config.headers) {
    config.headers = {}
  }

  if (!config.headers['X-API-Key']) {
    config.headers['X-API-Key'] = apiKey
  }

  return config
})

export { api, baseURL }
