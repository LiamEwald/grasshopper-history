import { Alert, Button, NonIdealState, OverlayToaster, Spinner } from '@blueprintjs/core'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import Panel from './Panel'
import Tree from './Tree'
import type { History, Level, Version } from './data'
import { LEVELS, READONLY, authorColors, loadHistory } from './data'
import { layout } from './graph'

// Phone-width screens: the tree fills the screen and details open as a full-screen sheet.
function useNarrow() {
  const query = '(max-width: 760px)'
  const [narrow, setNarrow] = useState(() => window.matchMedia(query).matches)
  useEffect(() => {
    const m = window.matchMedia(query)
    const on = () => setNarrow(m.matches)
    m.addEventListener('change', on)
    return () => m.removeEventListener('change', on)
  }, [])
  return narrow
}

export default function App() {
  const [history, setHistory] = useState<History | null>(null)
  const [selected, setSelected] = useState<number[]>([])
  const [levels, setLevels] = useState<Set<Level>>(new Set())
  const mobile = useNarrow()
  const [open, setOpen] = useState(() => !window.matchMedia('(max-width: 760px)').matches)
  const [restoring, setRestoring] = useState<Version | null>(null)
  const [busy, setBusy] = useState(false)
  const [combine, setCombine] = useState<{ state: string; versions?: number[] }>({ state: 'none' })
  const toaster = useRef<OverlayToaster | null>(null)

  const refresh = useCallback(async () => {
    const h = await loadHistory()
    setHistory((old) => (old && JSON.stringify(old) === JSON.stringify(h) ? old : h))
    if (!READONLY) setCombine(await (await fetch('/api/combine')).json())
    return h
  }, [])

  useEffect(() => {
    refresh().then((h) => setSelected((s) => (s.length || !h.versions.length ? s : [h.versions[0].n])))
    if (READONLY) return
    const t = setInterval(refresh, 3000) // new versions appear while you chat with Claude
    return () => clearInterval(t)
  }, [refresh])

  const versions = useMemo(() => history?.versions ?? [], [history])
  const colors = useMemo(() => authorColors(versions), [versions])
  const graph = useMemo(() => layout(versions, colors), [versions, colors])

  const select = (n: number, add: boolean) => {
    if (mobile) setOpen(true)
    setSelected((s) => {
      if (!add) return [n]
      if (s.includes(n)) return s.filter((x) => x !== n)
      return [...s.slice(-1), n] // at most two
    })
  }

  // Up and down walk the tree.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown') return
      const i = versions.findIndex((v) => v.n === selected[selected.length - 1])
      const j = Math.min(versions.length - 1, Math.max(0, i + (e.key === 'ArrowDown' ? 1 : -1)))
      if (versions[j]) setSelected([versions[j].n])
      e.preventDefault()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [versions, selected])

  const doRestore = async () => {
    const v = restoring!
    setRestoring(null)
    setBusy(true)
    try {
      const r = await fetch('/api/restore', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ n: v.n }) })
      if (!r.ok) throw new Error((await r.json()).error)
      const h = await refresh()
      setSelected([h.versions[0].n])
    } catch (e) {
      toaster.current?.show({ message: `Restore didn't work: ${String(e).slice(0, 200)}` })
    } finally {
      setBusy(false)
    }
  }

  const doCombine = async (a: Version, b: Version) => {
    await fetch('/api/combine', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ versions: [a.n, b.n] }) })
    refresh()
  }

  if (!history) return <NonIdealState icon={<Spinner />} />
  const authors = [...colors.entries()]
  const picked = selected.map((n) => versions.find((v) => v.n === n)).filter(Boolean) as Version[]

  return (
    <div className="app">
      <header className="bar">
        <div className="bar-left">
          <h1>Grasshopper History</h1>
          <div className="chips" role="group" aria-label="Highlight levels">
            {LEVELS.map((l) => (
              <button
                key={l.key}
                type="button"
                className={'level' + (levels.has(l.key) ? ' on' : '')}
                aria-pressed={levels.has(l.key)}
                onClick={() =>
                  setLevels((s) => {
                    const t = new Set(s)
                    if (t.has(l.key)) t.delete(l.key)
                    else t.add(l.key)
                    return t
                  })
                }
              >
                {l.label}
              </button>
            ))}
          </div>
        </div>
        <div className="bar-right">
          <div className="legend" aria-label="Authors">
            {authors.map(([name, c]) => (
              <span key={name}>
                <span className="dot" style={{ background: c }} />
                {name}
              </span>
            ))}
          </div>
          {!mobile && (
            // One toggle in one place: it stays put whether the details are shown or hidden.
            <Button
              variant="minimal"
              icon={open ? 'chevron-right' : 'chevron-left'}
              text={open ? 'Hide details' : 'Show details'}
              className="details-toggle"
              onClick={() => setOpen(!open)}
            />
          )}
        </div>
      </header>
      <main>
        {versions.length ? (
          <Tree
            versions={versions}
            graph={graph.rows}
            lanes={graph.lanes}
            colors={colors}
            selected={selected}
            levels={levels}
            onSelect={select}
          />
        ) : (
          <NonIdealState icon="git-commit" title="No versions yet" description="Ask Claude for a design change; each saved change appears here as a version." />
        )}
        {open && picked.length > 0 && (
          <Panel
            versions={versions}
            selected={picked}
            colors={colors}
            repo={history.repo}
            readonly={history.readonly}
            combine={combine}
            onRestore={setRestoring}
            onCombine={doCombine}
            onMinimise={() => setOpen(false)}
            mobile={mobile}
          />
        )}
      </main>
      <Alert
        isOpen={!!restoring}
        cancelButtonText="Cancel"
        confirmButtonText={restoring ? `Restore #${restoring.n}` : ''}
        intent="primary"
        icon="history"
        onCancel={() => setRestoring(null)}
        onConfirm={doRestore}
      >
        {restoring && (
          <p>
            Rhino will rebuild the model from the scripts of #{restoring.n} ({restoring.title}). The result is saved as a
            new version with #{restoring.n} as its parent; no version is deleted.
          </p>
        )}
      </Alert>
      {busy && (
        <div className="busy">
          <Spinner size={20} /> Rebuilding in Rhino…
        </div>
      )}
      <OverlayToaster ref={toaster} />
    </div>
  )
}
