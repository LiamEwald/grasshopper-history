// The history tree: one row per version, newest at the top.
// A row is a title, its level and when; who made it is the colour of its line and dot.
import { useRef } from 'react'
import type { Level, Version } from './data'
import { levelLabel, relativeTime } from './data'
import type { RowGraph } from './graph'

const ROW = 40
const LANE = 18
const R = 5

function Lines({ g, lanes, color, selected }: { g: RowGraph; lanes: number; color: string; selected: boolean }) {
  const x = (l: number) => 12 + l * LANE
  const mid = ROW / 2
  const me = x(g.lane)
  return (
    <svg width={x(lanes - 1) + 12} height={ROW} className="lines" aria-hidden>
      {g.through.map((e, i) => (
        <line key={'t' + i} x1={x(e.track)} y1={0} x2={x(e.track)} y2={ROW} stroke={e.color} />
      ))}
      {g.up.map((e, i) => (
        <path key={'u' + i} d={`M${x(e.track)},0 L${x(e.track)},${e.track === g.lane ? 0 : mid - 8} L${me},${mid}`} stroke={e.color} fill="none" />
      ))}
      {g.down.map((e, i) => (
        <path key={'d' + i} d={`M${me},${mid} L${x(e.track)},${e.track === g.lane ? mid : mid + 8} L${x(e.track)},${ROW}`} stroke={e.color} fill="none" />
      ))}
      {selected && <circle cx={me} cy={mid} r={R + 3.5} className="ring" />}
      <circle cx={me} cy={mid} r={R} fill={color} />
    </svg>
  )
}

export default function Tree(props: {
  versions: Version[]
  graph: RowGraph[]
  lanes: number
  colors: Map<string, string>
  selected: number[]
  levels: Set<Level>
  onSelect: (n: number, add: boolean) => void
}) {
  const { versions, graph, lanes, colors, selected, levels } = props
  const now = Date.now()
  // Press and hold adds a second version (phones have no Ctrl+click).
  const hold = useRef<{ timer?: number; fired: boolean }>({ fired: false })
  const press = (n: number) => {
    hold.current.fired = false
    hold.current.timer = window.setTimeout(() => {
      hold.current.fired = true
      props.onSelect(n, true)
    }, 500)
  }
  const release = () => window.clearTimeout(hold.current.timer)
  return (
    <div className="tree" role="listbox" aria-multiselectable>
      {versions.map((v, i) => {
        const on = selected.includes(v.n)
        const dim = levels.size > 0 && !v.levels.some((l) => levels.has(l))
        return (
          <div
            key={v.n}
            role="option"
            aria-selected={on}
            className={'row' + (on ? ' selected' : '') + (dim ? ' dim' : '')}
            onClick={(e) => {
              if (!hold.current.fired) props.onSelect(v.n, e.ctrlKey || e.metaKey || e.shiftKey)
              hold.current.fired = false
            }}
            onPointerDown={() => press(v.n)}
            onPointerUp={release}
            onPointerLeave={release}
            onPointerCancel={release}
            onContextMenu={(e) => e.preventDefault()}
          >
            <Lines g={graph[i]} lanes={lanes} color={colors.get(v.author) ?? '#8F99A8'} selected={on} />
            <span className="title">{v.title}</span>
            {v.level && <span className="level">{levelLabel(v.level)}</span>}
            <span className="when">{relativeTime(v.time, now)}</span>
          </div>
        )
      })}
    </div>
  )
}
