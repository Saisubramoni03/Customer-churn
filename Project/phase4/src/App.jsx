import { useState } from 'react'
import './App.css'
import CustomerSearch from './pages/CustomerSearch'
import ChurnSummary from './pages/ChurnSummary'
import HighRiskCustomers from './pages/HighRiskCustomers'
import ChurnPrediction from './pages/ChurnPrediction'

const tabs = [
  { key: 'summary', label: 'Summary' },
  { key: 'customer', label: 'Customer Search' },
  { key: 'high-risk', label: 'High Risk' },
  { key: 'prediction', label: 'Prediction' },
]

function App() {
  const [activeTab, setActiveTab] = useState('summary')

  const renderPage = () => {
    switch (activeTab) {
      case 'customer':
        return <CustomerSearch />
      case 'high-risk':
        return <HighRiskCustomers />
      case 'prediction':
        return <ChurnPrediction />
      case 'summary':
      default:
        return <ChurnSummary />
    }
  }

  return (
    <div className="dashboard-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Customer retention</p>
          <h1>Retention dashboard</h1>
        </div>
      </header>

      <nav className="tab-nav" aria-label="Dashboard sections">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            className={activeTab === tab.key ? 'tab active' : 'tab'}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <main className="page-content">{renderPage()}</main>
    </div>
  )
}

export default App
