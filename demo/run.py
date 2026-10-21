"""Builds the demo history: a reconstruction of a football stadium in the manner of the Allianz
Arena, Munich (Herzog & de Meuron with ArupSport, 2002-2005), by three fictional authors, through
the real pipeline.

It is not the architects' design process. It starts with rough massing studies, one branch per
person, then works in parallel phases where each of the three owns one branch (bowl, structure
and site; envelope, roof and rooms; services, lighting and the last bowl row; the 2012-14
capacity changes and the LED facade), which are then combined. When someone works on a
colleague's branch, the title says so. The milestones follow the published history (see
demo/SOURCES.md): a three-tier bowl for about 66,000 with the first row raised, an envelope of
rhomboid ETFE cushions on 96 diagonal lines and 30 rings, 96 radial steel trusses cantilevering
about 50 m, a maximum height of about 40 m, an esplanade from the south, 106 hospitality boxes,
about 20 air-conditioning systems, the upper-tier and corner additions that took capacity to
75,024 in 2014, and the LED facade of 2015. Everything else is an estimate or invented, and the
steps between those milestones are invented.

Each step is what Claude would do after a chat message: edit the scripts in scripts/, then save
a version (Rhino build, measurements, element compare, picture, commit). Branches use
tools/start_from.py and restores tools/restore.py, as in a chat. Summaries of value changes are
written from the actual before and after values.

  py demo/run.py          (from an empty history)
"""
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PARTS = os.path.join(HERE, "stadium")
sys.path.insert(0, os.path.join(ROOT, "tools"))
import autosave  # noqa: E402
import combine  # noqa: E402
import start_from  # noqa: E402

SCRIPTS = os.path.join(ROOT, "scripts")
LIAM, MAYA, JONAS = "Liam", "Maya", "Jonas"

# How each design value reads in a summary: (label, unit). Unit m, mm (stored in m), deg, %, n, or names.
LABELS = {
    "m_type": ("mass", {0: "one ring, superellipse plan", 1: "four separate stands", 2: "one ring, circular plan",
                        3: "one ring, chamfered rectangle"}),
    "m_a": ("mass half-length", "m"), "m_b": ("mass half-width", "m"), "m_p": ("mass plan exponent (2 = ellipse)", "x"),
    "m_h": ("mass height", "m"), "m_flare": ("top flare, share of the plan", "%"),
    "m_open": ("opening, share of the plan", "%"),
    "runoff": ("distance from touchline to the first row", "m"), "corner_r": ("bowl corner radius", "m"),
    "bay": ("bowl bay width", "m"), "tread": ("row depth", "mm"), "c_value": ("C-value, tier 1", "mm"),
    "c2": ("C-value, tier 2", "mm"), "c3": ("C-value, tier 3", "mm"),
    "first_h": ("eye height of the first row above the pitch", "m"),
    "rows1": ("rows in tier 1", "n"), "rows2": ("rows in tier 2", "n"), "rows3": ("rows in tier 3", "n"),
    "gap2": ("gap between tiers 1 and 2", "m"), "lift2": ("step up from tier 1 to tier 2", "m"),
    "gap3": ("gap between tiers 2 and 3", "m"), "lift3": ("step up from tier 2 to tier 3", "m"),
    "raker_d": ("raker depth", "mm"), "col_b": ("bowl column size", "mm"), "conc_w": ("concourse depth", "m"),
    "env_a": ("envelope half-length", "m"), "env_b": ("envelope half-width", "m"),
    "env_p": ("envelope plan exponent (2 = ellipse)", "x"), "env_z0": ("envelope base level", "m"),
    "env_h": ("envelope rim height", "m"), "bulge": ("facade bulge, share of the radius", "%"),
    "cant": ("roof cantilever", "m"), "roof_rise": ("roof rise", "m"), "roof_drop": ("roof fall to the inner edge", "m"),
    "env_div": ("envelope divisions around", "n"), "rings_f": ("facade rings", "n"), "rings_r": ("roof rings", "n"),
    "env_on": ("ETFE cushions", {0: "none", 1: "facade", 2: "roof", 3: "facade and roof"}),
    "trusses": ("roof trusses", "n"), "truss_d": ("truss depth at the rim", "m"), "tip_d": ("truss depth at the tip", "m"),
    "panels": ("truss panels", "n"), "purlins": ("purlin rings", "n"), "support_every": ("a column under every n-th truss", "n"),
    "esp_on": ("esplanade", {0: "none", 1: "ramp from the south"}), "esp_w": ("esplanade width", "m"),
    "esp_l": ("esplanade length", "m"), "garages": ("car parks", "n"), "garage_levels": ("car park storeys", "n"),
    "boxes_n": ("hospitality boxes", "n"), "box_w": ("box width", "m"), "box_d": ("box depth", "m"),
    "rooms_n": ("team rooms", "n"), "room_w": ("team room width", "m"), "tunnel_w": ("players' tunnel width", "m"),
    "flood_n": ("floodlights", "n"), "facade_rings": ("facade lighting rings", "n"),
    "led": ("facade lighting", {0: "luminaire housings", 1: "LED strips"}),
    "ahu_n": ("air-handling units", "n"), "duct_d": ("supply ring duct diameter", "mm"),
    "duct_ring": ("supply ring distance from the touchline", "m"), "down_n": ("rainwater downpipes", "n"),
}


