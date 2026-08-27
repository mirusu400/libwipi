# Image Pipeline

This WIPI-C example exercises offscreen framebuffers, context mutation, RGB
pixel upload and readback, framebuffer copying, image decoding, image drawing,
and repaint presentation. Its embedded 1 by 1 GIF is an original synthetic
fixture and contains no commercial asset.

Press any direction or OK to rebuild the offscreen pattern and redraw it.

Build and inspect it from the repository root:

```powershell
docker run --rm -v "${PWD}:/work" -w /work libwipi-toolchain `
  make -C examples/image-pipeline clean package inspect
```

The current package target is explicitly
`1.2.1/lgt-raptor/aram-wie-raptor`.
