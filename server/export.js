// Read-only copy for hosting: versions, pictures and each version's scripts into app/public/data.
const fs = require("fs");
const path = require("path");
const { HIST, ROOT, repoUrl, loadVersions, scriptsOf } = require("./versions");

const out = path.join(ROOT, "app", "public", "data");
fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(out, { recursive: true });
const versions = loadVersions();
fs.mkdirSync(path.join(out, "scripts"), { recursive: true });
for (const v of versions) {
  fs.writeFileSync(path.join(out, "scripts", `${v.n}.json`), JSON.stringify(scriptsOf(v.n)));
  for (const pic of [v.picture, v.inside].filter(Boolean)) {
    fs.mkdirSync(path.join(out, String(v.n)), { recursive: true });
    fs.copyFileSync(path.join(HIST, String(v.n), pic), path.join(out, String(v.n), pic));
  }
}
fs.writeFileSync(path.join(out, "versions.json"), JSON.stringify({ repo: repoUrl(), readonly: true, versions }));
console.log(`exported ${versions.length} versions`);
