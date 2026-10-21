# category: concourse slabs
# level: structure
# material: concrete
# gh-input: pitch_l float 105 90 120
# gh-input: pitch_w float 68 60 90
# gh-input: runoff float 7.5 3 15
# gh-input: corner_r float 20 0 60
# gh-input: bay float 9 6 15
# gh-input: tread float 0.8 0.7 1.0
# gh-input: c_value float 0.09 0.04 0.15
# gh-input: c2 float 0.09 0.04 0.15
# gh-input: c3 float 0.06 0.04 0.15
# gh-input: first_h float 1.8 0.6 3.0
# gh-input: rows1 int 21 0 40
# gh-input: rows2 int 22 0 40
# gh-input: rows3 int 16 0 40
# gh-input: gap2 float 2 -8 12
# gh-input: lift2 float 2.5 1 12
# gh-input: gap3 float 2 -8 12
# gh-input: lift3 float 2.5 1 12
# gh-input: conc_w float 10 4 16
# Concourse behind each tier: a 300 mm slab ring conc_w deep at the level of the tier's back
# row, one slab per bay (CS2-B014). Their outlines are floor plates for gross floor area.
import Rhino.Geometry as rg

EYE = 1.15


def ring(d):
    hx, hy = pitch_l / 2 + d, pitch_w / 2 + d
    r = min(corner_r, hx - 0.1, hy - 0.1)
    crv = rg.Rectangle3d(rg.Plane.WorldXY, rg.Interval(-hx, hx), rg.Interval(-hy, hy)).ToNurbsCurve()
    if r > 0.01:
        crv = rg.Curve.CreateFilletCornersCurve(crv, r, 0.001, 0.001) or crv
    return crv


def tier_rows(d0, n0, count, c=c_value):
    out, d, n = [], d0, n0
    for _ in range(count):
        out.append((d, n))
        n = (n + c) * (d + tread) / d
        d += tread
    return out


tiers = []
d0, n0 = runoff, first_h
for count, gap, lift, c in ((int(rows1), 0.0, 0.0, c_value), (int(rows2), gap2, lift2, c2), (int(rows3), gap3, lift3, c3)):
    if not count:
        break
    if tiers:
        d_last, n_last = tiers[-1][-1]
        d0, n0 = d_last + tread + gap, n_last + lift
    tiers.append(tier_rows(d0, n0, count, c))

base = ring(runoff)
n_bays = max(8, int(round(base.GetLength() / bay)))
frames = []
for t in base.DivideByCount(n_bays, True):
    p = base.PointAt(t)
    out = rg.Vector3d.CrossProduct(base.TangentAt(t), rg.Vector3d.ZAxis)
    if out * rg.Vector3d(p.X, p.Y, 0) < 0:
        out.Reverse()
    out.Unitize()
    frames.append((p, out))

a, names, floors = [], [], []
for k, tier in enumerate(tiers):
    d, n = tier[-1]
    z = n - EYE
    o0, o1 = d - runoff + tread, d - runoff + tread + conc_w
    for b in range(n_bays):
        p0, v0 = frames[b]
        p1, v1 = frames[(b + 1) % n_bays]
        q = [p0 + v0 * o0, p1 + v1 * o0, p1 + v1 * o1, p0 + v0 * o1]
        pl = rg.Polyline([rg.Point3d(v.X, v.Y, z - 0.3) for v in q] + [rg.Point3d(q[0].X, q[0].Y, z - 0.3)])
        ext = rg.Extrusion.Create(pl.ToNurbsCurve(), 0.3, True)
        if ext:
            a.append(ext.ToBrep())
            names.append("CS%d-B%03d" % (k + 1, b + 1))
            floors.append(rg.Brep.CreateFromCornerPoints(*([rg.Point3d(v.X, v.Y, z) for v in q] + [0.001])))
