import { Suspense, useEffect, useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, useAnimations, useGLTF } from '@react-three/drei';
import { SkeletonUtils } from 'three-stdlib';

type CharacterViewerProps = {
  url: string;
  animationName?: string;
  height?: number;
  /** For GLB whose feet are at world Y=0 and height is approximately 1.7 m. */
  targetY?: number;
};

function CharacterAsset({ url, animationName }: Pick<CharacterViewerProps, 'url' | 'animationName'>) {
  const { scene, animations } = useGLTF(url);
  // Required when multiple instances use skinned meshes; avoid sharing bone transforms.
  const clone = useMemo(() => SkeletonUtils.clone(scene), [scene]);
  const { actions } = useAnimations(animations, clone);

  useEffect(() => {
    const action = animationName ? actions[animationName] : undefined;
    if (!action) return;
    action.reset().fadeIn(0.2).play();
    return () => { action.fadeOut(0.2); };
  }, [actions, animationName]);

  return <primitive object={clone} castShadow />;
}

/** Basic functional viewer, not a substitute for mobile/browser acceptance testing. */
export function CharacterViewer({
  url,
  animationName,
  height = 460,
  targetY = 0.9,
}: CharacterViewerProps) {
  return (
    <div style={{ width: '100%', height, overflow: 'hidden', borderRadius: 12 }}>
      <Canvas camera={{ position: [0, 1.25, 3.2], fov: 36, near: 0.02, far: 100 }} shadows>
        <color attach="background" args={['#e9eef0']} />
        <ambientLight intensity={0.95} />
        <directionalLight position={[3, 5, 4]} intensity={1.7} castShadow shadow-mapSize={[1024, 1024]} />
        <Suspense fallback={null}>
          <CharacterAsset url={url} animationName={animationName} />
        </Suspense>
        <mesh position={[0, -0.015, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
          <planeGeometry args={[12, 12]} />
          <meshStandardMaterial color="#dce3e6" roughness={0.95} />
        </mesh>
        <OrbitControls makeDefault target={[0, targetY, 0]} minDistance={1.5} maxDistance={12} />
      </Canvas>
    </div>
  );
}
