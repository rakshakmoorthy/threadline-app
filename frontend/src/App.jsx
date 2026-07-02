import { useState, useEffect } from 'react'
import { getConditions, getOpportunities } from './api/threadline'
import ConditionSelector from './components/ConditionSelector'
import OpportunityCard from './components/OpportunityCard'
import ProductBrief from './components/ProductBrief'

export default function App() {
  const [conditions, setConditions] = useState([])
  const [selectedConditions, setSelectedConditions] = useState([])
  const [opportunities, setOpportunities] = useState([])
  const [selectedOpportunity, setSelectedOpportunity] = useState(null)
  const [visitedIds, setVisitedIds] = useState(new Set())
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Load conditions on mount
  useEffect(() => {
    getConditions()
      .then(data => setConditions(data.conditions))
      .catch(() => setError('Could not connect to Threadline API. Make sure the backend is running.'))
  }, [])

  // Toggle condition selection
  const toggleCondition = (conditionId) => {
    setSelectedConditions(prev =>
      prev.includes(conditionId)
        ? prev.filter(c => c !== conditionId)
        : [...prev, conditionId]
    )
    // Clear results when selection changes
    setOpportunities([])
    setSelectedOpportunity(null)
  }

  // Load opportunities
  const loadOpportunities = async () => {
    if (selectedConditions.length === 0) return
    setLoading(true)
    setError(null)
    try {
      const data = await getOpportunities(selectedConditions)
      setOpportunities(data.opportunities)
    } catch (e) {
      setError('Failed to load opportunities. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // Open a brief
  const openBrief = (opportunity) => {
    setSelectedOpportunity(opportunity)
    setVisitedIds(prev => new Set([...prev, opportunity.id]))
  }

  return (
    <div style={{
      backgroundColor: '#0f0f1a',
      minHeight: '100vh',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      color: '#F0FAFA',
    }}>
      <div style={{ maxWidth: '900px', margin: '0 auto', padding: '40px 24px' }}>

        {/* Header */}
        <div style={{ marginBottom: '40px' }}>
          <h1 style={{
            fontSize: '32px',
            fontWeight: '700',
            color: '#14BDAC',
            margin: 0,
          }}>
            Threadline
          </h1>
          <p style={{
            color: '#94a3b8',
            fontSize: '16px',
            marginTop: '8px',
          }}>
            Turns consumer frustration into product briefs before a brand runs a focus group.
          </p>
        </div>

        {/* Show brief or main view */}
        {selectedOpportunity ? (
          <ProductBrief
            opportunity={selectedOpportunity}
            onBack={() => setSelectedOpportunity(null)}
          />
        ) : (
          <>
            {/* Condition selector */}
            <div>
              <h2 style={{ color: '#F0FAFA', fontSize: '18px', fontWeight: '600', margin: 0 }}>
                Select a condition
              </h2>
              <p style={{ color: '#94a3b8', fontSize: '14px', marginTop: '4px' }}>
                Choose one or more conditions to see ranked product opportunities.
              </p>

              {error && (
                <div style={{
                  backgroundColor: '#1a1a2e',
                  border: '1px solid #ef4444',
                  borderRadius: '8px',
                  padding: '12px 16px',
                  color: '#ef4444',
                  marginTop: '16px',
                  fontSize: '14px',
                }}>
                  {error}
                </div>
              )}

              <ConditionSelector
                conditions={conditions}
                selected={selectedConditions}
                onToggle={toggleCondition}
              />

              {selectedConditions.length > 0 && (
                <button
                  onClick={loadOpportunities}
                  disabled={loading}
                  style={{
                    marginTop: '20px',
                    backgroundColor: '#0D7377',
                    color: '#F0FAFA',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '12px 24px',
                    fontSize: '15px',
                    fontWeight: '600',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    opacity: loading ? 0.7 : 1,
                  }}
                >
                  {loading ? 'Loading...' : 'Show opportunities'}
                </button>
              )}
            </div>

            {/* Opportunities list */}
            {opportunities.length > 0 && (
              <div style={{ marginTop: '40px' }}>
                <h2 style={{ color: '#F0FAFA', fontSize: '18px', fontWeight: '600', marginBottom: '4px' }}>
                  {opportunities.length} product opportunities
                </h2>
                <p style={{ color: '#94a3b8', fontSize: '14px', marginTop: '0', marginBottom: '20px' }}>
                  Ranked by signal strength. Click any card to see the full product brief.
                </p>
                {opportunities.map(opp => (
                  <OpportunityCard
                    key={opp.id}
                    opportunity={opp}
                    onClick={openBrief}
                    visited={visitedIds.has(opp.id)}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}