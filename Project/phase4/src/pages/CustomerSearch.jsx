import { useState } from 'react'
import { api } from '../api'

function CustomerSearch() {
  const [customerId, setCustomerId] = useState('')
  const [customer, setCustomer] = useState(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  const handleSearch = async () => {
    const trimmedId = customerId.trim()

    if (!trimmedId) {
      setCustomer(null)
      setMessage('Please enter a customer ID.')
      return
    }

    try {
      setLoading(true)
      setMessage('')

      const [profileRes, featureRes] = await Promise.all([
        api.get(`/customers/${trimmedId}/profile`),
        api.get(`/features/${trimmedId}`),
      ])

      const mergedCustomer = {
        ...profileRes.data,
        ...featureRes.data,
        customer_id: trimmedId,
      }

      setCustomer(mergedCustomer)
    } catch (error) {
      setCustomer(null)
      if (error.response?.status === 404) {
        setMessage('Customer not found')
      } else {
        setMessage(error.response?.data?.detail || 'Unable to load customer profile.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-block">
      <h2>Customer search</h2>

      <div className="search-box">
        <input
          type="text"
          value={customerId}
          onChange={(event) => setCustomerId(event.target.value)}
          placeholder="Enter customer ID"
        />
        <button type="button" onClick={handleSearch} disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {message && <p className="status">{message}</p>}

      {customer && (
        <div className="profile-card">
          <div className={`status-pill ${customer.churn === 1 ? 'danger' : 'success'}`}>
            {customer.churn === 1 ? 'Churned' : 'Active'}
          </div>

          <div className="profile-grid">
            <div><span>Customer ID</span><strong>{customer.customer_id}</strong></div>
            <div><span>Tenure</span><strong>{customer.tenure ?? '—'} months</strong></div>
            <div><span>Contract</span><strong>{customer.contract_type}</strong></div>
            {/* <div><span>Internet</span><strong>{customer.internet_service}</strong></div> */}
            <div><span>Monthly charges</span><strong>{Number(customer.monthly_charges ?? 0).toFixed(2)}</strong></div>
            <div><span>Churn</span><strong>{customer.churn === 1 ? 'Yes' : 'No'}</strong></div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CustomerSearch
