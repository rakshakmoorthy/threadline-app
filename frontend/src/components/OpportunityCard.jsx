export default function OpportunityCard({ opportunity, onClick, visited }) {
  const confidenceColor = {
    high: '#14BDAC',
    medium: '#f59e0b',
    low: '#6b7280',
  }

  return (
    <div
      onClick={() => onClick(opportunity)}
      style={{
        backgroundColor: visited ? '#1a1a2e' : '#16213e',
        border: '1px solid #0D7377',
        borderRadius: '12px',
        padding: '20px',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        opacity: visited ? 0.75 : 1,
        marginBottom: '12px',
      }}
      onMouseEnter={e => e.currentTarget.style.borderColor = '#14BDAC'}
      onMouseLeave={e => e.currentTarget.style.borderColor = '#0D7377'}
    >
      {/* Header row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <h3 style={{ color: '#F0FAFA', margin: 0, fontSize: '16px', fontWeight: '600', flex: 1 }}>
          {opportunity.title}
        </h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: '16px' }}>
          {opportunity.overlap && (
            <span style={{
              backgroundColor: '#0D7377',
              color: '#F0FAFA',
              fontSize: '11px',
              padding: '2px 8px',
              borderRadius: '4px',
              fontWeight: '600',
            }}>
              ⚡ OVERLAP
            </span>
          )}
          <div style={{
            backgroundColor: '#0D7377',
            color: '#F0FAFA',
            borderRadius: '8px',
            padding: '4px 12px',
            fontSize: '18px',
            fontWeight: '700',
            minWidth: '48px',
            textAlign: 'center',
          }}>
            {opportunity.score}
          </div>
        </div>
      </div>

      {/* Pain point summary */}
      <p style={{ color: '#94a3b8', margin: '8px 0 0 0', fontSize: '14px' }}>
        {opportunity.pain_point_summary}
      </p>

      {/* Conditions + confidence */}
      <div style={{ display: 'flex', gap: '8px', marginTop: '12px', flexWrap: 'wrap' }}>
        {opportunity.conditions.map(c => (
          <span key={c} style={{
            backgroundColor: '#1a1a2e',
            border: '1px solid #0D7377',
            color: '#14BDAC',
            fontSize: '11px',
            padding: '2px 8px',
            borderRadius: '4px',
          }}>
            {c.replace(/_/g, ' ')}
          </span>
        ))}
        <span style={{
          color: confidenceColor[opportunity.confidence],
          fontSize: '11px',
          padding: '2px 8px',
          borderRadius: '4px',
          border: `1px solid ${confidenceColor[opportunity.confidence]}`,
        }}>
          {opportunity.confidence} confidence
        </span>
      </div>
    </div>
  )
}