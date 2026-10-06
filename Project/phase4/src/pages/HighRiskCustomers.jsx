import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'

function HighRiskCustomers() {
  const [customers, setCustomers] = useState([])
  const [limit, setLimit] = useState(50)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [sortAsc, setSortAsc] = useState(true)

  useEffect(() => {
    const fetchHighRiskCustomers = async () => {
      try {
        setLoading(true)
        const { data } = await api.get('/customers/high-risk')

        const enriched = (data || []).map((customer) => ({
          ...customer,
          tenure: customer.tenure ?? 0,
          risk_reason: customer.churn === 1 ? 'High churn risk' : 'Elevated churn risk',
        }))

        setCustomers(enriched)
        setError('')
      } catch (err) {
        setError(err.response?.data?.detail || 'Unable to load high-risk customers.')
      } finally {
        setLoading(false)
      }
    }

    fetchHighRiskCustomers()
  }, [])

  const visibleCustomers = useMemo(() => {
    const sorted = [...customers].sort((a, b) => {
      const first = Number(a.tenure ?? 0)
      const second = Number(b.tenure ?? 0)
      return sortAsc ? first - second : second - first
    })

    return sorted.slice(0, limit)
  }, [customers, limit, sortAsc])

  if (loading) return <p className="status">Loading high-risk list...</p>
  if (error) return <p className="error">{error}</p>

  return (
    <div className="page-block">
      <h2>High-risk customers</h2>
      <p className="count-banner">{customers.length} high-risk customers identified</p>

      {visibleCustomers.length === 0 ? (
        <p className="status">No high-risk customers found</p>
      ) : (
        <div className="table-card">
          <table>
            <thead>
              <tr>
                <th>Customer ID</th>
                <th>Tenure</th>
                <th>Monthly charges</th>
                <th>Contract type</th>
                <th>Risk reason</th>
              </tr>
            </thead>
            <tbody>
              {visibleCustomers.map((customer) => (
                <tr key={customer.customer_id}>
                  <td>{customer.customer_id}</td>
                  <td>{customer.tenure !== undefined && customer.tenure !== null && customer.tenure !== '' ? customer.tenure : 'N/A'}</td>
                  <td>{Number(customer.monthly_charges ?? 0).toFixed(2)}</td>
                  <td>{customer.contract_type}</td>
                  <td>{customer.risk_reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="page-actions">
        <button type="button" onClick={() => setSortAsc((current) => !current)}>
          Sort tenure: {sortAsc ? 'ascending' : 'descending'}
        </button>
        <button type="button" onClick={() => setLimit((current) => current + 50)} disabled={limit >= customers.length}>
          Load more
        </button>
      </div>
    </div>
  )
}

export default HighRiskCustomers
