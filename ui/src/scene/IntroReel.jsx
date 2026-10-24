import { useEffect, useLayoutEffect, useMemo, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Bloom, EffectComposer, Vignette } from '@react-three/postprocessing';
import { motion } from 'framer-motion';
import * as THREE from 'three';
import { Button } from '@/components/ui/button';

const ROWS = 26;
const COLS = 30;
const RUN_MS = 4800;
const UP = new THREE.Color('#2ee59d');
const DOWN = new THREE.Color('#ff4d6d');

// Seeded so every visit flies through the same market.
function rng(seed) {
  let s = seed;
  return () => (s = (s * 16807) % 2147483647) / 2147483647;
}

// A field of candles receding into the fog; the camera dollies down the aisle as they rise.
function CandleField() {
  const mesh = useRef(null);
  const candles = useMemo(() => {
    const rand = rng(42);
    const out = [];
    for (let row = 0; row < ROWS; row++) {
      for (let col = 0; col < COLS; col++) {
        const up = rand() > 0.44;
        out.push({
          x: (col - COLS / 2) * 0.62 + (rand() - 0.5) * 0.2,
          z: -row * 1.5,
          h: 0.6 + rand() * 2.2 + row * 0.08,
          delay: rand() * 0.7 + row * 0.05,
          up,
        });
      }
    }
    return out;
  }, []);
  const dummy = useMemo(() => new THREE.Object3D(), []);

  useLayoutEffect(() => {
    candles.forEach((c, i) => mesh.current.setColorAt(i, c.up ? UP : DOWN));
    mesh.current.instanceColor.needsUpdate = true;
  }, [candles]);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    const cam = state.camera;
    cam.position.z = THREE.MathUtils.lerp(10, -22, THREE.MathUtils.smoothstep(t, 0.3, RUN_MS / 1000));
    cam.position.y = 3.4 - THREE.MathUtils.smoothstep(t, 0, 4) * 1.6;
    cam.lookAt(0, 0.6, cam.position.z - 14);

    candles.forEach((c, i) => {
      const grow = THREE.MathUtils.smoothstep(t - c.delay, 0, 1.1);
      dummy.position.set(c.x, (c.h * grow) / 2, c.z);
      dummy.scale.set(0.34, Math.max(0.001, c.h * grow), 0.34);
      dummy.updateMatrix();
      mesh.current.setMatrixAt(i, dummy.matrix);
    });
    mesh.current.instanceMatrix.needsUpdate = true;
  });

  return (
    <instancedMesh ref={mesh} args={[null, null, candles.length]}>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial roughness={0.45} metalness={0.05} />
    </instancedMesh>
  );
}

export default function IntroReel({ onDone }) {
  useEffect(() => {
    const timer = setTimeout(onDone, RUN_MS);
    return () => clearTimeout(timer);
  }, [onDone]);

  return (
    <motion.div
      className="fixed inset-0 z-50 bg-background"
      initial={{ opacity: 1 }}
      exit={{ opacity: 0, transition: { duration: 0.7, ease: 'easeInOut' } }}
    >
      <Canvas camera={{ position: [0, 3.4, 10], fov: 56, near: 0.1, far: 90 }} dpr={[1, 1.75]} aria-hidden="true">
        <color attach="background" args={['#07080a']} />
        <fog attach="fog" args={['#07080a', 4, 34]} />
        <ambientLight intensity={0.35} />
        <pointLight position={[0, 9, 4]} intensity={60} color="#5ce1ff" />
        <CandleField />
        <EffectComposer>
          <Bloom intensity={0.45} luminanceThreshold={0.75} luminanceSmoothing={0.2} mipmapBlur />
          <Vignette offset={0.25} darkness={0.9} />
        </EffectComposer>
      </Canvas>

      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center gap-5 px-6 text-center">
        <motion.p
          className="font-mono text-xs uppercase tracking-[0.3em] text-accent"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.2, duration: 0.6 }}
        >
          Live GMGN evidence · one scoring agent
        </motion.p>
        <motion.h1
          className="font-display text-4xl leading-[1.05] font-semibold tracking-tight sm:text-6xl md:text-7xl"
          initial={{ opacity: 0, y: 24, filter: 'blur(12px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          transition={{ delay: 1.5, duration: 1.1, ease: [0.2, 0.7, 0.2, 1] }}
        >
          Memecoin
          <br />
          Research Desk
        </motion.h1>
      </div>

      <Button
        variant="ghost"
        size="sm"
        onClick={onDone}
        className="absolute right-5 bottom-5 border border-border/70 bg-background/60 backdrop-blur"
      >
        Skip intro
      </Button>
    </motion.div>
  );
}
