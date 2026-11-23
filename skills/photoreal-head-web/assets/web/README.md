# React Three Fiber head viewer

1. Install `three`, `@react-three/fiber`, and `@react-three/drei` in the existing React project.
2. Copy `HeadViewer.tsx` to the app's components folder.
3. Place the exported file in `public/models/head_web_v01.glb`.
4. Render `<HeadViewer url="/models/head_web_v01.glb" />`.
5. Test the asset's true scale, UV normals, skin roughness, eyebrow transparency, mobile loading, and orbit focus in browser. The template is a starting point, not proof that the model is production-ready.
6. If the GLB uses Draco, Meshopt, or KTX2, configure compatible decoders in the loading stack first, or export a standard uncompressed GLB.
