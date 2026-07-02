import axios from 'axios'

const API_BASE = 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
})

export const getConditions = async () => {
  const response = await api.get('/conditions')
  return response.data
}

export const getOpportunities = async (conditions) => {
  const conditionString = Array.isArray(conditions) 
    ? conditions.join(',') 
    : conditions
  const response = await api.get(`/opportunities?conditions=${conditionString}`)
  return response.data
}

export const getOpportunityBrief = async (id) => {
  const response = await api.get(`/opportunities/${id}`)
  return response.data
}