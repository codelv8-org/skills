// Web-ready head model preview for a React + React Three Fiber application.
// Install: npm install three @react-three/fiber @react-three/drei
// Copy your GLB to public/models/head_web_v01.glb.
import { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { Bounds, Center, Environment, Html, OrbitControls, useGLTF } from '@react-three/drei';
import * as THREE from 'three';

type HeadViewerProps = {
  url?: string;
  height?: number | string;
};

function Head({ url }: { url: string }) {
  const { scene } = useGLTF(url);
  return <primitive object={scene} />;
}

export default function HeadViewer({ url = '/models/head_web_v01.glb', height = 540 }: HeadViewerProps) {
  return (
    <div style={{ width: '100%', height, background: '#202329', borderRadius: 18, overflow: 'hidden' }}>
      <Canvas
        camera={{ position: [0, 0.08, 0.75], fov: 36, near: 0.01, far: 100 }}
        dpr={[1, 2]}
        gl={{ antialias: true, toneMapping: THREE.ACESFilmicToneMapping, outputColorSpace: THREE.SRGBColorSpace }}
      >
        <ambientLight intensity={0.28} />
        <directionalLight position={[3, 5, 4]} intensity={2} />
        <Suspense fallback={<Html center style={{ color: 'white' }}>Loading head…</Html>}>
          <Environment preset="studio" />
          <Bounds fit clip observe margin={1.25}>
            <Center>
              <Head url={url} />
            </Center>
          </Bounds>
        </Suspense>
        <OrbitControls makeDefault enablePan={false} minDistance={0.15} maxDistance={3} />
      </Canvas>
    </div>
  );
}
