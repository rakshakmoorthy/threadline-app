const CONDITION_COLORS = {
  post_mastectomy: '#0D7377',
  ostomy: '#14BDAC',
  rheumatoid: '#0D7377',
  post_surgical: '#14BDAC',
}

export default function ConditionSelector({ conditions, selected, onToggle }) {
  return (
    <div style={{
      display: 'flex',
      flexWrap: 'wrap',
      gap: '12px',
      marginTop: '24px',
    }}>
      {conditions.map((condition) => {
        const isSelected = selected.includes(condition.id)
        return (
          <button
            key={condition.id}
            onClick={() => onToggle(condition.id)}
            style={{
              padding: '12px 20px',
              borderRadius: '8px',
              border: `2px solid ${CONDITION_COLORS[condition.id]}`,
              backgroundColor: isSelected ? CONDITION_COLORS[condition.id] : 'transparent',
              color: isSelected ? '#ffffff' : CONDITION_COLORS[condition.id],
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500',
              transition: 'all 0.2s ease',
            }}
          >
            {condition.label}
            <span style={{
              marginLeft: '8px',
              fontSize: '12px',
              opacity: 0.8,
            }}>
              ({condition.signal_count.toLocaleString()} signals)
            </span>
          </button>
        )
      })}
    </div>
  )
}