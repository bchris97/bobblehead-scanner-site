# Hero logo layers

`logo-head.png` and `logo-body.png` are the app icon's bobblehead, split into
two transparent layers so the hero can bob the head on its spring.

Both are drawn on the same 475x696 canvas and are absolutely positioned in the
same box, so they line up when stacked. Only the head layer is animated; it
rotates about **49.3% / 49.1%**, which is the base of the spring. Those numbers
are baked into `.logo-head` in `index.html` — if the artwork changes, re-measure
rather than guessing.

## Regenerating

Source of truth is the app icon, `bobblehead-app/assets/icon.png` in the
`bobblehead-scanner` repo:

    python3 assets/split-logo.py

Standard library only, no Pillow or ImageMagick.

The script keys off two properties of the source art, both of which it would be
worth re-checking if the icon is ever redrawn:

- The figure is white on a flat blue field, so alpha is recovered per pixel from
  the red channel. Anti-aliased edges survive; a plain threshold would not.
- The head and cap are closed shapes ending at `y=440`, exactly where the spring
  coils start, so the split lands on the neck and leaves no seam. The baseball
  sits at `x<=358` and stays with the body.

The icon's own corner brackets are dropped (they are detected as the four
components parked in the corners) because the page draws its own scan frame.

## Encoding

The two layers are **colour type 4 (grey + alpha)** with **filter type 0 on
every row**, and both choices are load-bearing:

- The art is pure white, so only coverage varies. Grey+alpha is 2 bytes per
  pixel where RGBA needs 4.
- Fully transparent pixels are left as `0,0` rather than `255,0`. Empty regions
  then stay long runs of zeros, which is where the compression actually comes
  from. Filling grey everywhere costs ~4KB.
- **Filter 0, not adaptive.** The PNG spec's heuristic minimises delta
  magnitude, which breaks those runs. Benchmarked on the body layer: filter 0 =
  70,291 bytes, adaptive = 83,565, old RGBA+filter 0 = 79,539. Do not "improve"
  this to adaptive filtering.

# og-image.png

1200x630 social card, rendered from an HTML template in headless Chrome at that
exact window size. Referenced by absolute URL in `og:image` / `twitter:image` —
relative paths do not work for social scrapers.

# Favicons and touch icon

These live at the repo root because browsers and iOS expect them there.

| File | Source | Used at |
|------|--------|---------|
| `favicon.svg` | the nav glyph | any size, modern browsers |
| `favicon-32.png` | `favicon.svg` | 32px tab, retina |
| `favicon-16.png` | `favicon-16.svg` | 16px tab |
| `favicon.ico` | the two PNGs above | bare `/favicon.ico` probes |
| `apple-touch-icon.png` | the app icon, unmodified | 180px iOS home screen |

**The app logo is deliberately not used for the favicon.** Measured against the
source art, the median interior detail (jersey seams, glove laces, ball
stitches) is 14px on a 696px-tall figure, so it goes sub-pixel below roughly
50px of display height. A favicon renders at 16-32px, well under that, and the
detail turns to grey mush. The touch icon is 180px, which is comfortably above
the threshold, so that one *is* the real logo.

`favicon-16.svg` is a separate drawing rather than a scaled copy: at 16px the
nav glyph's outlined head and 1.5px strokes blur out, so the small version uses
integer-aligned 2px strokes and a solid head. Mass beats detail at that size.

To re-rasterise after changing either SVG, render it in headless Chrome at the
target size with a transparent canvas:

    chrome --headless --default-background-color=00000000 \
           --window-size=32,32 --screenshot=favicon-32.png page-wrapping-the-svg.html
