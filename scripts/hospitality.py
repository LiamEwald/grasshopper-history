# category: hospitality boxes
# level: interior
# material: timber
# gh-input: pitch_l float 105 90 120
# gh-input: pitch_w float 68 60 90
# gh-input: runoff float 7.5 3 15
# gh-input: tread float 0.8 0.7 1.0
# gh-input: c_value float 0.09 0.04 0.15
# gh-input: c2 float 0.09 0.04 0.15
# gh-input: c3 float 0.06 0.04 0.15
# gh-input: first_h float 1.8 0.6 3.0
# gh-input: rows1 int 20 0 40
# gh-input: rows2 int 22 0 40
# gh-input: gap2 float 2 -8 12
# gh-input: lift2 float 2.5 1 12
# gh-input: boxes_n int 106 0 140
# gh-input: box_w float 4.2 3 9
# gh-input: box_d float 6 4 10
# Hospitality boxes behind the back row of tier 2 on the two long sides: boxes_n boxes in total,
# each box_w wide and box_d deep, as 150 mm party walls (BX-S012 = wall 12 on the south side)
# and a glazed front (BX-FS012). Height 3.0 m.
import Rhino.Geometry as rg

EYE = 1.15


def tier_rows(d0, n0, count, c=c_value):
    out, d, n = [], d0, n0
    for _ in range(count):
        out.append((d, n))
        n = (n + c) * (d + tread) / d
        d += tread
    return out


a, names, floors = [], [], []
if int(rows2) and int(rows1) and int(boxes_n):
    t1 = tier_rows(runoff, first_h, int(rows1))
    d_last, n_last = t1[-1]
    t2 = tier_rows(d_last + tread + gap2, n_last + lift2, int(rows2), c2)
    d2, n2 = t2[-1]
    z = n2 - EYE
    per_side = int(boxes_n) // 2
    run = per_side * box_w
    for side, sy in (("S", -1), ("N", 1)):
        y0 = sy * (pitch_w / 2 + d2 + tread)
        y1 = y0 + sy * box_d
        for k in range(per_side + 1):
            x = -run / 2 + k * box_w
            a.append(rg.Box(rg.Plane.WorldXY, rg.Interval(x - 0.075, x + 0.075), rg.Interval(min(y0, y1), max(y0, y1)),
                            rg.Interval(z, z + 3.0)).ToBrep())
            names.append("BX-%s%03d" % (side, k + 1))
        for k in range(per_side):
            x = -run / 2 + k * box_w
            a.append(rg.Box(rg.Plane.WorldXY, rg.Interval(x + 0.075, x + box_w - 0.075),
                            rg.Interval(min(y0, y0 + sy * 0.05), max(y0, y0 + sy * 0.05)), rg.Interval(z + 0.9, z + 3.0)).ToBrep())
            names.append("BX-F%s%03d" % (side, k + 1))
