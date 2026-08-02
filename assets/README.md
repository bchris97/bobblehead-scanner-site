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
