# category: terrace units
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
# gh-input: rows3 int 18 0 40
# gh-input: gap2 float 2 -8 12
# gh-input: lift2 float 2.5 1 12
# gh-input: gap3 float 2 -8 12
# gh-input: lift3 float 2.5 1 12
# Seating bowl from sightlines. Each row's eye height comes from the C-value formula
#   N(n+1) = (N(n) + C) * (D(n) + T) / D(n)
# D: horizontal distance from the eye to the touchline (the focal point); N: eye height above
# it; T: tread; C: C-value (c_value, c2, c3 for tiers 1-3). The riser is N(n+1) - N(n), so the
# rake steepens row by row.
# Tier 1 starts `runoff` from the touchline with its first eye height first_h. Tier 2 starts
# gap2 behind tier 1's last row (negative: it overhangs tier 1) and lift2 above it; tier 3 the
# same from tier 2. The bowl follows a rectangle around the pitch with corners of radius
# corner_r, in bays of about `bay` metres: one precast terrace unit per row per bay,
# TU2-R05-B023. Stats: seats (one per 0.5 m of row), farthest viewing distance to the far
# corner flag, and the steepest rake of each tier.
import math
import Rhino.Geometry as rg

EYE = 1.15   # eye height above the tread, seated
SEAT_W = 0.5


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

a, names, floors, stats = [], [], [], []
seats, far, rakes = 0, 0.0, []
corners = [rg.Point3d(sx * pitch_l / 2, sy * pitch_w / 2, 0) for sx in (-1, 1) for sy in (-1, 1)]
for k, tier in enumerate(tiers):
    steepest = 0.0
    for r, (d, n) in enumerate(tier):
        z_top = n - EYE
        riser = (tier[r + 1][1] - n) if r + 1 < len(tier) else (n - tier[r - 1][1] if r else 0.4)
        steepest = max(steepest, math.degrees(math.atan2(riser, tread)))
        z_bot = z_top - max(riser, 0.15) - 0.12
        off = d - runoff
        seats += int(ring(d).GetLength() / SEAT_W)
        for b in range(n_bays):
            p0, o0 = frames[b]
            p1, o1 = frames[(b + 1) % n_bays]
            q = [p0 + o0 * off, p1 + o1 * off, p1 + o1 * (off + tread), p0 + o0 * (off + tread)]
            pl = rg.Polyline([rg.Point3d(v.X, v.Y, z_bot) for v in q] + [rg.Point3d(q[0].X, q[0].Y, z_bot)])
            ext = rg.Extrusion.Create(pl.ToNurbsCurve(), z_top - z_bot, True)
            if ext:
                a.append(ext.ToBrep())
                names.append("TU%d-R%02d-B%03d" % (k + 1, r + 1, b + 1))
            if r == len(tier) - 1:
                eye = rg.Point3d(p0.X + o0.X * (off + tread / 2), p0.Y + o0.Y * (off + tread / 2), n)
                far = max(far, max(eye.DistanceTo(c) for c in corners))
    rakes.append(steepest)
stats.append("Seats, estimated at 0.5 m per seat|n|%d" % seats)
stats.append("Farthest viewing distance to a corner flag|m|%.1f" % far)
for k, s in enumerate(rakes):
    stats.append("Steepest rake, tier %d|deg|%.1f" % (k + 1, s))
