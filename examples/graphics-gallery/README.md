# Graphics Gallery

This standalone WIPI-C example presents three pages of drawing operations. It
demonstrates pixels, lines, outlined and filled rectangles, arcs, RGB color
conversion, font metrics, string measurement, text, framebuffer access, and
LCD flushing.

Use Left and Right, keypad 4 and 6, or OK to change pages.

Build and inspect the package from the repository root:

```powershell
docker run --rm -v "${PWD}:/work" -w /work libwipi-toolchain `
  make -C examples/graphics-gallery clean package inspect
```

The source is profile independent application code. The current package
target is explicitly `1.2.1/lgt-raptor/aram-wie-raptor`.
