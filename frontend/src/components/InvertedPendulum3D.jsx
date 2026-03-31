/**
 * InvertedPendulum3D — Three.js 3D visualization of cart-pendulum system.
 *
 * Receives pre-computed trajectory arrays from the backend and animates them
 * at 60fps with frame interpolation.
 *
 * Props:
 *   animation: { t, cart_x, theta, control_force, dt, num_frames, pend_length, is_stable }
 *   isStable: boolean
 */

import React, { useRef, useEffect, useCallback, useState, useMemo } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass';

const lerp = (a, b, t) => a + (b - a) * t;
const SPEED_OPTIONS = [0.5, 1, 2, 4];
const TRAIL_LENGTH = 30;

function InvertedPendulum3D({ animation, isStable }) {
  const containerRef = useRef(null);
  const rendererRef = useRef(null);
  const composerRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const controlsRef = useRef(null);
  const clockRef = useRef(new THREE.Clock());
  const objectsRef = useRef({});
  const trailRef = useRef([]);
  const physicsRef = useRef({ velNorm: 0 });

  const frameRef = useRef(0);
  const lastFrameTimeRef = useRef(0);
  const playingRef = useRef(true);
  const speedRef = useRef(1);

  const [isPlaying, setIsPlaying] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);
  const [speed, setSpeed] = useState(1);

  useEffect(() => { playingRef.current = isPlaying; }, [isPlaying]);
  useEffect(() => { speedRef.current = speed; }, [speed]);

  const COLORS = useMemo(() => ({
    cart: 0x3b82f6,
    cartEmissive: 0x2563eb,
    rail: 0x64748b,
    railEmissive: 0x475569,
    pendulum: 0x3b82f6,
    pendEmissive: 0x2563eb,
    bob: 0xf97316,
    bobEmissive: 0xea580c,
    bobStable: 0x10b981,
    bobUnstable: 0xef4444,
    pivot: 0xffffff,
    force: 0xa855f7,
    ground: 0x080e1a,
    gridMain: 0x334155,
    gridSecondary: 0x1a2744,
    background: 0x060c18,
    trailStart: 0x3b82f6,
    trailMid: 0x8b5cf6,
    trailEnd: 0xf97316,
  }), []);

  // Scale factors
  const CART_SCALE = 0.8;
  const RAIL_HALF = 2.5;
  const CART_Y = 0.15;

  const initScene = useCallback(() => {
    if (!containerRef.current) return;
    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(COLORS.background);
    scene.fog = new THREE.Fog(COLORS.background, 8, 20);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(40, width / height, 0.01, 100);
    camera.position.set(2.5, 1.8, 2.5);
    camera.lookAt(0, 0.6, 0);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({
      antialias: true, alpha: true, powerPreference: 'high-performance',
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.3;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    containerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Post-processing: bloom
    const composer = new EffectComposer(renderer);
    composer.addPass(new RenderPass(scene, camera));
    const bloomPass = new UnrealBloomPass(
      new THREE.Vector2(width, height), 0.2, 0.3, 0.85
    );
    composer.addPass(bloomPass);
    composer.addPass(new OutputPass());
    composerRef.current = composer;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.rotateSpeed = 0.5;
    controls.zoomSpeed = 0.8;
    controls.minDistance = 1.0;
    controls.maxDistance = 6.0;
    controls.maxPolarAngle = Math.PI * 0.85;
    controls.target.set(0, 0.5, 0);
    controls.update();
    controlsRef.current = controls;

    setupLighting(scene);
    setupEnvironment(scene);
    buildSystem(scene);
    createTrailObjects(scene);

    const onResize = () => {
      if (!containerRef.current) return;
      const w = containerRef.current.clientWidth;
      const h = containerRef.current.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
      composer.setSize(w, h);
    };
    const resizeObs = new ResizeObserver(onResize);
    resizeObs.observe(containerRef.current);

    clockRef.current.start();
    let animId;
    const renderLoop = () => {
      controls.update();
      updateGlowEffects(clockRef.current.getElapsedTime());
      composer.render();
      animId = requestAnimationFrame(renderLoop);
    };
    animId = requestAnimationFrame(renderLoop);

    return () => {
      cancelAnimationFrame(animId);
      resizeObs.disconnect();
      if (controlsRef.current) {
        controlsRef.current.dispose();
        controlsRef.current = null;
      }
      composer.dispose();
      renderer.dispose();
      scene.traverse((obj) => {
        if (obj.geometry) obj.geometry.dispose();
        if (obj.material) {
          if (Array.isArray(obj.material)) obj.material.forEach(m => m.dispose());
          else obj.material.dispose();
        }
      });
      if (containerRef.current && renderer.domElement.parentNode === containerRef.current) {
        containerRef.current.removeChild(renderer.domElement);
      }
    };
  }, [COLORS]);

  const setupLighting = (scene) => {
    scene.add(new THREE.AmbientLight(0xffffff, 0.35));
    scene.add(new THREE.HemisphereLight(0xb0d0ff, 0x404040, 0.25));

    const key = new THREE.DirectionalLight(0xffffff, 1.0);
    key.position.set(3, 6, 4);
    key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048);
    key.shadow.camera.near = 0.1;
    key.shadow.camera.far = 20;
    key.shadow.camera.left = -3;
    key.shadow.camera.right = 3;
    key.shadow.camera.top = 3;
    key.shadow.camera.bottom = -1;
    key.shadow.bias = -0.0003;
    scene.add(key);

    const fill = new THREE.DirectionalLight(0xfff5e6, 0.3);
    fill.position.set(-4, 2, 2);
    scene.add(fill);
  };

  const setupEnvironment = (scene) => {
    const groundGeo = new THREE.PlaneGeometry(8, 8);
    const groundMat = new THREE.MeshStandardMaterial({
      color: COLORS.ground, roughness: 0.85, metalness: 0.15,
    });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = 0;
    ground.receiveShadow = true;
    scene.add(ground);

    // Grid
    const gridGroup = new THREE.Group();
    gridGroup.position.y = 0.001;
    for (let i = -4; i <= 4; i++) {
      const pts = [new THREE.Vector3(i * 0.5, 0, -4), new THREE.Vector3(i * 0.5, 0, 4)];
      const geo = new THREE.BufferGeometry().setFromPoints(pts);
      const mat = new THREE.LineBasicMaterial({
        color: i === 0 ? COLORS.gridMain : COLORS.gridSecondary,
        transparent: true, opacity: i === 0 ? 0.3 : 0.1,
      });
      gridGroup.add(new THREE.Line(geo, mat));
    }
    for (let i = -4; i <= 4; i++) {
      const pts = [new THREE.Vector3(-4, 0, i * 0.5), new THREE.Vector3(4, 0, i * 0.5)];
      const geo = new THREE.BufferGeometry().setFromPoints(pts);
      const mat = new THREE.LineBasicMaterial({
        color: COLORS.gridSecondary, transparent: true, opacity: 0.08,
      });
      gridGroup.add(new THREE.Line(geo, mat));
    }
    scene.add(gridGroup);
  };

  const buildSystem = (scene) => {
    const obj = objectsRef.current;

    // Rail
    const railGeo = new THREE.BoxGeometry(RAIL_HALF * 2, 0.02, 0.06);
    const railMat = new THREE.MeshStandardMaterial({
      color: COLORS.rail, emissive: COLORS.railEmissive, emissiveIntensity: 0.05,
      roughness: 0.2, metalness: 0.9,
    });
    const rail = new THREE.Mesh(railGeo, railMat);
    rail.position.y = CART_Y - 0.06;
    rail.castShadow = true;
    scene.add(rail);

    // Rail end caps
    const capGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.08, 12);
    const capMat = new THREE.MeshStandardMaterial({
      color: 0x64748b, emissive: 0x475569, emissiveIntensity: 0.15,
      roughness: 0.1, metalness: 0.8,
    });
    [-RAIL_HALF, RAIL_HALF].forEach(xPos => {
      const cap = new THREE.Mesh(capGeo, capMat);
      cap.position.set(xPos, CART_Y - 0.06, 0);
      cap.rotation.x = Math.PI / 2;
      scene.add(cap);
    });

    // Cart group (moves along x)
    const cartGroup = new THREE.Group();
    cartGroup.position.y = CART_Y;
    scene.add(cartGroup);
    obj.cartGroup = cartGroup;

    // Cart body
    const cartGeo = new THREE.BoxGeometry(0.3, 0.12, 0.2);
    const cartMat = new THREE.MeshStandardMaterial({
      color: COLORS.cart, emissive: COLORS.cartEmissive, emissiveIntensity: 0.1,
      roughness: 0.1, metalness: 0.6,
    });
    const cart = new THREE.Mesh(cartGeo, cartMat);
    cart.castShadow = true;
    cartGroup.add(cart);
    obj.cartMat = cartMat;

    // Cart wireframe
    const cartEdgeGeo = new THREE.EdgesGeometry(cartGeo);
    const cartEdgeMat = new THREE.LineBasicMaterial({
      color: 0x60a5fa, transparent: true, opacity: 0.4,
    });
    cart.add(new THREE.LineSegments(cartEdgeGeo, cartEdgeMat));

    // Wheels
    const wheelGeo = new THREE.CylinderGeometry(0.025, 0.025, 0.22, 16);
    const wheelMat = new THREE.MeshStandardMaterial({
      color: 0xc0c0c0, roughness: 0.15, metalness: 0.95,
    });
    [-0.1, 0.1].forEach(xOff => {
      const wheel = new THREE.Mesh(wheelGeo, wheelMat);
      wheel.rotation.x = Math.PI / 2;
      wheel.position.set(xOff, -0.06, 0);
      cartGroup.add(wheel);
    });

    // Pivot point (on top of cart)
    const pivotGeo = new THREE.SphereGeometry(0.02, 16, 16);
    const pivotMat = new THREE.MeshStandardMaterial({
      color: COLORS.pivot, emissive: 0xffffff, emissiveIntensity: 0.25,
      roughness: 0.05, metalness: 1.0,
    });
    const pivot = new THREE.Mesh(pivotGeo, pivotMat);
    pivot.position.y = 0.06;
    cartGroup.add(pivot);

    // Pendulum group (rotates around pivot)
    const pendGroup = new THREE.Group();
    pendGroup.position.y = 0.06;
    cartGroup.add(pendGroup);
    obj.pendGroup = pendGroup;

    // Pendulum rod
    const pendLength = animation?.pend_length || 0.5;
    const rodGeo = new THREE.CylinderGeometry(0.008, 0.008, pendLength, 12);
    const rodMat = new THREE.MeshStandardMaterial({
      color: COLORS.pendulum, emissive: COLORS.pendEmissive, emissiveIntensity: 0.15,
      roughness: 0.12, metalness: 0.6,
    });
    const rod = new THREE.Mesh(rodGeo, rodMat);
    rod.position.y = pendLength / 2;
    rod.castShadow = true;
    pendGroup.add(rod);
    obj.rod = rod;
    obj.rodMat = rodMat;

    // Bob (mass at end)
    const bobGeo = new THREE.SphereGeometry(0.04, 24, 24);
    const bobMat = new THREE.MeshStandardMaterial({
      color: COLORS.bob, emissive: COLORS.bobEmissive, emissiveIntensity: 0.2,
      roughness: 0.08, metalness: 0.5,
    });
    const bob = new THREE.Mesh(bobGeo, bobMat);
    bob.position.y = pendLength;
    bob.castShadow = true;
    pendGroup.add(bob);
    obj.bob = bob;
    obj.bobMat = bobMat;

    // Bob glow
    const bobGlowGeo = new THREE.SphereGeometry(0.06, 16, 16);
    const bobGlowMat = new THREE.MeshBasicMaterial({
      color: COLORS.bob, transparent: true, opacity: 0.2,
    });
    const bobGlow = new THREE.Mesh(bobGlowGeo, bobGlowMat);
    bob.add(bobGlow);
    obj.bobGlowMat = bobGlowMat;

    // Dynamic point light following bob
    const bobLight = new THREE.PointLight(0xff8800, 0.15, 1.5);
    pendGroup.add(bobLight);
    obj.bobLight = bobLight;

    // Force arrow (shows control input direction)
    const arrowGeo = new THREE.ConeGeometry(0.02, 0.08, 8);
    const arrowMat = new THREE.MeshBasicMaterial({
      color: COLORS.force, transparent: true, opacity: 0.8,
    });
    const forceArrow = new THREE.Mesh(arrowGeo, arrowMat);
    forceArrow.rotation.z = -Math.PI / 2;
    forceArrow.position.set(0.25, 0, 0);
    forceArrow.visible = false;
    cartGroup.add(forceArrow);
    obj.forceArrow = forceArrow;
    obj.forceArrowMat = arrowMat;
  };

  const createTrailObjects = (scene) => {
    const obj = objectsRef.current;
    const trailGroup = new THREE.Group();
    const trails = [];

    for (let i = 0; i < TRAIL_LENGTH; i++) {
      const t = i / TRAIL_LENGTH;
      const size = 0.012 * (1 - t * 0.5);
      const opacity = 0.7 * Math.pow(1 - t, 0.7);

      const color = new THREE.Color();
      if (t < 0.5) {
        color.setHex(COLORS.trailStart);
        color.lerp(new THREE.Color(COLORS.trailMid), t * 2);
      } else {
        color.setHex(COLORS.trailMid);
        color.lerp(new THREE.Color(COLORS.trailEnd), (t - 0.5) * 2);
      }

      const geo = new THREE.SphereGeometry(size, 8, 8);
      const mat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.visible = false;
      trailGroup.add(mesh);
      trails.push({ mesh, position: new THREE.Vector3(), active: false, baseOpacity: opacity });
    }
    scene.add(trailGroup);
    obj.trails = trails;
  };

  const updateGlowEffects = (elapsed) => {
    const obj = objectsRef.current;
    const vel = physicsRef.current.velNorm || 0;

    if (obj.bobGlowMat) {
      obj.bobGlowMat.opacity = 0.05 + vel * 0.08 + Math.sin(elapsed * 5) * 0.02;
    }
    if (obj.bobMat) {
      const color = new THREE.Color(COLORS.bob);
      if (vel > 0.5) color.lerp(new THREE.Color(0xef4444), (vel - 0.5) * 2);
      else if (vel < 0.1) color.lerp(new THREE.Color(0x10b981), (0.1 - vel) * 10);
      obj.bobMat.color.copy(color);
      obj.bobMat.emissiveIntensity = 0.15 + vel * 0.1;
    }
    if (obj.bobLight) {
      obj.bobLight.intensity = 0.05 + vel * 0.1;
    }
    if (obj.rodMat) {
      obj.rodMat.emissiveIntensity = 0.1 + vel * 0.05;
    }
  };

  const updatePositions = useCallback((anim, frameIdx) => {
    const obj = objectsRef.current;
    if (!obj.cartGroup || !obj.pendGroup || !anim) return;

    const idx = Math.min(frameIdx, anim.num_frames - 1);
    const cartX = (anim.cart_x[idx] || 0) * CART_SCALE;
    const theta = anim.theta[idx] || Math.PI;
    const force = anim.control_force[idx] || 0;
    const pendLength = anim.pend_length || 0.5;

    // Cart position along x
    obj.cartGroup.position.x = Math.max(-RAIL_HALF + 0.15, Math.min(RAIL_HALF - 0.15, cartX));

    // Pendulum angle: theta is measured from downward vertical, π = upright.
    // In 3D: rotation around z-axis. θ=π means rod points up.
    // Convert: visual angle from upright = theta - π
    const visualAngle = theta - Math.PI;
    obj.pendGroup.rotation.z = -visualAngle;

    // Update rod and bob positions (in case pendulum length changed)
    if (obj.rod) obj.rod.position.y = pendLength / 2;
    if (obj.bob) obj.bob.position.y = pendLength;
    if (obj.bobLight) obj.bobLight.position.y = pendLength;

    // Force arrow
    if (obj.forceArrow) {
      const maxForce = 50;
      const normForce = Math.abs(force) / maxForce;
      if (normForce > 0.01) {
        obj.forceArrow.visible = true;
        const dir = force > 0 ? 1 : -1;
        obj.forceArrow.position.x = dir * (0.2 + normForce * 0.15);
        obj.forceArrow.rotation.z = dir > 0 ? -Math.PI / 2 : Math.PI / 2;
        obj.forceArrow.scale.setScalar(0.5 + normForce * 1.5);
        if (obj.forceArrowMat) obj.forceArrowMat.opacity = 0.3 + normForce * 0.7;
      } else {
        obj.forceArrow.visible = false;
      }
    }

    // Velocity for glow effects
    if (idx > 0 && idx < anim.num_frames) {
      const prevTheta = anim.theta[idx - 1] || Math.PI;
      const angVel = Math.abs(theta - prevTheta) / (anim.dt || 0.02);
      physicsRef.current.velNorm = Math.min(1, angVel / 5);
    }

    // Bob world position for trail
    const bobWorldX = cartX + pendLength * Math.sin(visualAngle);
    const bobWorldY = CART_Y + 0.06 + pendLength * Math.cos(visualAngle);

    // Trail
    if (obj.trails) {
      for (let i = TRAIL_LENGTH - 1; i > 0; i--) {
        obj.trails[i].position.copy(obj.trails[i - 1].position);
        obj.trails[i].active = obj.trails[i - 1].active;
      }
      obj.trails[0].position.set(bobWorldX, bobWorldY, 0);
      obj.trails[0].active = true;

      const opBoost = 0.5 + (physicsRef.current.velNorm || 0) * 0.5;
      for (let i = 0; i < TRAIL_LENGTH; i++) {
        const trail = obj.trails[i];
        trail.mesh.visible = trail.active && i > 0;
        if (trail.active) {
          trail.mesh.position.copy(trail.position);
          trail.mesh.material.opacity = trail.baseOpacity * opBoost;
        }
      }
    }
  }, [COLORS]);

  // Init scene
  useEffect(() => {
    const cleanup = initScene();
    return cleanup;
  }, [initScene]);

  // Animation loop
  useEffect(() => {
    if (!animation || animation.num_frames < 2) return;

    const frameDt = (animation.dt || 0.02) * 1000;
    lastFrameTimeRef.current = performance.now();
    let animId;

    const loop = (ts) => {
      if (playingRef.current) {
        const elapsed = ts - lastFrameTimeRef.current;
        const adjusted = frameDt / speedRef.current;
        if (elapsed >= adjusted) {
          lastFrameTimeRef.current = ts;
          frameRef.current = (frameRef.current + 1) % animation.num_frames;
          setCurrentTime(animation.t[frameRef.current] || 0);
        }
      }
      updatePositions(animation, frameRef.current);
      animId = requestAnimationFrame(loop);
    };

    animId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animId);
  }, [animation, updatePositions]);

  // Reset on data change
  useEffect(() => {
    frameRef.current = 0;
    lastFrameTimeRef.current = performance.now();
    if (objectsRef.current.trails) {
      objectsRef.current.trails.forEach(t => { t.active = false; t.mesh.visible = false; });
    }
    setCurrentTime(0);
    setIsPlaying(true);
  }, [animation]);

  const togglePlay = () => setIsPlaying(p => !p);
  const restart = () => {
    frameRef.current = 0;
    lastFrameTimeRef.current = performance.now();
    if (objectsRef.current.trails) {
      objectsRef.current.trails.forEach(t => { t.active = false; t.mesh.visible = false; });
    }
    setCurrentTime(0);
  };
  const cycleSpeed = () => {
    setSpeed(s => {
      const i = SPEED_OPTIONS.indexOf(s);
      return SPEED_OPTIONS[(i + 1) % SPEED_OPTIONS.length];
    });
  };

  return (
    <div className="ip3d-animation-panel">
      <div ref={containerRef} className="ip3d-canvas-3d">
        <div className="ip3d-3d-hint">
          Drag to rotate &middot; Scroll to zoom
        </div>
      </div>
      <div className="ip3d-animation-controls">
        <button className="ip3d-ctrl-btn" onClick={togglePlay} title={isPlaying ? 'Pause' : 'Play'}>
          {isPlaying ? '\u23F8' : '\u25B6'}
        </button>
        <button className="ip3d-ctrl-btn" onClick={restart} title="Restart">
          {'\u21BA'}
        </button>
        <button className="ip3d-ctrl-btn ip3d-speed-btn" onClick={cycleSpeed} title="Speed">
          {speed}&times;
        </button>
        <span className="ip3d-time-label">
          {currentTime.toFixed(2)} / {animation?.t?.[animation.num_frames - 1]?.toFixed(1) ?? '?'} s
        </span>
        <span className={`ip3d-stability-badge ${isStable ? 'stable' : 'unstable'}`}>
          {isStable ? 'STABLE' : 'UNSTABLE'}
        </span>
      </div>
    </div>
  );
}

export default InvertedPendulum3D;
