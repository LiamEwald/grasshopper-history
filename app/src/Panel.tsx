// The side panel: everything about the selected version lives here and only here.
import { useCallback, useEffect, useRef, useState } from 'react'
import { AnchorButton, Button, Callout, HTMLTable, Tooltip } from '@blueprintjs/core'
import Code from './Code'
import type { Version } from './data'
import { NUMBERS_NOTE, exactTime, fmt, levelLabel, measurementRows, pictureUrl } from './data'

function delta(d: number, digits: number) {
  const changed = Math.abs(d) >= Math.pow(10, -digits) / 2
  return (
    <td className={'num' + (changed ? ' changed' : ' muted')}>
      {changed ? (d > 0 ? '+' : '−') + fmt(Math.abs(d), digits) : 'same'}
    </td>
  )
}

function Numbers({ v, parent }: { v: Version; parent?: Version }) {
  if (!v.numbers) return <p className="muted">No measurements: the model did not build.</p>
  return (
    <HTMLTable compact className="numbers">
      <tbody>
        {measurementRows(v, parent).map((m) => (
          <tr key={m.key}>
            <td>{m.label}</td>
            <td className="num">
              {fmt(m.get(v.numbers!), m.digits)} <span className="muted">{m.unit}</span>
            </td>
            {parent?.numbers ? delta(m.get(v.numbers!) - m.get(parent.numbers), m.digits) : <td />}
          </tr>
        ))}
      </tbody>
    </HTMLTable>
  )
}

function Compare({ a, b }: { a: Version; b: Version }) {
  return (
    <HTMLTable compact className="numbers">
      <thead>
        <tr>
          <th />
          <th className="num">#{a.n}</th>
          <th className="num">#{b.n}</th>
          <th className="num">Difference</th>
        </tr>
      </thead>
      <tbody>
        {measurementRows(a, b).map((m) => {
          const x = a.numbers ? m.get(a.numbers) : 0
          const y = b.numbers ? m.get(b.numbers) : 0
          return (
            <tr key={m.key}>
              <td>
                {m.label} <span className="muted">{m.unit}</span>
              </td>
              <td className="num">{fmt(x, m.digits)}</td>
              <td className="num">{fmt(y, m.digits)}</td>
              {delta(y - x, m.digits)}
            </tr>
          )
        })}
      </tbody>
    </HTMLTable>
  )
}

// Changed elements against the parent, by category: what an engineer checks first.
function Changes({ v }: { v: Version }) {
  const groups = v.changedBy ?? []
  if (!v.parents.length) return null
  if (!groups.length) return <p className="muted small">No element changed.</p>
  const words = (g: (typeof groups)[number]) =>
    [
      g.added.length && `${g.added.length} added`,
      g.changed.length && `${g.changed.length} changed`,
      g.removed.length && `${g.removed.length} removed`,
    ]
      .filter(Boolean)
      .join(', ')
  return (
    <HTMLTable compact className="numbers changes">
      <tbody>
        {groups.map((g) => (
          <tr key={g.category}>
            <td>
              <details>
                <summary>{g.category[0].toUpperCase() + g.category.slice(1)}</summary>
                <div className="names">
                  {[...g.added, ...g.changed, ...g.removed].slice(0, 60).join(', ')}
                  {g.added.length + g.changed.length + g.removed.length > 60 ? ', …' : ''}
                </div>
              </details>
            </td>
            <td className="num changed">{words(g)}</td>
          </tr>
        ))}
      </tbody>
    </HTMLTable>
  )
}

// Full-screen viewer for a version's pictures: arrow keys or swipe between them, Esc, the close
// button or a click outside closes it.
function Viewer(props: { v: Version; pics: { file: string; label: string }[]; at: number; onClose: () => void }) {
  const { v, pics, onClose } = props
  const [i, setI] = useState(props.at)
  const touch = useRef<number | null>(null)
  const step = useCallback((d: number) => setI((k) => (k + d + pics.length) % pics.length), [pics.length])
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
      else if (e.key === 'ArrowRight') step(1)
      else if (e.key === 'ArrowLeft') step(-1)
      else return
      e.preventDefault()
      e.stopPropagation()
    }
    window.addEventListener('keydown', onKey, true)
    return () => window.removeEventListener('keydown', onKey, true)
  }, [onClose, step])
  const p = pics[i]
  return (
    <div
      className="viewer"
      role="dialog"
      aria-label={`${p.label}: ${v.title}`}
      onClick={onClose}
      onTouchStart={(e) => (touch.current = e.touches[0].clientX)}
      onTouchEnd={(e) => {
        if (touch.current === null) return
        const dx = e.changedTouches[0].clientX - touch.current
        touch.current = null
        if (Math.abs(dx) > 40) step(dx < 0 ? 1 : -1)
      }}
    >
      <Button className="viewer-close" variant="minimal" icon="cross" aria-label="Close" onClick={onClose} />
      <img src={pictureUrl(v, p.file)} alt={`${p.label}: ${v.title}`} onClick={(e) => e.stopPropagation()} />
      <div className="viewer-caption" onClick={(e) => e.stopPropagation()}>
        #{v.n} {v.title} · {p.label}
        {pics.length > 1 && (
          <span className="viewer-nav">
            <Button variant="minimal" icon="chevron-left" aria-label="Previous picture" onClick={() => step(-1)} />
            {i + 1} / {pics.length}
            <Button variant="minimal" icon="chevron-right" aria-label="Next picture" onClick={() => step(1)} />
          </span>
        )}
      </div>
    </div>
  )
}

