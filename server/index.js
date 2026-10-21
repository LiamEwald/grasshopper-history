// History server: the versions and pictures for the app, plus Restore and Combine.
// Looking at versions never touches Rhino; only a confirmed Restore rebuilds the model.
const express = require("express");
const fs = require("fs");
const path = require("path");
const { execFile } = require("child_process");
const { ROOT, HIST, repoUrl, loadVersions, scriptsOf } = require("./versions");

const PORT = process.env.PORT || 5174;
const REQUEST = path.join(HIST, "combine-request.json");
const SENT = path.join(HIST, "combine-request-sent.json");
const app = express();
app.use(express.json());

app.get("/api/versions", (req, res) => {
  res.json({ repo: repoUrl(), readonly: false, versions: loadVersions() });
});

app.get("/api/scripts/:n", (req, res) => {
  const files = scriptsOf(parseInt(req.params.n, 10));
  if (!files) return res.status(404).json({ error: "no such version" });
  res.json(files);
});

// Restore: scripts of version n come back, Rhino rebuilds, saved as a new version from n.
app.post("/api/restore", (req, res) => {
  const n = parseInt(req.body.n, 10);
  if (!n) return res.status(400).json({ error: "which version?" });
  execFile("py", [path.join(ROOT, "tools", "restore.py"), String(n)], { cwd: ROOT, timeout: 180000 }, (err, out, errOut) => {
    if (err) return res.status(500).json({ error: errOut || String(err) });
    res.json({ ok: true });
  });
});

// Combine: leave a request for Claude; the prompt hook hands it over on the next message.
app.post("/api/combine", (req, res) => {
  const [a, b] = (req.body.versions || []).map((x) => parseInt(x, 10));
  if (!a || !b || a === b) return res.status(400).json({ error: "pick two versions" });
  fs.writeFileSync(REQUEST, JSON.stringify({ versions: [a, b], time: new Date().toISOString() }));
  if (fs.existsSync(SENT)) fs.unlinkSync(SENT);
  res.json({ ok: true });
});

app.get("/api/combine", (req, res) => {
  const read = (f) => (fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, "utf8")) : null);
  const waiting = read(REQUEST);
  res.json(waiting ? { state: "waiting", versions: waiting.versions } : read(SENT) ? { state: "sent", versions: read(SENT).versions } : { state: "none" });
});

app.use("/history", express.static(HIST));
const dist = path.join(ROOT, "app", "dist");
app.use(express.static(dist));
app.listen(PORT, () => console.log(`History: http://localhost:${PORT}`));
