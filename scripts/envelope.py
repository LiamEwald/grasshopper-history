# category: ETFE cushions
# level: envelope
# material: ETFE
# gh-input: env_a float 130 100 150
# gh-input: env_b float 115 90 140
# gh-input: env_p float 2.4 2 4
# gh-input: env_z0 float 12 0 20
# gh-input: env_h float 40 30 50
# gh-input: bulge float 0.03 0 0.08
# gh-input: cant float 50 30 60
# gh-input: roof_rise float 3 0 8
# gh-input: roof_drop float 4 0 10
# gh-input: env_div int 192 48 240
# gh-input: rings_f int 9 4 16
# gh-input: rings_r int 21 0 30
# gh-input: env_on int 1 0 3
# Rhomboid ETFE cushions on the envelope. The envelope runs from the plinth at env_z0 up the
# facade to the rim at env_h, bulging outwards by `bulge` at mid-height, and over the roof to its
# inner edge `cant` in from the rim (the surface the roof trusses follow). It is divided by env_div
# lines around and rings_f + rings_r rings; each cushion spans two rings and two divisions, so
# neighbouring rows are offset by half a cushion. env_on: 0 none, 1 facade, 2 roof, 3 both.
# Names EF04-117 (facade row 4) and ER12-033 (roof row 12). Stats: cushion count, ETFE area.
import math
import Rhino.Geometry as rg


def rim(th):
    c, s = math.cos(th), math.sin(th)
    return rg.Point3d(env_a * math.copysign(abs(c) ** (2 / env_p), c), env_b * math.copysign(abs(s) ** (2 / env_p), s), 0)


def point(i, j):
    th = 2 * math.pi * i / env_div
    p = rim(th)
    nf, nr = int(rings_f), int(rings_r)
    if j <= nf:
        t = j / float(nf)
        k = 1 + bulge * math.sin(math.pi * t)
        return rg.Point3d(p.X * k, p.Y * k, env_z0 + (env_h - env_z0) * t)
    w = (j - nf) / float(nr)
    r = math.hypot(p.X, p.Y)
    k = 1 - w * cant / r
    return rg.Point3d(p.X * k, p.Y * k, env_h + roof_rise * 4 * w * (1 - w) - roof_drop * w + 0.3)


a, names, floors, stats = [], [], [], []
n = int(env_div)
nf, nr = int(rings_f), int(rings_r)
on = int(env_on)
area = 0.0
for j in range(1, nf + nr):
    roof = j > nf
    if (roof and on not in (2, 3)) or (not roof and on not in (1, 3)):
        continue
    for i in range(n):
        if (i + j) % 2:
            continue
        q = [point(i, j - 1), point(i + 1, j), point(i, j + 1), point(i - 1, j)]
        srf = rg.Brep.CreateFromCornerPoints(q[0], q[1], q[2], q[3], 0.01)
        if srf:
            a.append(srf)
            names.append("%s%02d-%03d" % ("ER" if roof else "EF", (j - nf) if roof else j, i + 1))
            amp = rg.AreaMassProperties.Compute(srf)
            area += amp.Area if amp else 0.0
stats.append("ETFE cushions|n|%d" % len(a))
stats.append("ETFE area|m²|%d" % round(area))