function Pictures({ v }: { v: Version }) {
  const [open, setOpen] = useState<number | null>(null)
  const pics = [
    v.picture && { file: v.picture, label: 'Exterior' },
    v.inside && { file: v.inside, label: 'Inside view: envelope and roof hidden' },
  ].filter(Boolean) as { file: string; label: string }[]
  if (!pics.length) return <p className="muted">No picture: the model did not build.</p>
  return (
    <div className="pictures">
      {pics.map((p, k) => (
        <figure key={p.file}>
          <button type="button" className="picture-button" onClick={() => setOpen(k)} aria-label={`Open ${p.label} full screen`}>
            <img src={pictureUrl(v, p.file)} alt={`${p.label}: ${v.title}`} />
          </button>
          {pics.length > 1 && <figcaption>{p.label}</figcaption>}
        </figure>
      ))}
      {open !== null && <Viewer v={v} pics={pics} at={open} onClose={() => setOpen(null)} />}
    </div>
  )
}

export default function Panel(props: {
  versions: Version[]
  selected: Version[]
  colors: Map<string, string>
  repo: string | null
  readonly: boolean
  combine: { state: string; versions?: number[] }
  onRestore: (v: Version) => void
  onCombine: (a: Version, b: Version) => void
  onMinimise: () => void
  mobile: boolean
}) {
  const { selected, colors, repo, readonly, combine } = props
  const v = selected[selected.length - 1]
  if (!v) return null
  const other = selected.length > 1 ? selected[0] : undefined
  const parent = props.versions.find((x) => x.n === v.parents[0])
  const [a, b] = other ? [other, v].sort((x, y) => x.n - y.n) : [v, v]
  const sent = !!other && !!combine.versions?.includes(a.n) && !!combine.versions?.includes(b.n)
  return (
    <aside className={'panel' + (props.mobile ? ' sheet' : '')}>
      <header>
        <div>
          <div className="muted small">
            #{v.n}
            {v.level && ` · ${levelLabel(v.level)}`}
          </div>
          <h2>{v.title}</h2>
        </div>
        {props.mobile && <Button variant="minimal" icon="arrow-left" text="Back" onClick={props.onMinimise} />}
      </header>
      <Pictures v={v} />
      <p className="summary">{v.summary}</p>
      {!other && v.parents.length > 0 && (
        <>
          <h3>Changed elements</h3>
          <Changes v={v} />
        </>
      )}
      <h3>{other ? `Measurements, #${a.n} and #${b.n}` : 'Measurements'}</h3>
      {other ? <Compare a={a} b={b} /> : <Numbers v={v} parent={parent} />}
      <p className="muted small">
        {!other && parent ? `Change from parent #${parent.n}. ` : ''}
        {NUMBERS_NOTE}
      </p>
      <Code before={other ? a : parent} after={other ? b : v} />
      <dl className="facts">
        <dt>Author</dt>
        <dd>
          <span className="dot" style={{ background: colors.get(v.author) }} />
          {v.author}
        </dd>
        <dt>Date</dt>
        <dd>{exactTime(v.time)}</dd>
        {v.parents.length > 0 && (
          <>
            <dt>{v.parents.length > 1 ? 'Parents' : 'Parent'}</dt>
            <dd>{v.parents.map((p) => '#' + p).join(', ')}</dd>
          </>
        )}
        <dt>Commit</dt>
        <dd>
          {v.commit && repo ? (
            <a href={`${repo}/commit/${v.commit}`} target="_blank" rel="noreferrer">
              {v.commit.slice(0, 7)} on GitHub
            </a>
          ) : (
            (v.commit?.slice(0, 7) ?? '—')
          )}
        </dd>
      </dl>
      <div className="actions">
        <Tooltip content="This is a read-only copy" disabled={!readonly}>
          {other ? (
            <AnchorButton intent="primary" icon="git-merge" disabled={readonly} onClick={() => props.onCombine(a, b)}>
              Combine #{a.n} and #{b.n}
            </AnchorButton>
          ) : (
            <AnchorButton intent="primary" icon="history" disabled={readonly} onClick={() => props.onRestore(v)}>
              Restore #{v.n}
            </AnchorButton>
          )}
        </Tooltip>
        {sent && (
          <Callout icon="chat" className="sent">
            {combine.state === 'sent'
              ? 'Claude has received both versions and will discuss them with you in Claude Code before building.'
              : 'Ready for Claude: your next message in Claude Code passes both versions to it.'}
          </Callout>
        )}
        {!other && (
          <p className="muted small">
            {props.mobile ? 'Press and hold' : 'Ctrl+click'} a second version to compare or combine.
          </p>
        )}
      </div>
    </aside>
  )
}
