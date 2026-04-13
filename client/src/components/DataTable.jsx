import React, { useState, useRef } from 'react'
import { ChevronUp, ChevronDown, GripVertical } from 'lucide-react'

export default function DataTable({ columns, data, onRowClick, loading, emptyMessage = 'No data' }) {
  const [colOrder, setColOrder] = useState(columns.map(c => c.key))
  const [sortKey, setSortKey] = useState(null)
  const [sortDir, setSortDir] = useState('asc')
  const dragItem = useRef(null)
  const dragOverItem = useRef(null)

  function handleDragStart(e, key) {
    dragItem.current = key
    e.dataTransfer.effectAllowed = 'move'
  }

  function handleDragEnter(e, key) {
    e.preventDefault()
    dragOverItem.current = key
  }

  function handleDragOver(e) {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  function handleDrop(e) {
    e.preventDefault()
    if (!dragItem.current || dragItem.current === dragOverItem.current) return
    const from = colOrder.indexOf(dragItem.current)
    const to = colOrder.indexOf(dragOverItem.current)
    if (from < 0 || to < 0) return
    const newOrder = [...colOrder]
    newOrder.splice(from, 1)
    newOrder.splice(to, 0, dragItem.current)
    setColOrder(newOrder)
    dragItem.current = null
    dragOverItem.current = null
  }

  function handleDragEnd() {
    dragItem.current = null
    dragOverItem.current = null
  }

  function handleSort(key) {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  const visibleCols = colOrder.map(key => columns.find(c => c.key === key)).filter(Boolean)

  let sortedData = data
  if (sortKey) {
    sortedData = [...data].sort((a, b) => {
      const av = a[sortKey] ?? ''
      const bv = b[sortKey] ?? ''
      const cmp = av < bv ? -1 : av > bv ? 1 : 0
      return sortDir === 'asc' ? cmp : -cmp
    })
  }

  return (
    <div className="table-scroll">
      <table className="data-table">
        <thead>
          <tr>
            {visibleCols.map(col => (
              <th
                key={col.key}
                draggable
                onDragStart={e => handleDragStart(e, col.key)}
                onDragEnter={e => handleDragEnter(e, col.key)}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                onDragEnd={handleDragEnd}
                style={{ cursor: 'grab', userSelect: 'none', whiteSpace: 'nowrap', ...(col.width ? { width: col.width } : {}) }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <GripVertical size={12} style={{ color: 'var(--text3)', flexShrink: 0, opacity: 0.6 }} />
                  <span
                    style={{ cursor: col.sortable !== false ? 'pointer' : 'default' }}
                    onClick={col.sortable !== false ? () => handleSort(col.key) : undefined}
                  >
                    {col.label}
                  </span>
                  {col.sortable !== false && sortKey === col.key && (
                    sortDir === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            Array.from({ length: 8 }).map((_, i) => (
              <tr key={i}>
                {visibleCols.map(col => (
                  <td key={col.key}><div className="skeleton" style={{ height: 14, width: '80%' }} /></td>
                ))}
              </tr>
            ))
          ) : sortedData.length === 0 ? (
            <tr><td colSpan={visibleCols.length}><div className="empty-state"><div className="empty-state-title">{emptyMessage}</div></div></td></tr>
          ) : (
            sortedData.map((row, i) => (
              <tr
                key={row.id || i}
                className={onRowClick ? 'clickable' : ''}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
              >
                {visibleCols.map(col => (
                  <td key={col.key} style={col.style || {}}>
                    {col.render ? col.render(row[col.key], row) : (row[col.key] ?? '—')}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
