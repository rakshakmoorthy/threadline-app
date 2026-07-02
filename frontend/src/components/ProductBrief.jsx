export default function ProductBrief({ opportunity, onBack }) {
  const { title, score, confidence, conditions, overlap, brief } = opportunity

  const confidenceColor = {
    high: '#14BDAC',
    medium: '#f59e0b',
    low: '#6b7280',
  }

  const Section = ({ title, children }) => (
    <div style={{ marginBottom: '24px' }}>
      <h3 style={{
        color: '#14BDAC',
        fontSize: '13px',
        fontWeight: '600',
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        marginBottom: '12px',
      }}>
        {title}
      </h3>
      {children}
    </div>
  )

  const Tag = ({ text, color = '#0D7377' }) => (
    <span style={{
      backgroundColor: '#1a1a2e',
      border: `1px solid ${color}`,
      color: color,
      fontSize: '12px',
      padding: '4px 10px',
      borderRadius: '4px',
      marginRight: '8px',
      marginBottom: '8px',
      display: 'inline-block',
    }}>
      {text}
    </span>
  )

  return (
    <div style={{ color: '#F0FAFA' }}>
      {/* Back button */}
      <button
        onClick={onBack}
        style={{
          backgroundColor: 'transparent',
          border: '1px solid #0D7377',
          color: '#14BDAC',
          padding: '8px 16px',
          borderRadius: '6px',
          cursor: 'pointer',
          fontSize: '14px',
          marginBottom: '24px',
        }}
      >
        ← Back to opportunities
      </button>

      {/* Header */}
      <div style={{
        backgroundColor: '#16213e',
        border: '1px solid #0D7377',
        borderRadius: '12px',
        padding: '24px',
        marginBottom: '24px',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <h1 style={{ color: '#F0FAFA', margin: 0, fontSize: '22px', fontWeight: '700', flex: 1 }}>
            {title}
          </h1>
          <div style={{
            backgroundColor: '#0D7377',
            color: '#F0FAFA',
            borderRadius: '8px',
            padding: '8px 16px',
            fontSize: '24px',
            fontWeight: '700',
            marginLeft: '16px',
          }}>
            {score}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px', marginTop: '16px', flexWrap: 'wrap' }}>
          {conditions.map(c => (
            <Tag key={c} text={c.replace(/_/g, ' ')} color='#14BDAC' />
          ))}
          <Tag
            text={`${confidence} confidence`}
            color={confidenceColor[confidence]}
          />
          {overlap && <Tag text='⚡ cross-condition overlap' color='#0D7377' />}
        </div>
      </div>

      {/* Brief sections */}
      <div style={{
        backgroundColor: '#16213e',
        border: '1px solid #0D7377',
        borderRadius: '12px',
        padding: '24px',
      }}>
        <Section title="Confirmed Pain Points">
          <ul style={{ margin: 0, paddingLeft: '20px' }}>
            {(brief.confirmed_pain_points || []).map((p, i) => (
              <li key={i} style={{ color: '#94a3b8', marginBottom: '6px', fontSize: '14px' }}>{p}</li>
            ))}
          </ul>
        </Section>

        <Section title="Priority Features — Build These First">
          <div>
            {(brief.priority_features || []).map((f, i) => (
              <Tag key={i} text={`${i + 1}. ${f}`} color='#14BDAC' />
            ))}
          </div>
        </Section>

        <Section title="Recommended Features">
          <div>
            {(brief.recommended_features || []).map((f, i) => (
              <Tag key={i} text={f} />
            ))}
          </div>
        </Section>

        <Section title="Gaps — What We Don't Know Yet">
          <ul style={{ margin: 0, paddingLeft: '20px' }}>
            {(brief.gaps || []).map((g, i) => (
              <li key={i} style={{ color: '#94a3b8', marginBottom: '6px', fontSize: '14px' }}>{g}</li>
            ))}
          </ul>
        </Section>

        {brief.evidence && brief.evidence.length > 0 && (
          <Section title="Source Evidence">
            {brief.evidence.map((e, i) => (
              <div key={i} style={{
                backgroundColor: '#1a1a2e',
                border: '1px solid #0D7377',
                borderRadius: '8px',
                padding: '12px',
                marginBottom: '8px',
              }}>
                <span style={{
                  color: '#14BDAC',
                  fontSize: '11px',
                  fontWeight: '600',
                  textTransform: 'uppercase',
                }}>
                  {e.source}
                </span>
                <p style={{ color: '#94a3b8', margin: '4px 0 0 0', fontSize: '13px' }}>
                  "{e.excerpt}"
                </p>
              </div>
            ))}
          </Section>
        )}
      </div>
    </div>
  )
}