def value(name):
    """Current default of a gh-input, from the first script that has it."""
    for f in sorted(os.listdir(SCRIPTS)):
        m = re.search(r"^# gh-input: %s \w+ (\S+)" % name, open(os.path.join(SCRIPTS, f), encoding="utf-8").read(), re.M)
        if m:
            return float(m.group(1))
    return None


def fmt(name, x):
    unit = LABELS[name][1]
    if isinstance(unit, dict):
        return unit[int(x)]
    if unit == "mm":
        return "%d mm" % round(x * 1000)
    if unit == "m":
        return ("%.2f" % x).rstrip("0").rstrip(".") + " m"
    if unit == "deg":
        return "%g°" % x
    if unit == "%":
        return "%g %%" % round(x * 100, 1)
    if unit == "x":
        return "%g" % x
    return "%d" % x


def describe(before, values):
    parts = []
    for k, x in values.items():
        b = before.get(k)
        if b is None or abs(b - x) < 1e-9:
            continue
        label = LABELS[k][0]
        parts.append("%s%s from %s to %s" % (label[0].upper(), label[1:], fmt(k, b), fmt(k, x)))
    return ". ".join(parts) + "." if parts else ""


def set_(**values):
    """Change gh-input defaults in every script that has them (shared sliders)."""
    for f in os.listdir(SCRIPTS):
        path = os.path.join(SCRIPTS, f)
        src = open(path, encoding="utf-8").read()
        for k, x in values.items():
            src = re.sub(r"^(# gh-input: %s \w+ )\S+" % k, r"\g<1>%s" % x, src, flags=re.M)
        open(path, "w", encoding="utf-8", newline="\n").write(src)


def add(*parts):
    """Add category scripts, taking over the shared values the model already has."""
    shared = {}
    for p in parts:
        src = open(os.path.join(PARTS, p + ".py"), encoding="utf-8").read()
        for name in re.findall(r"^# gh-input: (\w+)", src, re.M):
            if value(name) is not None:
                shared[name] = "%g" % value(name)
        open(os.path.join(SCRIPTS, p + ".py"), "w", encoding="utf-8", newline="\n").write(src)
    set_(**shared)


def save(author, title, summary, parents=None):
    rec = autosave.save(title, summary, author, parents)
    if rec is None:
        raise RuntimeError("%r changed nothing in the scripts" % title)
    stats = (rec.get("numbers") or {}).get("stats", {})
    seats = stats.get("Seats, estimated at 0.5 m per seat", {}).get("value")
    print("#%d %-40s %-6s %-9s seats=%s pic=%s inside=%s" % (
        rec["n"], title.encode("ascii", "replace").decode(), author, rec["level"], seats, bool(rec["picture"]),
        bool(rec["inside"])), flush=True)
    return rec["n"]


def v(author, title, why="", parents=None, **values):
    """One design change: set values, write the summary from before and after, save."""
    before = {k: value(k) for k in values}
    set_(**values)
    return save(author, title, " ".join(s for s in (why, describe(before, values)) if s), parents)


def start(n):
    """The next version branches from #n (as "try X from #n" in a chat)."""
    start_from.checkout(n)
    with open(os.path.join(ROOT, ".history", "tmp", "start_from.json"), "w") as f:
        f.write('{"version": %d}' % n)


