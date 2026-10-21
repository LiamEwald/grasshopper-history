// Reads the versions from .history/<n>/version.json and their commits from git.
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const ROOT = path.resolve(__dirname, "..");
const HIST = path.join(ROOT, ".history");

const git = (...args) => execFileSync("git", ["-C", ROOT, ...args], { encoding: "utf8", maxBuffer: 64 << 20 });

function repoUrl() {
  try {
    return git("remote", "get-url", "origin").trim().replace(/\.git$/, "").replace(/^git@github\.com:/, "https://github.com/");
  } catch {
    return null;
  }
}

let cache = { key: null, list: [] };

// Changes against the first parent, grouped by element category (columns, girders, joists...).
function changedByCategory(v, parent) {
  const groups = {};
  const add = (kind, name, el) => {
    const g = (groups[el.category] ||= { category: el.category, level: el.level, added: [], changed: [], removed: [] });
    g[kind].push(name);
  };
  for (const kind of ["added", "changed"]) for (const n of v.changes?.[kind] || []) if (v.elements[n]) add(kind, n, v.elements[n]);
  for (const n of v.changes?.removed || []) if (parent?.elements?.[n]) add("removed", n, parent.elements[n]);
  return Object.values(groups);
}

// Version list without the element tables, newest first. Cached until HEAD moves.
function loadVersions() {
  const key = git("rev-parse", "HEAD").trim();
  if (cache.key === key) return cache.list;
  const commits = new Map();
  for (const line of git("log", "--format=%H %s").split("\n")) {
    const m = line.match(/^(\w+) #(\d+) /);
    if (m && !commits.has(+m[2])) commits.set(+m[2], m[1]);
  }
  const raw = new Map();
  for (const dir of fs.readdirSync(HIST)) {
    const file = path.join(HIST, dir, "version.json");
    if (/^\d+$/.test(dir) && fs.existsSync(file)) raw.set(+dir, JSON.parse(fs.readFileSync(file, "utf8")));
  }
  const list = [];
  for (const full of raw.values()) {
    const { elements, ...v } = full;
    v.commit = commits.get(v.n) || null;
    v.elementCount = Object.keys(elements || {}).length;
    v.changedBy = changedByCategory(full, raw.get(v.parents[0]));
    list.push(v);
  }
  list.sort((a, b) => b.n - a.n);
  cache = { key, list };
  return list;
}

// The scripts as they were in version n: {file name: text}, for the code diff.
function scriptsOf(n) {
  const v = loadVersions().find((x) => x.n === n);
  if (!v || !v.commit) return null;
  const files = {};
  for (const f of git("ls-tree", "--name-only", v.commit, "scripts/").split("\n").filter(Boolean)) {
    files[path.basename(f)] = git("show", `${v.commit}:${f}`);
  }
  return files;
}

module.exports = { ROOT, HIST, git, repoUrl, loadVersions, scriptsOf };
