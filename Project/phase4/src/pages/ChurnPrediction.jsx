import { useState } from 'react'
import { api } from '../api'

const initialForm = {
  customer_id: '',
  tenure: 12,
  monthly_charges: 65,
  contract_type: 'Month-to-month',
  service_count: 2,
}

function ChurnPrediction() {
  const [formData, setFormData] = useState(initialForm)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormData((current) => ({
      ...current,
      [name]: name === 'tenure' || name === 'service_count' || name === 'monthly_charges'
        ? Number(value)
        : value,
    }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    try {
      setLoading(true)
      setError('')
      const { data } = await api.post('/predict-churn', formData)
      setResult(data)
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(Array.isArray(detail) ? detail[0]?.msg || 'Validation failed.' : detail || 'Unable to predict churn.')
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  const riskLevel = result
    ? result.risk_score >= 60
      ? 'high'
      : result.risk_score >= 30
        ? 'medium'
        : 'low'
    : 'neutral'

  return (
    <div className="page-block">
      <h2>Churn prediction</h2>

      <form className="prediction-form" onSubmit={handleSubmit}>
        <label>
          Customer ID
          <input name="customer_id" value={formData.customer_id} onChange={handleChange} placeholder="CU-1001" />
        </label>

        <label>
          Tenure (months)
          <input type="number" name="tenure" min="0" max="100" value={formData.tenure} onChange={handleChange} />
        </label>

        <label>
          Monthly charges
          <input type="number" name="monthly_charges" min="0" step="0.01" value={formData.monthly_charges} onChange={handleChange} />
        </label>

        <label>
          Contract type
          <select name="contract_type" value={formData.contract_type} onChange={handleChange}>
            <option value="Month-to-month">Month-to-month</option>
            <option value="One year">One year</option>
            <option value="Two year">Two year</option>
          </select>
        </label>

        <label>
          Service count
          <input type="number" name="service_count" min="0" max="6" value={formData.service_count} onChange={handleChange} />
        </label>

        <button type="submit" disabled={loading}>
          {loading ? 'Predicting...' : 'Predict churn risk'}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {result && (
        <div className={`result-card ${riskLevel}`}>
          <h3>Prediction result</h3>
          <p><strong>Customer:</strong> {formData.customer_id}</p>
          <p><strong>Risk score:</strong> {Number(result.risk_score).toFixed(2)}%</p>
          <p><strong>Prediction:</strong> {result.prediction}</p>
          <p><strong>Confidence:</strong> {Number(result.confidence).toFixed(2)}%</p>
        </div>
      )}
    </div>
  )
}

export default ChurnPrediction
