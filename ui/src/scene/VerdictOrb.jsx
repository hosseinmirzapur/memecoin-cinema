import { useMemo, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { useReducedMotion } from 'framer-motion';
import * as THREE from 'three';

const SEGMENTS = 72;
const DIM = new THREE.Color('#1d232d');
const TONE = { ape: '#2ee59d', reject: '#ff4d6d', wait: '#ffb020' };

// A ring of segments fills to the score, in the verdict's colour. Lit segments ease in one by one.
// The ring stays still so the lit arc always reads against the 0 and 100 marks.
function Ring({ score, tone, still }) {
  const mesh = useRef(null);
  const core = useRef(null);
  const dummy = useMemo(() => new THREE.Object3D(), []);
  const color = useMemo(() => new THREE.Color(), []);
  const toneColor = useMemo(() => new THREE.Color(TONE[tone]), [tone]);
  const lit = useMemo(() => new Float32Array(SEGMENTS), []);
  const litTarget = Math.round((score / 100) * SEGMENTS);

  useFrame((_, dt) => {
    for (let i = 0; i < SEGMENTS; i++) {
      const target = i < litTarget ? 1 : 0;
      lit[i] += (target - lit[i]) * (still ? 1 : Math.min(1, dt * 6));
      const angle = (i / SEGMENTS) * Math.PI * 2 - Math.PI / 2;
      const r = 1.45 + lit[i] * 0.08;
      dummy.position.set(Math.cos(angle) * r, Math.sin(angle) * r, 0);
      dummy.rotation.set(0, 0, angle + Math.PI / 2);
      dummy.scale.set(0.09, 0.26 + lit[i] * 0.12, 0.05);
      dummy.updateMatrix();
      mesh.current.setMatrixAt(i, dummy.matrix);
      mesh.current.setColorAt(i, color.copy(DIM).lerp(toneColor, lit[i]));
    }
    mesh.current.instanceMatrix.needsUpdate = true;
    mesh.current.instanceColor.needsUpdate = true;
    if (!still) {
      core.current.rotation.y += dt * 0.5;
      core.current.rotation.x += dt * 0.2;
    }
  });

  return (
    <>
      <instancedMesh ref={mesh} args={[null, null, SEGMENTS]}>
        <boxGeometry args={[1, 1, 1]} />
        <meshBasicMaterial toneMapped={false} />
      </instancedMesh>
      <mesh ref={core}>
        <icosahedronGeometry args={[0.3, 1]} />
        <meshBasicMaterial color={toneColor} wireframe transparent opacity={0.4} toneMapped={false} />
      </mesh>
    </>
  );
}

export default function VerdictOrb({ score, tone = 'wait' }) {
  const still = useReducedMotion() === true;
  return (
    <div className="aspect-square w-full max-w-[260px]" role="img" aria-label={`Safety score ${score} of 100`}>
      <Canvas camera={{ position: [0, 0, 4.4], fov: 40 }} dpr={[1, 2]}>
        <Ring score={score} tone={tone} still={still} />
      </Canvas>
    </div>
  );
}
