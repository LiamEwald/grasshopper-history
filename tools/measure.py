"""Numbers and the element table for the model Grasshopper just solved. Runs inside Rhino.

Writes .history/tmp/measure.json:
  numbers:  height, gross floor area, footprint (plan projection of the floor plates),
            solid volume per material (from each script's "# material:" header),
            stats: figures a script computes itself, such as a seat count
  elements: {name: {category, level, material, box: [x0,y0,z0,x1,y1,z1], size}}
The element table is what versions are compared by (compare() in tools/autosave.py).
"""
import json
import os
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULT = os.path.join(ROOT, ".history", "tmp", "measure.json")
GH_PATH = os.path.join(ROOT, "model.gh")


def write_result(data):
    os.makedirs(os.path.dirname(RESULT), exist_ok=True)
    with open(RESULT + ".tmp", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    os.replace(RESULT + ".tmp", RESULT)


def header(name, key, default):
    try:
        for line in open(os.path.join(ROOT, "scripts", name + ".py"), encoding="utf-8"):
            if line.startswith("# %s:" % key):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return default


try:
    import Rhino.Geometry as rg
    import Grasshopper as gh

    def find_doc():
        for d in gh.Instances.DocumentServer:
            if d.FilePath and os.path.normcase(d.FilePath) == os.path.normcase(GH_PATH):
                return d
        raise RuntimeError("model.gh is not open; run gh_build first")

    def to_geometry(goo):
        geo = goo.ScriptVariable() if hasattr(goo, "ScriptVariable") else goo
        if isinstance(geo, (rg.Extrusion, rg.Box)):
            geo = geo.ToBrep()
        return geo if isinstance(geo, rg.GeometryBase) else None

    def output(comp, nick):
        for p in comp.Params.Output:
            if p.NickName == nick:
                return [goo.ScriptVariable() if hasattr(goo, "ScriptVariable") else goo
                        for goo in p.VolatileData.AllData(True)]
        return []

    def size_of(g):
        """Volume of a closed solid, else area: changes when the element is resized or reshaped."""
        if (isinstance(g, rg.Brep) and g.IsSolid) or (isinstance(g, rg.Mesh) and g.IsClosed):
            vmp = rg.VolumeMassProperties.Compute(g)
            return abs(vmp.Volume) if vmp else 0.0, True
        amp = rg.AreaMassProperties.Compute(g) if isinstance(g, (rg.Brep, rg.Mesh, rg.Surface)) else None
        return (amp.Area if amp else 0.0), False

    def plan_area(plates):
        """Area of the plan projection of the floor plates (overlaps counted once)."""
        to_plan = rg.Transform.PlanarProjection(rg.Plane.WorldXY)
        outlines = []
        for f in plates:
            joined = rg.Curve.JoinCurves(f.DuplicateNakedEdgeCurves(True, False) or [])
            for c in joined:
                c = c.DuplicateCurve()
                c.Transform(to_plan)
                if c.IsClosed:
                    outlines.append(c)
        if not outlines:
            return 0.0
        union = rg.Curve.CreateBooleanUnion(outlines, 0.001) or outlines
        regions = rg.Brep.CreatePlanarBreps(union, 0.001) or []  # nested outlines become holes
        total = 0.0
        for b in regions:
            amp = rg.AreaMassProperties.Compute(b)
            total += amp.Area if amp else 0.0
        return total

    def main():
        doc = find_doc()
        elements, all_box, floor_area, plates = {}, rg.BoundingBox.Empty, 0.0, []
        volumes = {}  # material -> m3
        stats = {}  # label -> {value, unit}: figures a script computes itself ("label|unit|value")
        warnings = []
        for comp in doc.Objects:
            if not hasattr(comp, "Params") or not any(p.NickName == "names" for p in comp.Params.Output):
                continue
            cat = header(comp.NickName, "category", comp.NickName)
            level = header(comp.NickName, "level", "structure")
            material = header(comp.NickName, "material", "unspecified")
            geos = [to_geometry(x) for x in output(comp, "a")]
            names = [str(n) for n in output(comp, "names")]
            if len(names) != len(geos):
                warnings.append("%s: %d names for %d elements" % (comp.NickName, len(names), len(geos)))
            for i, g in enumerate(geos):
                if g is None:
                    continue
                name = names[i] if i < len(names) else "%s-%d" % (comp.NickName, i + 1)
                if name in elements:
                    warnings.append("%s: name %s used twice" % (comp.NickName, name))
                    name = "%s#%d" % (name, i + 1)
                b = g.GetBoundingBox(True)
                all_box.Union(b)
                s, solid = size_of(g)
                if solid:
                    volumes[material] = volumes.get(material, 0.0) + s
                elements[name] = {"script": comp.NickName, "category": cat, "level": level, "material": material,
                                  "box": [round(v, 3) for v in (b.Min.X, b.Min.Y, b.Min.Z, b.Max.X, b.Max.Y, b.Max.Z)],
                                  "size": round(s, 4)}
            for line in output(comp, "stats"):
                try:
                    label, unit, val = str(line).split("|")
                    stats[label] = {"value": float(val), "unit": unit}
                except ValueError:
                    warnings.append("%s: stats line %r is not label|unit|value" % (comp.NickName, str(line)))
            for f in output(comp, "floors"):
                f = to_geometry(f)
                amp = rg.AreaMassProperties.Compute(f) if f else None
                if amp:
                    floor_area += amp.Area
                    plates.append(f)
        numbers = {
            "height": round(max(all_box.Max.Z, 0.0), 2) if all_box.IsValid else 0,
            "floor_area": round(floor_area, 1),
            "footprint": round(plan_area(plates), 1),
            "volumes": {m: round(v, 2) for m, v in sorted(volumes.items())},
            "stats": stats,
        }
        write_result({"ok": True, "numbers": numbers, "elements": elements, "warnings": warnings})

    main()
except Exception:
    write_result({"ok": False, "error": traceback.format_exc()})
