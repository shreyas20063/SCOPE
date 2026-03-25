/**
 * BallBeam3D — Three.js 3D visualization of ball-and-beam system.
 *
 * Receives pre-computed trajectory arrays from the backend and animates them
 * at 60fps with frame interpolation. Matches the neon aesthetic of existing
 * 3D components (InvertedPendulum3D, FurutaPendulum3D).
 *
 * Props:
 *   animation: { t, ball_r, beam_alpha, control_torque, dt, num_frames, beam_length, ball_radius, is_stable }
 *   isStable: boolean
 */

import React, { useRef, useEffect, useCallback, useState, useMemo } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

const SPEED_OPTIONS = [0.5, 1, 2, 4];
const TRAIL_LENGTH = 30;

function BallBeam3D({ animation, isStable }) {
  const containerRef = useRef(null);
  const rendererRef = useRef(null);
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
    beam: 0x22d3ee,
    beamEmissive: 0x06b6d4,
    ball: 0xff6600,
    ballEmissive: 0xff4400,
    ballStable: 0x10b981,
    ballUnstable: 0xef4444,
    pivot: 0xffffff,
    torque: 0xf472b6,
    support: 0x64748b,
    supportEmissive: 0x475569,
    ground: 0x080e1a,
    gridMain: 0x00ffff,
    gridSecondary: 0x1a2744,
    background: 0x060c18,
    trailStart: 0x00ffff,
    trailMid: 0xff00ff,
    trailEnd: 0xff6600,
  }), []);

  // Scale factors
  const BEAM_Y = 0.6;  // pivot height above ground

  const initScene = useCallback(() => {
    if (!containerRef.current) return;
    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(COLORS.background);
    scene.fog = new THREE.Fog(COLORS.background, 5, 12);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(40, width / height, 0.01, 100);
    camera.position.set(2.0, 1.5, 2.5);
    camera.lookAt(0, 0.5, 0);
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
    };
    const resizeObs = new ResizeObserver(onResize);
    resizeObs.observe(containerRef.current);

    clockRef.current.start();
    let animId;
    const renderLoop = () => {
      controls.update();
      updateGlowEffects(clockRef.current.getElapsedTime());
      renderer.render(scene, camera);
      animId = requestAnimationFrame(renderLoop);
    };
    animId = requestAnimationFrame(renderLoop);

    return () => {
      cancelAnimationFrame(animId);
      resizeObs.disconnect();
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
    scene.add(new THREE.AmbientLight(0xffffff, 0.15));
    scene.add(new THREE.HemisphereLight(0x0066ff, 0xff0066, 0.2));

    const key = new THREE.DirectionalLight(0xffffff, 1.5);
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

    const cyan = new THREE.DirectionalLight(0x00ffff, 0.6);
    cyan.position.set(-4, 2, 2);
    scene.add(cyan);

    const magenta = new THREE.DirectionalLight(0xff00ff, 0.35);
    magenta.position.set(4, 2, -2);
    scene.add(magenta);
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
    const beamLen = animation?.beam_length || 1.0;
    const ballRad = animation?.ball_radius || 0.015;

    // Pivot support (vertical pillar)
    const supportGeo = new THREE.CylinderGeometry(0.03, 0.04, BEAM_Y, 12);
    const supportMat = new THREE.MeshStandardMaterial({
      color: COLORS.support, emissive: COLORS.supportEmissive, emissiveIntensity: 0.2,
      roughness: 0.2, metalness: 0.9,
    });
    const support = new THREE.Mesh(supportGeo, supportMat);
    support.position.y = BEAM_Y / 2;
    support.castShadow = true;
    scene.add(support);

    // Pivot point (bright sphere at top of support)
    const pivotGeo = new THREE.SphereGeometry(0.025, 16, 16);
    const pivotMat = new THREE.MeshStandardMaterial({
      color: COLORS.pivot, emissive: 0x00ffff, emissiveIntensity: 0.8,
      roughness: 0.05, metalness: 1.0,
    });
    const pivot = new THREE.Mesh(pivotGeo, pivotMat);
    pivot.position.y = BEAM_Y;
    scene.add(pivot);

    // Beam group (rotates around pivot)
    const beamGroup = new THREE.Group();
    beamGroup.position.y = BEAM_Y;
    scene.add(beamGroup);
    obj.beamGroup = beamGroup;

    // Beam body (long rectangular bar)
    const beamGeo = new THREE.BoxGeometry(beamLen, 0.025, 0.08);
    const beamMat = new THREE.MeshStandardMaterial({
      color: COLORS.beam, emissive: COLORS.beamEmissive, emissiveIntensity: 0.4,
      roughness: 0.12, metalness: 0.6,
    });
    const beam = new THREE.Mesh(beamGeo, beamMat);
    beam.castShadow = true;
    beamGroup.add(beam);
    obj.beam = beam;
    obj.beamMat = beamMat;

    // Beam wireframe
    const beamEdgeGeo = new THREE.EdgesGeometry(beamGeo);
    const beamEdgeMat = new THREE.LineBasicMaterial({
      color: 0x67e8f9, transparent: true, opacity: 0.4,
    });
    beam.add(new THREE.LineSegments(beamEdgeGeo, beamEdgeMat));

    // Beam end caps (glowing markers)
    const capGeo = new THREE.CylinderGeometry(0.02, 0.02, 0.09, 12);
    const capMat = new THREE.MeshStandardMaterial({
      color: 0x00ffff, emissive: 0x00ffff, emissiveIntensity: 0.5,
      roughness: 0.1, metalness: 0.8,
    });
    [-beamLen / 2, beamLen / 2].forEach(xPos => {
      const cap = new THREE.Mesh(capGeo, capMat);
      cap.position.set(xPos, 0, 0);
      cap.rotation.x = Math.PI / 2;
      beamGroup.add(cap);
    });

    // Track groove on top of beam (ball rolls on this)
    const grooveGeo = new THREE.BoxGeometry(beamLen - 0.04, 0.006, 0.025);
    const grooveMat = new THREE.MeshStandardMaterial({
      color: 0x1e293b, roughness: 0.3, metalness: 0.5,
    });
    const groove = new THREE.Mesh(grooveGeo, grooveMat);
    groove.position.y = 0.0125 + 0.003;
    beamGroup.add(groove);

    // Ball (sphere that slides along beam)
    const displayBallRad = Math.max(ballRad * 2, 0.03);  // scale up for visibility
    const ballGeo = new THREE.SphereGeometry(displayBallRad, 24, 24);
    const ballMat = new THREE.MeshStandardMaterial({
      color: COLORS.ball, emissive: COLORS.ballEmissive, emissiveIntensity: 0.7,
      roughness: 0.08, metalness: 0.5,
    });
    const ball = new THREE.Mesh(ballGeo, ballMat);
    ball.position.y = 0.0125 + displayBallRad;
    ball.castShadow = true;
    beamGroup.add(ball);
    obj.ball = ball;
    obj.ballMat = ballMat;
    obj.displayBallRad = displayBallRad;

    // Ball glow
    const ballGlowGeo = new THREE.SphereGeometry(displayBallRad * 1.5, 16, 16);
    const ballGlowMat = new THREE.MeshBasicMaterial({
      color: COLORS.ball, transparent: true, opacity: 0.2,
    });
    const ballGlow = new THREE.Mesh(ballGlowGeo, ballGlowMat);
    ball.add(ballGlow);
    obj.ballGlowMat = ballGlowMat;

    // Dynamic point light following ball
    const ballLight = new THREE.PointLight(0xff8800, 0.6, 1.5);
    ball.add(ballLight);
    obj.ballLight = ballLight;

    // Torque arrow (shows control input direction — curved arrow at pivot)
    const arrowGeo = new THREE.ConeGeometry(0.02, 0.08, 8);
    const arrowMat = new THREE.MeshBasicMaterial({
      color: COLORS.torque, transparent: true, opacity: 0.8,
    });
    const torqueArrow = new THREE.Mesh(arrowGeo, arrowMat);
    torqueArrow.position.set(0, 0.08, 0.08);
    torqueArrow.visible = false;
    beamGroup.add(torqueArrow);
    obj.torqueArrow = torqueArrow;
    obj.torqueArrowMat = arrowMat;
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

    if (obj.ballGlowMat) {
      obj.ballGlowMat.opacity = 0.15 + vel * 0.3 + Math.sin(elapsed * 5) * 0.05;
    }
    if (obj.ballMat) {
      const color = new THREE.Color(COLORS.ball);
      if (vel > 0.5) color.lerp(new THREE.Color(0xff0066), (vel - 0.5) * 2);
      else if (vel < 0.1) color.lerp(new THREE.Color(0x10b981), (0.1 - vel) * 10);
      obj.ballMat.color.copy(color);
      obj.ballMat.emissiveIntensity = 0.5 + vel * 0.5;
    }
    if (obj.ballLight) {
      obj.ballLight.intensity = 0.3 + vel * 0.8;
    }
    if (obj.beamMat) {
      obj.beamMat.emissiveIntensity = 0.3 + vel * 0.3;
    }
  };

  const updatePositions = useCallback((anim, frameIdx) => {
    const obj = objectsRef.current;
    if (!obj.beamGroup || !obj.ball || !anim) return;

    const idx = Math.min(frameIdx, anim.num_frames - 1);
    const ballR = anim.ball_r[idx] || 0;
    const alpha = anim.beam_alpha[idx] || 0;
    const torque = anim.control_torque[idx] || 0;
    const beamLen = anim.beam_length || 1.0;
    const displayBallRad = obj.displayBallRad || 0.03;

    // Beam tilt: rotate around z-axis at pivot
    obj.beamGroup.rotation.z = -alpha;  // negative for visual consistency

    // Ball position along beam (local x-axis of beam)
    // Clamp to beam bounds
    const halfLen = beamLen / 2 - displayBallRad;
    const clampedR = Math.max(-halfLen, Math.min(halfLen, ballR));
    obj.ball.position.x = clampedR;

    // Torque arrow
    if (obj.torqueArrow) {
      const maxTorque = 10;
      const normTorque = Math.abs(torque) / maxTorque;
      if (normTorque > 0.01) {
        obj.torqueArrow.visible = true;
        const dir = torque > 0 ? 1 : -1;
        obj.torqueArrow.position.x = 0;
        obj.torqueArrow.position.y = 0.06;
        obj.torqueArrow.position.z = dir * 0.06;
        obj.torqueArrow.rotation.x = dir > 0 ? 0 : Math.PI;
        obj.torqueArrow.scale.setScalar(0.5 + normTorque * 1.5);
        if (obj.torqueArrowMat) obj.torqueArrowMat.opacity = 0.3 + normTorque * 0.7;
      } else {
        obj.torqueArrow.visible = false;
      }
    }

    // Velocity for glow effects
    if (idx > 0 && idx < anim.num_frames) {
      const prevR = anim.ball_r[idx - 1] || 0;
      const vel = Math.abs(ballR - prevR) / (anim.dt || 0.02);
      physicsRef.current.velNorm = Math.min(1, vel / 2);
    }

    // Ball world position for trail
    const cosA = Math.cos(alpha);
    const sinA = Math.sin(alpha);
    const ballWorldX = clampedR * cosA;
    const ballWorldY = BEAM_Y - clampedR * sinA + (0.0125 + displayBallRad) * cosA;

    // Trail
    if (obj.trails) {
      for (let i = TRAIL_LENGTH - 1; i > 0; i--) {
        obj.trails[i].position.copy(obj.trails[i - 1].position);
        obj.trails[i].active = obj.trails[i - 1].active;
      }
      obj.trails[0].position.set(ballWorldX, ballWorldY, 0);
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
    <div className="bb3d-animation-panel">
      <div ref={containerRef} className="bb3d-canvas-3d">
        <div className="bb3d-3d-hint">
          Drag to rotate &middot; Scroll to zoom
        </div>
      </div>
      <div className="bb3d-animation-controls">
        <button className="bb3d-ctrl-btn" onClick={togglePlay} title={isPlaying ? 'Pause' : 'Play'}>
          {isPlaying ? '\u23F8' : '\u25B6'}
        </button>
        <button className="bb3d-ctrl-btn" onClick={restart} title="Restart">
          {'\u21BA'}
        </button>
        <button className="bb3d-ctrl-btn bb3d-speed-btn" onClick={cycleSpeed} title="Speed">
          {speed}&times;
        </button>
        <span className="bb3d-time-label">
          {currentTime.toFixed(2)} / {animation?.t?.[animation.num_frames - 1]?.toFixed(1) ?? '?'} s
        </span>
        <span className={`bb3d-stability-badge ${isStable ? 'stable' : 'unstable'}`}>
          {isStable ? 'STABLE' : 'UNSTABLE'}
        </span>
      </div>
    </div>
  );
}

export default BallBeam3D;
