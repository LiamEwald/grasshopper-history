# category: raker frames
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
# gh-input: raker_d float 1.5 0.6 2.0
# gh-input: col_b float 0.9 0.5 1.2
# Reinforced-concrete frames under the terraces, one per bay line: for every tier a raker beam
# (500 mm wide, raker_d deep) following the underside of the terrace units from the first to the
# last row, carried by a front and a back column (col_b square) down to pitch level.
# Names RK2-B014, CF2-B014 (front), CB2-B014 (back). Same bowl geometry as bowl.py.
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


def member(p0, p1, b, h):
    d = p1 - p0
    side = rg.Vector3d.CrossProduct(d, rg.Vector3d.ZAxis)
    side.Unitize()
    pl = rg.Plane(p0, d, side)
    if pl.ZAxis.Z < 0:
        pl = rg.Plane(p0, d, -side)
    return rg.Box(pl, rg.Interval(0, d.Length), rg.Interval(-b / 2, b / 2), rg.Interval(-h, 0)).ToBrep()


def column(p, z1, name):
    c = col_b / 2
    a.append(rg.Box(rg.Plane.WorldXY, rg.Interval(p.X - c, p.X + c), rg.Interval(p.Y - c, p.Y + c),
                    rg.Interval(0.0, max(z1, 0.5))).ToBrep())
    names.append(name)


a, names, floors = [], [], []
for b, t in enumerate(base.DivideByCount(n_bays, True)):
    p = base.PointAt(t)
    out = rg.Vector3d.CrossProduct(base.TangentAt(t), rg.Vector3d.ZAxis)
    if out * rg.Vector3d(p.X, p.Y, 0) < 0:
        out.Reverse()
    out.Unitize()
    for k, tier in enumerate(tiers):
        (d_a, n_a), (d_b, n_b) = tier[0], tier[-1]
        pa = p + out * (d_a - runoff)
        pb = p + out * (d_b - runoff + tread)
        za, zb = n_a - EYE - 0.45, n_b - EYE - 0.45
        a.append(member(rg.Point3d(pa.X, pa.Y, za), rg.Point3d(pb.X, pb.Y, zb), 0.5, raker_d))
        names.append("RK%d-B%03d" % (k + 1, b + 1))
        column(pa + out * 0.6, za - raker_d, "CF%d-B%03d" % (k + 1, b + 1))
        column(pb - out * 0.6, zb - raker_d, "CB%d-B%03d" % (k + 1, b + 1))
