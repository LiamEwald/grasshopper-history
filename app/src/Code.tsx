// Code diff between two versions, one block per changed script, GitHub style:
// removed lines on red, added lines on green, old and new line numbers.
import { Button, Collapse } from '@blueprintjs/core'
import { structuredPatch } from 'diff'
import { useEffect, useState } from 'react'
import type { Version } from './data'
import { loadScripts } from './data'

type Files = Record<string, string>

interface FileDiff {
  name: string
  added: number
  removed: number
  hunks: ReturnType<typeof structuredPatch>['hunks']
}

function diffFiles(before: Files, after: Files): { changed: FileDiff[]; unchanged: number } {
  const names = [...new Set([...Object.keys(before), ...Object.keys(after)])].sort()
  const changed: FileDiff[] = []
  let unchanged = 0
  for (const name of names) {
    const a = before[name] ?? ''
    const b = after[name] ?? ''
    if (a === b) {
      unchanged++
      continue
    }
    const { hunks } = structuredPatch(name, name, a, b, '', '', { context: 2 })
    let added = 0
    let removed = 0
    for (const h of hunks)
      for (const l of h.lines) {
        if (l[0] === '+') added++
        if (l[0] === '-') removed++
      }
    changed.push({ name, added, removed, hunks })
  }
  return { changed, unchanged }
}

function Hunks({ f }: { f: FileDiff }) {
  return (
    <table className="diff">
      <colgroup>
        <col className="ln-col" />
        <col className="ln-col" />
        <col />
      </colgroup>
      <tbody>
        {f.hunks.map((h, i) => {
          let o = h.oldStart
          let n = h.newStart
          return [
            <tr key={'h' + i} className="hunk">
              <td colSpan={3}>
                lines {h.newStart}–{h.newStart + Math.max(h.newLines - 1, 0)}
              </td>
            </tr>,
            ...h.lines
              .filter((l) => l[0] !== '\\')
              .map((l, j) => {
                const kind = l[0] === '+' ? 'add' : l[0] === '-' ? 'del' : 'ctx'
                const left = kind === 'add' ? '' : o++
                const right = kind === 'del' ? '' : n++
                return (
                  <tr key={i + '-' + j} className={kind}>
                    <td className="ln">{left}</td>
                    <td className="ln">{right}</td>
                    <td className="code">{l.slice(1) || ' '}</td>
                  </tr>
                )
              }),
          ]
        })}
      </tbody>
    </table>
  )
}

export default function Code({ before, after }: { before?: Version; after: Version }) {
  const [open, setOpen] = useState(false)
  const [result, setResult] = useState<{ changed: FileDiff[]; unchanged: number } | null>(null)

  useEffect(() => {
    if (!open) return
    let live = true
    setResult(null)
    Promise.all([before ? loadScripts(before.n) : Promise.resolve({}), loadScripts(after.n)]).then(([a, b]) => {
      if (live) setResult(diffFiles(a, b))
    })
    return () => {
      live = false
    }
  }, [open, before, after])

  const label = before ? `Code, #${before.n} → #${after.n}` : `Code, #${after.n}`
  return (
    <section className="code-section">
      <Button variant="minimal" alignText="start" fill icon={open ? 'chevron-down' : 'chevron-right'} onClick={() => setOpen(!open)}>
        {label}
      </Button>
      <Collapse isOpen={open}>
        {!result ? (
          <p className="muted small">Loading…</p>
        ) : (
          <>
            {result.changed.map((f) => (
              <div key={f.name} className="file">
                <div className="file-head">
                  <span>scripts/{f.name}</span>
                  <span className="muted">
                    +{f.added} −{f.removed}
                  </span>
                </div>
                <Hunks f={f} />
              </div>
            ))}
            {!result.changed.length && <p className="muted small">No script changed.</p>}
            {result.unchanged > 0 && (
              <p className="muted small">
                {result.unchanged} {result.unchanged === 1 ? 'script' : 'scripts'} unchanged.
              </p>
            )}
          </>
        )}
      </Collapse>
    </section>
  )
}
