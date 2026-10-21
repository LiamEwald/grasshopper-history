// Branch lines for the tree, rows newest first. A line is coloured by the author of
// the version it leads to; there are no other colours and no arrows.
import type { Version } from './data'

export interface Edge {
  track: number // lane the line runs in
  color: string
}

export interface RowGraph {
  lane: number
  through: Edge[] // lines passing this row
  up: Edge[] // lines ending at this row's dot from above
  down: Edge[] // lines leaving this row's dot downwards
}

export function layout(rows: Version[], colors: Map<string, string>): { rows: RowGraph[]; lanes: number } {
  const index = new Map(rows.map((v, i) => [v.n, i]))
  // The line of work that goes on longest stays straight: of a version's children, the one
  // with the most versions after it continues its lane; trials and side options step aside.
  const after = new Map<number, number>()
  rows.forEach((v) => {
    // newest first, so every child is counted before its parents
    v.parents.forEach((p) => after.set(p, Math.max(after.get(p) ?? 0, (after.get(v.n) ?? 0) + 1)))
  })
  const heir = new Map<number, number>()
  ;[...rows].reverse().forEach((v) => {
    const p = v.parents[0]
    if (p === undefined) return
    const h = heir.get(p)
    if (h === undefined || (after.get(v.n) ?? 0) > (after.get(h) ?? 0)) heir.set(p, v.n)
  })
  // Oldest first: the heir takes its parent's lane; any other child opens the lowest lane
  // that is free from the parent onwards.
  const lane = new Map<number, number>()
  const laneEnd: number[] = []
  const waiting = new Set<number>() // lanes kept for an heir that comes later
  const pos = new Map<number, number>()
  ;[...rows].reverse().forEach((v, t) => {
    pos.set(v.n, t)
    const p = v.parents[0]
    let l: number
    if (p !== undefined && lane.has(p) && heir.get(p) === v.n) {
      l = lane.get(p)!
    } else {
      const from = p !== undefined && pos.has(p) ? pos.get(p)! : t
      l = laneEnd.findIndex((end, i) => i > 0 && end < from && !waiting.has(i))
      if (l < 0) l = laneEnd.length
    }
    lane.set(v.n, l)
    laneEnd[l] = t
    if (heir.has(v.n)) waiting.add(l)
    else waiting.delete(l)
  })
  const out: RowGraph[] = rows.map((v) => ({ lane: lane.get(v.n)!, through: [], up: [], down: [] }))
  rows.forEach((v, i) => {
    const color = colors.get(v.author) ?? '#8F99A8'
    v.parents.forEach((p, k) => {
      const j = index.get(p)
      if (j === undefined) return
      const track = k === 0 ? lane.get(v.n)! : lane.get(p)!
      out[i].down.push({ track, color })
      for (let r = i + 1; r < j; r++) out[r].through.push({ track, color })
      out[j].up.push({ track, color })
    })
  })
  return { rows: out, lanes: Math.max(laneEnd.length, 1) }
}
