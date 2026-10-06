import { useEffect, useState } from 'react'
import { api } from '../api'

function ChurnSummary() {
  const [summary, setSummary] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        setLoading(true)
        const { data } = await api.get('/churn/summary')
        setSummary(data)
        setError('')
      } catch (err) {
        setError(err.response?.data?.detail || 'Unable to load churn summary.')
      } finally {
        setLoading(false)
      }
    }

    fetchSummary()
  }, [])

  if (loading) return <p className="status">Loading summary...</p>
  if (error) return <p className="error">{error}</p>
  if (!summary) return null

  const contractRates = (summary.by_contract || []).map((item) => Number(item.churn_rate || 0))
  const maxContractRate = Math.max(...contractRates, 1)

  return (
    <div className="page-block">
      <h2>Churn summary</h2>
      <p className="page-description">
        Executive overview of total customers, churned accounts, and contract-level churn trends.
      </p>

      <div className="stats-grid">
        <div className="stat-card">
          <span>Total customers</span>
          <strong>{summary.total_customers}</strong>
        </div>
        <div className="stat-card">
          <span>Total churned</span>
          <strong>{summary.churned_customers}</strong>
        </div>
        <div className="stat-card">
          <span>Churn rate</span>
          <strong>{Number(summary.churn_rate || 0).toFixed(1)}%</strong>
        </div>
      </div>

      <div className="table-card">
        <h3>Contract churn</h3>
        <table>
          <thead>
            <tr>
              <th>Contract type</th>
              <th>Total</th>
              <th>Churned</th>
              <th>Churn rate</th>
            </tr>
          </thead>
          <tbody>
            {(summary.by_contract || []).map((item) => (
              <tr key={item.contract_type}>
                <td>{item.contract_type}</td>
                <td>{item.total}</td>
                <td>{item.churned}</td>
                <td>
                  <div className="bar-row">
                    <span>{Number(item.churn_rate || 0).toFixed(1)}%</span>
                    <div className="bar-track">
                      <div
                        className="bar-fill"
                        style={{ width: `${(Number(item.churn_rate || 0) / maxContractRate) * 100}%` }}
                      />
                    </div>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default ChurnSummary
