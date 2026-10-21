# category: plinth and esplanade
# level: structure
# material: concrete
# gh-input: pitch_l float 105 90 120
# gh-input: pitch_w float 68 60 90
# gh-input: env_a float 130 100 150
# gh-input: env_b float 115 90 140
# gh-input: env_p float 2.4 2 4
# gh-input: env_z0 float 12 0 20
# gh-input: esp_on int 1 0 1
# gh-input: esp_w float 80 30 120
# gh-input: esp_l float 90 60 300
# gh-input: garages int 0 0 4
# gh-input: garage_levels int 4 1 6
# The pitch (PITCH, 300 mm build-up, for reference), the concrete plinth ring under the envelope
# from ground to env_z0 (PL-012, 24 segments), and, with esp_on, the esplanade: a ramp esp_w
# wide rising over esp_l from ground in the south to the plinth top (ES-RAMP), with `garages`
# parking garages of garage_levels storeys beside it, two either side (GA2-L3 = garage 2, level 3),
# each 60 x 80 m.
import math
import Rhino.Geometry as rg


def rim(th):
    c, s = math.cos(th), math.sin(th)
    return rg.Point3d(env_a * math.copysign(abs(c) ** (2 / env_p), c), env_b * math.copysign(abs(s) ** (2 / env_p), s), 0)


def box(x0, x1, y0, y1, z0, z1):
    return rg.Box(rg.Plane.WorldXY, rg.Interval(x0, x1), rg.Interval(y0, y1), rg.Interval(z0, z1)).ToBrep()


a, names, floors, stats = [], [], [], []
a.append(box(-pitch_l / 2 - 3, pitch_l / 2 + 3, -pitch_w / 2 - 3, pitch_w / 2 + 3, -0.3, 0.0))
names.append("PITCH")
seg = 24
for i in range(seg):
    t0, t1 = 2 * math.pi * i / seg, 2 * math.pi * (i + 1) / seg
    p0, p1 = rim(t0), rim(t1)
    q = []
    for p in (p0, p1):
        r = math.hypot(p.X, p.Y)
        q.append((p, rg.Point3d(p.X * (r - 12) / r, p.Y * (r - 12) / r, 0)))
    pl = rg.Polyline([q[0][0], q[1][0], q[1][1], q[0][1], q[0][0]])
    ext = rg.Extrusion.Create(pl.ToNurbsCurve(), env_z0, True)
    if ext:
        a.append(ext.ToBrep())
        names.append("PL-%03d" % (i + 1))
if int(esp_on):
    y_top = -env_b - 2
    y_bot = y_top - esp_l
    pts = [rg.Point3d(-esp_w / 2, y_bot, 0), rg.Point3d(esp_w / 2, y_bot, 0),
           rg.Point3d(esp_w / 2, y_top, env_z0), rg.Point3d(-esp_w / 2, y_top, env_z0)]
    srf = rg.Brep.CreateFromCornerPoints(pts[0], pts[1], pts[2], pts[3], 0.001)
    ramp = rg.Brep.CreateFromOffsetFace(srf.Faces[0], -0.5, 0.001, False, True)
    a.append(ramp or srf)
    names.append("ES-RAMP")
    for g in range(int(garages)):  # two each side of the ramp, the first pair nearest the stadium
        side, row = (-1 if g % 2 == 0 else 1), g // 2
        x0 = side * (esp_w / 2 + 5) - (60 if side < 0 else 0)
        y1 = y_top - 10 - row * 85
        for lv in range(int(garage_levels)):
            z = lv * 3.0
            a.append(box(x0, x0 + 60, y1 - 80, y1, z - 0.3, z))
            names.append("GA%d-L%d" % (g + 1, lv + 1))
            floors.append(rg.Brep.CreateFromCornerPoints(rg.Point3d(x0, y1 - 80, z), rg.Point3d(x0 + 60, y1 - 80, z),
                                                         rg.Point3d(x0 + 60, y1, z), rg.Point3d(x0, y1, z), 0.001))
    if int(garages):
        stats.append("Parking spaces, estimated at 25 m² each|n|%d" % (int(garages) * int(garage_levels) * 60 * 80 / 25))