def restore(n, author):
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "restore.py"), str(n), "--author", author],
                   check=True, capture_output=True)
    m = autosave.versions()[-1]
    print("#%d Restore #%d (%s)" % (m, n, author), flush=True)
    return m


class Story:
    """Parallel lines of work. Each line has a head version; working on a line checks its head
    out first (a branch, as "try X from #n" in a chat), so the lines interleave in time."""

    def __init__(self):
        self.heads = {}
        self.bases = {}  # line -> the version it was forked from

    def go(self, line):
        head = self.heads.get(line)
        if head is not None and head != autosave.versions()[-1]:
            start(head)

    def fork(self, new, line):
        self.heads[new] = self.bases[new] = self.heads[line]

    def merge_in(self, other):
        """Three-way merge of the other line's scripts into the checked-out ones (git merge-file,
        ours on a clash), so what the other line changed since its fork comes across."""
        files = lambda n: {f: combine.git("show", "%s:scripts/%s" % (combine.commit_of(n), f))
                           for f in combine.git("ls-tree", "--name-only", combine.commit_of(n), "scripts/").split()
                           for f in [os.path.basename(f)]}
        base, theirs = files(self.bases[other]), files(self.heads[other])
        tmp = os.path.join(ROOT, ".history", "tmp")
        new = []
        for f, text in theirs.items():
            mine = os.path.join(SCRIPTS, f)
            if not os.path.exists(mine) or f not in base:
                open(mine, "w", encoding="utf-8", newline="\n").write(text)  # new in the other line
                new.append(f)
                continue
            if text == base[f]:
                continue
            for tag, content in (("base", base[f]), ("theirs", text)):
                open(os.path.join(tmp, "merge-" + tag), "w", encoding="utf-8", newline="\n").write(content)
            r = subprocess.run(["git", "merge-file", "-p", "--ours", mine, os.path.join(tmp, "merge-base"),
                                os.path.join(tmp, "merge-theirs")], capture_output=True, text=True, encoding="utf-8")
            open(mine, "w", encoding="utf-8", newline="\n").write(r.stdout)
        # a script new from the other line still carries the shared values of its fork point
        shared = {}
        for f in os.listdir(SCRIPTS):
            if f not in new:
                text = open(os.path.join(SCRIPTS, f), encoding="utf-8").read()
                for name, val in re.findall(r"^# gh-input: (\w+) \w+ (\S+)", text, re.M):
                    shared.setdefault(name, val)
        for f in new:
            path = os.path.join(SCRIPTS, f)
            src = open(path, encoding="utf-8").read()
            for name, val in shared.items():
                src = re.sub(r"^(# gh-input: %s \w+ )\S+" % name, r"\g<1>%s" % val, src, flags=re.M)
            open(path, "w", encoding="utf-8", newline="\n").write(src)

    def do(self, line, author, title, why="", adds=(), drops=(), parents=None, **values):
        self.go(line)
        if adds:
            add(*adds)
        for d in drops:
            os.remove(os.path.join(SCRIPTS, d + ".py"))
        if parents:
            parents = [self.heads[line]] + [self.heads[p] for p in parents]
        self.heads[line] = v(author, title, why, parents, **values)
        return self.heads[line]

    def combine(self, line, other, author, title, why, **values):
        self.go(line)
        self.merge_in(other)
        self.heads[line] = v(author, title, why, [self.heads[line], self.heads[other]], **values)
        return self.heads[line]

    def restore(self, line, n, author):
        self.go(line)
        self.heads[line] = restore(n, author)
        return self.heads[line]


