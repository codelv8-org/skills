# CharacterViewer.tsx

Simple React Three Fiber viewer for a glTF 2.0 GLB character. Works for a static blockout or a genuinely rigged asset with named clips.

Install in a React project:

```bash
npm install three @react-three/fiber @react-three/drei three-stdlib
```

Copy `CharacterViewer.tsx` into your React source directory and the actual GLB into `public/models/character.glb`. Use:

```tsx
import { CharacterViewer } from './CharacterViewer';

<CharacterViewer url="/models/character.glb" />
// Only when the GLB really has an animation named "Idle":
<CharacterViewer url="/models/rigged.glb" animationName="Idle" />
```

The starter assumes glTF Y-up, character face toward glTF +Z, feet near Y=0, approximately 1.7 m tall. Verify target/device and change camera/target for another scale. The procedural blockout generator writes the correct Y-up convention. `SkeletonUtils.clone` allows independent bone transforms per instance; still test performance with many instances and dispose GPU resources appropriately on unmount. This simple viewer intentionally omits Draco/Meshopt/KTX2 decoder setup: only load compressed assets after wiring matching decoders.

Do not claim animation or mobile/browser QA passes without playing the actual exported GLB in the target browser.
