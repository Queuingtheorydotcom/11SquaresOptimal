"""Draw the known witness for documentation. Floating-point illustration only.
The exact construction is independently verified by the proof sources.
"""
from pathlib import Path

def witness():

    def f(u):
        return (((((((5 * u - 10) * u - 2) * u + 14) * u + 12) * u - 6) * u + 2) * u + 2) * u - 1
    lo, hi = (0.36, 0.37)
    for _ in range(64):
        mid = (lo + hi) / 2
        if f(mid) > 0:
            hi = mid
        else:
            lo = mid
    u = (lo + hi) / 2
    c = (1 - u * u) / (1 + u * u)
    s = 2 * u / (1 + u * u)
    T = (6 * u + 4) / (1 + 2 * u - u * u)
    r = 1 - (T - 3) * c
    a = ((1 + r) * c - 1) / s
    v = c - s
    w = (T - 1) / s - r - (3 + a) * c / s
    x = 1 + 2 / c - (T - 2) * s / c
    unit = ((0, 0), (1, 0), (1, 1), (0, 1))
    squares = [[(ox + dx, oy + dy) for dx, dy in unit] for ox, oy in [(0, 0), (T - 1, 0), (x, T - 1), (0, T - 1), (1, T - 1), (0, T - 2)]]
    for ox, oy in [(0, 0), (a, -1), (1, v), (a + 1, v - 1), (a + 2, -w)]:
        squares.append([(1 + c * (ox + dx) - s * (oy + dy - r), 1 + s * (ox + dx) + c * (oy + dy - r)) for dx, dy in unit])
    return (squares, T)

def main():
    squares, T = witness()
    size, margin = 500, 36
    def point(p):
        return f"{margin+p[0]*size/T:.5f},{margin+size-p[1]*size/T:.5f}"
    rows = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 572 600" role="img" aria-labelledby="title desc">',
            '<title id="title">Known optimal eleven-square packing</title>',
            '<desc id="desc">Six axis-aligned and five tilted congruent squares. Rounded illustration; exact coordinates are in the proof.</desc>',
            '<rect width="572" height="600" fill="#ffffff"/>']
    for i, square in enumerate(squares):
        color = '#dceef4' if i < 6 else '#f7dfad'
        coords = ' '.join(point(p) for p in square)
        rows.append(f'<polygon points="{coords}" fill="{color}" stroke="#244657" stroke-width="1.4"/>')
        x = margin + sum(p[0] for p in square)*size/T/4
        y = margin + size - sum(p[1] for p in square)*size/T/4
        rows.append(f'<text x="{x:.4f}" y="{y:.4f}" text-anchor="middle" dominant-baseline="middle" font-family="sans-serif" font-size="15" fill="#244657">{i}</text>')
    rows += ['<rect x="36" y="36" width="500" height="500" fill="none" stroke="#142c39" stroke-width="2"/>',
             '<text x="286" y="572" text-anchor="middle" font-family="sans-serif" font-size="18" fill="#142c39">T = 3.877083590022814…</text>', '</svg>']
    (Path(__file__).resolve().parents[1]/'docs/packing.svg').write_text('\n'.join(rows)+'\n')

if __name__ == '__main__':
    main()