def main():
    if os.path.isdir(SCRIPTS):
        shutil.rmtree(SCRIPTS)
    os.makedirs(SCRIPTS)
    os.makedirs(os.path.join(ROOT, ".history", "tmp"), exist_ok=True)
    s = Story()

    # 1. Massing. Three people, three branches, one owner each --------------------------------------
    add("site", "massing")
    first = save(LIAM, "Oval ring mass, 40 m",
                 "A first mass on the site: one ring, oval in plan, 260 × 230 m and 40 m high, open over the pitch.")
    s.heads["main"] = first
    s.fork("liam", "main")
    s.fork("maya", "main")
    s.fork("jonas", "main")
    s.do("maya", MAYA, "Chamfered rectangle mass", "A ring that follows the pitch, corners chamfered.", m_type=3)
    s.do("jonas", JONAS, "Circular ring mass", "A circle: the same structure all the way round.", m_type=2)
    s.do("liam", LIAM, "Oval mass 50 m high", "", m_h=50)
    s.do("maya", MAYA, "Rectangle tight to the pitch", "", m_a=125, m_b=100)
    s.do("jonas", JONAS, "Circle flaring outwards", "", m_flare=0.1)
    s.do("liam", LIAM, "Study: four separate stands", "One stand per side, open corners.", m_type=1)
    s.do("maya", MAYA, "Rectangle 36 m high", "", m_h=36)
    s.do("jonas", JONAS, "Circle 250 m across", "", m_a=125, m_b=125)
    s.do("liam", LIAM, "Study: stands 30 m high", "Not taken further: open corners lose the enclosure.", m_h=30)
    s.do("maya", MAYA, "Rectangle at envelope size", "", m_a=130, m_b=115)
    s.do("jonas", JONAS, "Circle, larger opening", "Not taken further: a circle leaves deep corners behind the goals.",
         m_open=0.68)
    s.restore("liam", first, LIAM)
    s.do("maya", MAYA, "Rectangle, rounder corners", "", m_p=2.4)
    s.do("liam", LIAM, "Oval squared, exponent 2.4", "", m_p=2.4)
    s.do("liam", LIAM, "Slight outward flare", "", m_flare=0.04)
    s.heads["main"] = s.heads["liam"]
    s.combine("main", "maya", LIAM, "Superellipse ring: oval facade, tight corners",
              "Combines Liam's oval (#%d) with Maya's rectangle (#%d). Claude asked whether the rectangle's tight "
              "corners or the oval's continuous facade mattered more; Liam kept one continuous ring with a "
              "superellipse plan, exponent 2.4, which brings the corners closer to the pitch."
              % (s.heads["liam"], s.heads["maya"]), m_type=0)
    s.do("main", JONAS, "Mass 44 m, roof allowance", "Room for a roof structure above the stands.", m_h=44)

    # 2. Bowl (Liam), structure (Jonas) and site (Maya) in parallel ------------------------------------
    s.do("main", LIAM, "Bowl replaces the massing ring",
         "The ring mass gives way to a seating bowl set out from sightlines: one tier of 20 rows, 800 mm deep, "
         "90 mm C-value, from 7.5 m behind the touchline.", adds=("bowl",), drops=("massing",))
    s.fork("bowl", "main")
    s.fork("struct", "main")
    s.fork("site", "main")
    s.do("bowl", LIAM, "Second tier", "", rows2=20)
    s.do("struct", JONAS, "Raker frames under the bowl", "A concrete raker and a front and back column on every bay line.",
         adds=("rakers",))
    s.do("site", MAYA, "Esplanade from the south", "A ramp 60 m wide rising from the south to the plinth top.",
         esp_on=1, esp_l=90)
    s.do("bowl", LIAM, "Third tier", "Three tiers for about 66,000.", rows3=16)
    s.do("struct", JONAS, "Rakers 1.4 m deep", "", raker_d=1.4)
    s.do("site", MAYA, "Esplanade 80 m wide", "", esp_w=80)
    three = s.heads["bowl"]
    s.do("bowl", LIAM, "Study: two deep tiers", "", rows1=28, rows2=28, rows3=0)
    s.do("struct", JONAS, "Bowl bays 9 m", "", bay=9)
    s.do("site", MAYA, "Esplanade 100 m long", "A gentler slope from the station side.", esp_l=100)
    s.restore("bowl", three, LIAM)
    s.do("struct", JONAS, "Concourse behind each tier", "", adds=("concourses",))
    s.do("bowl", LIAM, "Tier steps 2.5 m", "", lift2=2.5, lift3=2.5)
    s.do("bowl", JONAS, "Jonas on Liam's bowl: tier 3 C-value 60 mm",
         "Handoff: the upper tier was over 35°; a 60 mm C-value flattens it.", c3=0.06)
    s.do("struct", JONAS, "Concourses 10 m deep", "", conc_w=10)
    s.do("bowl", LIAM, "First row raised",
         "Raised so the lower tier is steeper than usual and still sees the touchline and goal line, as ArupSport "
         "describes for the built stadium.", first_h=1.8)
    s.do("struct", JONAS, "Columns 900 mm", "", col_b=0.9)
    s.do("bowl", LIAM, "Tier 2 two rows deeper", "", rows2=22)
    s.heads["main"] = s.heads["bowl"]
    s.combine("main", "struct", LIAM, "Bowl on Jonas's raker frames",
              "Combines the sightline work (#%d) with Jonas's raker frames and concourses (#%d). Claude checked that "
              "every tier sits on a raker after the steps changed and asked about the 900 mm columns; Jonas kept them."
              % (s.heads["bowl"], s.heads["struct"]))
    s.combine("main", "site", LIAM, "Esplanade joins the plinth",
              "Takes Maya's esplanade (#%d). Claude checked that the ramp lands on the plinth top at +12 m."
              % s.heads["site"])

    # 3. Envelope (Maya), roof (Jonas) and rooms (Liam) in parallel ------------------------------------
    s.fork("env", "main")
    s.fork("roof", "main")
    s.fork("rooms", "main")
    s.do("env", MAYA, "Facade of ETFE cushions",
         "Rhomboid ETFE cushions on the facade from +12 m to the rim at +40 m, 96 lines around and 9 rings, on steel "
         "transoms. Plan: superellipse, 260 × 230 m.", adds=("envelope", "transoms"))
    s.do("roof", JONAS, "48 radial roof trusses",
         "Steel trusses from the rim inwards, 8 m deep at the rim, 1.5 m at the tip, a column under every second one.",
         adds=("roof_trusses",))
    s.do("rooms", LIAM, "Hospitality boxes behind tier 2", "Boxes on both long sides, 4.5 × 6 m, glazed fronts.",
         adds=("hospitality",), boxes_n=80)
    s.do("env", MAYA, "Facade bulges outwards", "", bulge=0.05)
    s.do("roof", JONAS, "Cantilever 40 m", "", cant=40)
    s.do("rooms", LIAM, "106 hospitality boxes", "", boxes_n=106)
    s.do("env", MAYA, "Study: true ellipse in plan", "", env_p=2.0)
    s.do("roof", JONAS, "Cantilever 50 m", "The roof now covers all three tiers.", cant=50)
    s.do("rooms", LIAM, "Team rooms under the main stand",
         "Team rooms either side of a 4 m players' tunnel at pitch level.", adds=("team_rooms",), rooms_n=6)
    s.do("env", MAYA, "Plan exponent back to 2.4", "The ellipse pushed the corners away from the pitch.", env_p=2.4)
    t96 = s.do("roof", JONAS, "96 trusses, one per envelope line", "", trusses=96)
    s.do("rooms", LIAM, "Boxes 4.2 m wide", "", box_w=4.2)
    s.do("env", MAYA, "Bulge 3 %", "", bulge=0.03)
    s.do("roof", JONAS, "Study: 72 trusses, 10 m deep", "Fewer, deeper trusses.", trusses=72, truss_d=10)
    s.do("rooms", LIAM, "Eight team rooms", "", rooms_n=8)
    s.do("env", MAYA, "Cushion grid doubled, 192 lines", "Twice as many, smaller cushions.", env_div=192)
    s.restore("roof", t96, JONAS)
    s.do("rooms", LIAM, "Tunnel 5 m wide", "", tunnel_w=5)
    s.do("roof", JONAS, "Trusses 9 m deep at the rim", "With 96 trusses the 10 m of the 72-truss study is not needed.",
         truss_d=9)
    s.do("env", JONAS, "Jonas on Maya's envelope: transoms checked",
         "Handoff: 10 facade rings so the transoms meet the truss supports.", rings_f=10)
    s.do("roof", JONAS, "21 purlin rings", "One purlin ring per roof ring of the envelope.", purlins=21)
    s.combine("main", "env", MAYA, "Envelope: 192-line ETFE grid",
              "Takes Maya's envelope (#%d): ETFE cushions on 192 lines, 10 facade rings." % s.heads["env"])
    s.combine("main", "roof", LIAM, "Roof: 96 trusses, cushions over the stands",
              "Combines the envelope with Jonas's roof (#%d). Claude checked that the trusses follow the roof rings "
              "of the envelope and asked whether the cushions should continue over the roof; Maya said yes."
              % s.heads["roof"], env_on=3)
    s.combine("main", "rooms", LIAM, "Combine: 106 boxes and team rooms",
              "Takes Liam's hospitality boxes and team rooms (#%d)." % s.heads["rooms"])

    # 4. Before opening: services (Jonas), facade lighting (Maya), last bowl row (Liam) -------------------
    s.fork("mep", "main")
    s.fork("light", "main")
    s.fork("bowl2", "main")
    s.do("mep", JONAS, "Air handling and drainage",
         "Air-handling units on a ring behind tier 1 with a ring supply duct, a roof gutter and downpipes.",
         adds=("services",), ahu_n=12, down_n=24)
    s.do("light", MAYA, "Facade lighting rings",
         "Luminaire housings on 9 rings behind the facade cushions, for one colour at a time.",
         adds=("lighting",), facade_rings=9)
    s.do("bowl2", LIAM, "Tier 1 one row deeper", "", rows1=21)
    s.do("mep", JONAS, "20 air-handling units", "", ahu_n=20)
    s.do("light", MAYA, "Facade lighting on 12 rings", "An even light across the taller middle of the facade.",
         facade_rings=12)
    s.do("bowl2", JONAS, "Jonas on Liam's bowl: rakers 1.5 m",
         "Handoff: deeper rakers for the extra row of tier 1.", raker_d=1.5)
    duct = s.do("mep", JONAS, "Ring duct 1.0 m", "", duct_d=1.0)
    s.do("light", MAYA, "Floodlights at the roof edge", "", flood_n=160)
    s.do("mep", JONAS, "Study: ring duct 40 m out", "Moves the ring away from the box zone.", duct_ring=40)
    s.do("light", MAYA, "200 floodlights", "", flood_n=200)
    s.do("mep", JONAS, "32 downpipes", "", down_n=32)
    s.combine("main", "mep", LIAM, "Services: 20 AHUs, ring duct at 40 m",
              "Takes Jonas's services (#%d). Claude checked that the ring at 40 m stays under the tier 1 concourse "
              "and clear of the boxes." % s.heads["mep"])
    s.combine("main", "light", LIAM, "Lighting: 12 facade rings, 200 floodlights",
              "Takes Maya's lighting (#%d). Claude asked whether the floodlights clear the inner roof edge; they "
              "hang below the truss tips." % s.heads["light"])
    s.combine("main", "bowl2", LIAM, "Combine: tier 1 at 21 rows, deeper rakers",
              "Takes the extra tier 1 row and Jonas's deeper rakers (#%d)." % s.heads["bowl2"])

    # 5. After opening: 2012-14 capacity (Liam), 2015 LED facade (Maya) ---------------------------------
    s.fork("cap", "main")
    s.fork("led", "main")
    s.do("cap", LIAM, "Tier 3 two rows deeper", "More seats at the back of the upper tier.", rows3=18)
    s.do("led", MAYA, "LED strips replace the facade luminaires", "Slim LED strips replace the luminaire housings behind the cushions.", led=1)
    s.do("cap", JONAS, "Jonas on Liam's branch: tier 3 C-value 55 mm", "Handoff: keeps the deeper upper tier under 35°.",
         c3=0.055)
    s.do("led", MAYA, "LED strips on 16 facade rings", "", facade_rings=16)
    s.do("cap", LIAM, "Fuller bowl corners, radius 17 m", "More seats in the corners of the bowl.", corner_r=17)
    s.do("cap", LIAM, "Tier 2 one row deeper", "", rows2=23)
    s.do("led", MAYA, "LED strips back to 12 facade rings", "One strip per facade lighting ring, as before.",
         facade_rings=12)
    s.do("cap", JONAS, "Jonas on Liam's branch: tier 2 C-value 85 mm", "Handoff: tier 2 C-value 85 mm.", c2=0.085)
    s.combine("main", "cap", LIAM, "Combine: more seats in tiers 2 and 3 and the corners",
              "Takes the deeper tiers 2 and 3 and the fuller corners (#%d)." % s.heads["cap"])
    s.combine("main", "led", MAYA, "Combine: LED facade lighting",
              "Takes Maya's LED facade (#%d) onto the expanded stadium." % s.heads["led"])


if __name__ == "__main__":
    main()
