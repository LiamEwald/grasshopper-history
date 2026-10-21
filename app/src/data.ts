// Versions as the server (or the read-only export) gives them.
export type Level = 'massing' | 'structure' | 'envelope' | 'interior' | 'mep'

export interface Numbers {
  height: number
  floor_area: number
  footprint: number
  volumes: Record<string, number> // m³ of closed elements per material
  stats?: Record<string, { value: number; unit: string }> // figures a script computes itself
}

export interface CategoryChange {
  category: string
  level: Level
  added: string[]
  changed: string[]
  removed: string[]
}

export interface Version {
  n: number
  title: string
  summary: string
  prompt: string
  author: string
  time: string
  parents: number[]
  level: Level | null
  levels: Level[]
  changes: { added: string[]; removed: string[]; changed: string[] }
  numbers: Numbers | null
  picture: string | null
  inside: string | null
  side: string | null
  commit: string | null
  elementCount: number
  changedBy: CategoryChange[]
}

export interface History {
  repo: string | null
  readonly: boolean
  versions: Version[] // newest first
}

export const READONLY = import.meta.env.VITE_READONLY === '1'

export async function loadHistory(): Promise<History> {
  const r = await fetch(READONLY ? './data/versions.json' : '/api/versions', { cache: 'no-store' })
  return r.json()
}

export const pictureUrl = (v: Version, file: string) => (READONLY ? `./data/${v.n}/${file}` : `/history/${v.n}/${file}`)

// Massing: the building's overall extents changed. The others follow the element categories:
// structure (columns, beams, braces, slabs), envelope (walls, windows, roof), interior, MEP.
export const LEVELS: { key: Level; label: string }[] = [
  { key: 'massing', label: 'Massing' },
  { key: 'structure', label: 'Structure' },
  { key: 'envelope', label: 'Envelope' },
  { key: 'interior', label: 'Interior' },
  { key: 'mep', label: 'MEP' },
]
export const levelLabel = (l: Level | null) => LEVELS.find((x) => x.key === l)?.label ?? ''

// What the measurements are, exactly: see NUMBERS_NOTE.
export interface Row {
  key: string
  label: string
  unit: string
  digits: number
  get: (n: Numbers) => number
}

export function measurementRows(...versions: (Version | undefined)[]): Row[] {
  const materials = [...new Set(versions.flatMap((v) => Object.keys(v?.numbers?.volumes ?? {})))].sort()
  const stats = [...new Set(versions.flatMap((v) => Object.keys(v?.numbers?.stats ?? {})))]
  const shown: Record<string, string> = { n: '', deg: '°' }
  const unitOf = (k: string) => {
    const u = versions.map((v) => v?.numbers?.stats?.[k]?.unit).find(Boolean) ?? ''
    return u in shown ? shown[u] : u
  }
  return [
    ...stats.map((k) => ({
      key: 's-' + k,
      label: k,
      unit: unitOf(k),
      digits: Number.isInteger(versions.map((v) => v?.numbers?.stats?.[k]?.value).find((x) => x !== undefined)) ? 0 : 1,
      get: (n: Numbers) => n.stats?.[k]?.value ?? 0,
    })),
    { key: 'height', label: 'Height to highest point', unit: 'm', digits: 2, get: (n) => n.height },
    { key: 'floor_area', label: 'Gross floor area', unit: 'm²', digits: 1, get: (n) => n.floor_area },
    { key: 'footprint', label: 'Footprint', unit: 'm²', digits: 1, get: (n) => n.footprint },
    ...materials.map((m) => ({
      key: 'v-' + m,
      label: `${m[0].toUpperCase()}${m.slice(1)} volume`,
      unit: 'm³',
      digits: 2,
      get: (n: Numbers) => n.volumes?.[m] ?? 0,
    })),
  ]
}

export const NUMBERS_NOTE =
  'Height from ±0.00 to the highest point. Gross floor area from the floor plates at their outer edge; footprint is ' +
  'their plan projection. Volumes are the sum of closed elements per material; where elements overlap, the overlap counts twice.'

// Author colours: never red, which only ever means "changed".
const PALETTE = ['#4C90F0', '#32A467', '#9881F3', '#D1980B', '#00A396', '#8F99A8']

export function authorColors(versions: Version[]): Map<string, string> {
  const m = new Map<string, string>()
  ;[...versions].sort((a, b) => a.n - b.n).forEach((v) => {
    if (!m.has(v.author)) m.set(v.author, PALETTE[m.size % PALETTE.length])
  })
  return m
}

export function relativeTime(iso: string, now = Date.now()): string {
  const s = Math.max(0, (now - new Date(iso).getTime()) / 1000)
  if (s < 60) return 'just now'
  if (s < 3600) return `${Math.floor(s / 60)} min ago`
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`
  const d = Math.floor(s / 86400)
  return d === 1 ? 'yesterday' : `${d} days ago`
}

export function exactTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

export function fmt(x: number, digits: number): string {
  return x.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits })
}

const scriptCache = new Map<number, Promise<Record<string, string>>>()

// The scripts of version n: {file name: text}.
export function loadScripts(n: number): Promise<Record<string, string>> {
  if (!scriptCache.has(n)) {
    const url = READONLY ? `./data/scripts/${n}.json` : `/api/scripts/${n}`
    scriptCache.set(n, fetch(url).then((r) => r.json()))
  }
  return scriptCache.get(n)!
}
