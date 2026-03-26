/**
 * CoupledTanks3D — Three.js 3D visualization of coupled tank MIMO system.
 *
 * Two transparent cylindrical tanks connected by a pipe. Water levels animate
 * up/down. Top inflow pipes with particle droplets. Bottom connecting pipe
 * with flow visualization.
 *
 * Props:
 *   animation: { t, h1, h2, q1, q2, dt, num_frames, tank_area, orifice_area,
 *                h1_ref, h2_ref, is_stable }
 *   isStable: boolean
 */

import React, { useRef, useEffect, useCallback, useState, useMemo } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

const lerp = (a, b, t) => a + (b - a) * t;
const SPEED_OPTIONS = [0.5, 1, 2, 4];
const MAX_TANK_HEIGHT = 2.5;
const TANK_RADIUS = 0.5;
const TANK_GAP = 1.8;
const NUM_DROPLETS = 12;

function CoupledTanks3D({ animation, isStable }) {
  const containerRef = useRef(null);
  const rendererRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const controlsRef = useRef(null);
  const clockRef = useRef(new THREE.Clock());
  const objectsRef = useRef({});

  const frameRef = useRef(0);
  const lastFrameTimeRef = useRef(0);
  const playingRef = useRef(true);
  const speedRef = useRef(1);
  const animationRef = useRef(null);

  const [isPlaying, setIsPlaying] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);
  const [speed, setSpeed] = useState(1);

  useEffect(() => { playingRef.current = isPlaying; }, [isPlaying]);
  useEffect(() => { speedRef.current = speed; }, [speed]);

  const COLORS = useMemo(() => ({
    tank1Water: 0x22d3ee,
    tank2Water: 0xf472b6,
    tankGlass: 0x94a3b8,
    pipe: 0x64748b,
    pipeEmissive: 0x475569,
    inflow1: 0x3b82f6,
    inflow2: 0xa855f7,
    droplet1: 0x22d3ee,
    droplet2: 0xf472b6,
    ground: 0x080e1a,
    gridMain: 0x00ffff,
    gridSecondary: 0x1a2744,
    background: 0x060c18,
    refLine: 0x34d399,
  }), []);

  const initScene = useCallback(() => {
    if (!containerRef.current) return;
    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(COLORS.background);
    scene.fog = new THREE.Fog(COLORS.background, 6, 14);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(40, width / height, 0.01, 100);
    camera.position.set(3.0, 2.5, 3.5);
    camera.lookAt(0, 0.8, 0);
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
    controls.minDistance = 1.5;
    controls.maxDistance = 8.0;
    controls.maxPolarAngle = Math.PI * 0.85;
    controls.target.set(0, 0.8, 0);
    controls.update();
    controlsRef.current = controls;

    setupLighting(scene);
    setupEnvironment(scene);
    buildTanks(scene);
    buildPipes(scene);
    createDroplets(scene);

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
    const renderLoop = (ts) => {
      // Frame advancement (merged from separate animation loop)
      const anim = animationRef.current;
      if (anim && anim.num_frames >= 2 && playingRef.current) {
        const frameDt = (anim.dt || 0.04) * 1000;
        const elapsed = ts - lastFrameTimeRef.current;
        const adjusted = frameDt / speedRef.current;
        if (elapsed >= adjusted) {
          lastFrameTimeRef.current = ts;
          frameRef.current = (frameRef.current + 1) % anim.num_frames;
          setCurrentTime(anim.t[frameRef.current] || 0);
        }
      }
      if (anim) {
        updatePositions(anim, frameRef.current);
      }

      controls.update();
      updateGlowEffects(clockRef.current.getElapsedTime());
      renderer.render(scene, camera);
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
    scene.add(new THREE.AmbientLight(0xffffff, 0.2));
    scene.add(new THREE.HemisphereLight(0x0066ff, 0xff0066, 0.15));

    const key = new THREE.DirectionalLight(0xffffff, 1.2);
    key.position.set(3, 6, 4);
    key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048);
    key.shadow.camera.near = 0.1;
    key.shadow.camera.far = 20;
    key.shadow.camera.left = -4;
    key.shadow.camera.right = 4;
    key.shadow.camera.top = 4;
    key.shadow.camera.bottom = -1;
    key.shadow.bias = -0.0003;
    scene.add(key);

    const cyan = new THREE.DirectionalLight(0x00ffff, 0.5);
    cyan.position.set(-3, 3, 2);
    scene.add(cyan);

    const magenta = new THREE.DirectionalLight(0xff00ff, 0.3);
    magenta.position.set(3, 2, -3);
    scene.add(magenta);
  };

  const setupEnvironment = (scene) => {
    const groundGeo = new THREE.PlaneGeometry(10, 10);
    const groundMat = new THREE.MeshStandardMaterial({
      color: COLORS.ground, roughness: 0.85, metalness: 0.15,
    });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = 0;
    ground.receiveShadow = true;
    scene.add(ground);

    const gridGroup = new THREE.Group();
    gridGroup.position.y = 0.001;
    for (let i = -5; i <= 5; i++) {
      const pts = [new THREE.Vector3(i * 0.5, 0, -5), new THREE.Vector3(i * 0.5, 0, 5)];
      const geo = new THREE.BufferGeometry().setFromPoints(pts);
      const mat = new THREE.LineBasicMaterial({
        color: i === 0 ? COLORS.gridMain : COLORS.gridSecondary,
        transparent: true, opacity: i === 0 ? 0.25 : 0.08,
      });
      gridGroup.add(new THREE.Line(geo, mat));
    }
    for (let i = -5; i <= 5; i++) {
      const pts = [new THREE.Vector3(-5, 0, i * 0.5), new THREE.Vector3(5, 0, i * 0.5)];
      const geo = new THREE.BufferGeometry().setFromPoints(pts);
      const mat = new THREE.LineBasicMaterial({
        color: COLORS.gridSecondary, transparent: true, opacity: 0.06,
      });
      gridGroup.add(new THREE.Line(geo, mat));
    }
    scene.add(gridGroup);
  };

  const buildTanks = (scene) => {
    const obj = objectsRef.current;
    const tankX1 = -TANK_GAP / 2;
    const tankX2 = TANK_GAP / 2;

    // --- Tank 1 (glass shell) ---
    const tankGeo = new THREE.CylinderGeometry(TANK_RADIUS, TANK_RADIUS, MAX_TANK_HEIGHT, 32, 1, true);
    const tankMat1 = new THREE.MeshPhysicalMaterial({
      color: COLORS.tankGlass, transparent: true, opacity: 0.12,
      roughness: 0.05, metalness: 0.1, side: THREE.DoubleSide,
      depthWrite: false,
    });
    const tank1 = new THREE.Mesh(tankGeo, tankMat1);
    tank1.position.set(tankX1, MAX_TANK_HEIGHT / 2, 0);
    scene.add(tank1);

    // Tank 1 edge rings
    const ringGeo = new THREE.TorusGeometry(TANK_RADIUS, 0.012, 8, 32);
    const ringMat1 = new THREE.MeshStandardMaterial({
      color: 0x22d3ee, emissive: 0x22d3ee, emissiveIntensity: 0.5,
      roughness: 0.1, metalness: 0.8,
    });
    const topRing1 = new THREE.Mesh(ringGeo, ringMat1);
    topRing1.rotation.x = Math.PI / 2;
    topRing1.position.set(tankX1, MAX_TANK_HEIGHT, 0);
    scene.add(topRing1);
    const botRing1 = new THREE.Mesh(ringGeo, ringMat1.clone());
    botRing1.rotation.x = Math.PI / 2;
    botRing1.position.set(tankX1, 0, 0);
    scene.add(botRing1);

    // --- Tank 2 (glass shell) ---
    const tankMat2 = new THREE.MeshPhysicalMaterial({
      color: COLORS.tankGlass, transparent: true, opacity: 0.12,
      roughness: 0.05, metalness: 0.1, side: THREE.DoubleSide,
      depthWrite: false,
    });
    const tank2 = new THREE.Mesh(tankGeo.clone(), tankMat2);
    tank2.position.set(tankX2, MAX_TANK_HEIGHT / 2, 0);
    scene.add(tank2);

    const ringMat2 = new THREE.MeshStandardMaterial({
      color: 0xf472b6, emissive: 0xf472b6, emissiveIntensity: 0.5,
      roughness: 0.1, metalness: 0.8,
    });
    const topRing2 = new THREE.Mesh(ringGeo.clone(), ringMat2);
    topRing2.rotation.x = Math.PI / 2;
    topRing2.position.set(tankX2, MAX_TANK_HEIGHT, 0);
    scene.add(topRing2);
    const botRing2 = new THREE.Mesh(ringGeo.clone(), ringMat2.clone());
    botRing2.rotation.x = Math.PI / 2;
    botRing2.position.set(tankX2, 0, 0);
    scene.add(botRing2);

    // --- Water volumes (scaled cylinders) ---
    const waterGeo = new THREE.CylinderGeometry(TANK_RADIUS * 0.95, TANK_RADIUS * 0.95, 1, 32);

    const waterMat1 = new THREE.MeshPhysicalMaterial({
      color: COLORS.tank1Water, transparent: true, opacity: 0.45,
      roughness: 0.1, metalness: 0.05, side: THREE.DoubleSide,
    });
    const water1 = new THREE.Mesh(waterGeo, waterMat1);
    water1.position.set(tankX1, 0.5, 0);
    water1.castShadow = true;
    scene.add(water1);
    obj.water1 = water1;
    obj.waterMat1 = waterMat1;

    const waterMat2 = new THREE.MeshPhysicalMaterial({
      color: COLORS.tank2Water, transparent: true, opacity: 0.45,
      roughness: 0.1, metalness: 0.05, side: THREE.DoubleSide,
    });
    const water2 = new THREE.Mesh(waterGeo.clone(), waterMat2);
    water2.position.set(tankX2, 0.5, 0);
    water2.castShadow = true;
    scene.add(water2);
    obj.water2 = water2;
    obj.waterMat2 = waterMat2;

    // Water surface glow discs
    const surfGeo = new THREE.CircleGeometry(TANK_RADIUS * 0.95, 32);
    const surfMat1 = new THREE.MeshBasicMaterial({
      color: COLORS.tank1Water, transparent: true, opacity: 0.25, side: THREE.DoubleSide,
    });
    const surface1 = new THREE.Mesh(surfGeo, surfMat1);
    surface1.rotation.x = -Math.PI / 2;
    surface1.position.set(tankX1, 1.0, 0);
    scene.add(surface1);
    obj.surface1 = surface1;
    obj.surfMat1 = surfMat1;

    const surfMat2 = new THREE.MeshBasicMaterial({
      color: COLORS.tank2Water, transparent: true, opacity: 0.25, side: THREE.DoubleSide,
    });
    const surface2 = new THREE.Mesh(surfGeo.clone(), surfMat2);
    surface2.rotation.x = -Math.PI / 2;
    surface2.position.set(tankX2, 1.0, 0);
    scene.add(surface2);
    obj.surface2 = surface2;
    obj.surfMat2 = surfMat2;

    // Point lights inside tanks
    const light1 = new THREE.PointLight(0x22d3ee, 0.4, 2.0);
    light1.position.set(tankX1, 0.5, 0);
    scene.add(light1);
    obj.light1 = light1;

    const light2 = new THREE.PointLight(0xf472b6, 0.4, 2.0);
    light2.position.set(tankX2, 0.5, 0);
    scene.add(light2);
    obj.light2 = light2;

    // Reference level markers
    const refGeo = new THREE.TorusGeometry(TANK_RADIUS * 1.02, 0.005, 8, 32);
    const refMat = new THREE.MeshBasicMaterial({
      color: COLORS.refLine, transparent: true, opacity: 0.6,
    });
    const ref1 = new THREE.Mesh(refGeo, refMat);
    ref1.rotation.x = Math.PI / 2;
    ref1.position.set(tankX1, 1.0, 0);
    scene.add(ref1);
    obj.ref1 = ref1;

    const ref2 = new THREE.Mesh(refGeo.clone(), refMat.clone());
    ref2.rotation.x = Math.PI / 2;
    ref2.position.set(tankX2, 0.5, 0);
    scene.add(ref2);
    obj.ref2 = ref2;

    // Tank labels (using sprite text)
    obj.tankX1 = tankX1;
    obj.tankX2 = tankX2;
  };

  const buildPipes = (scene) => {
    const obj = objectsRef.current;
    const tankX1 = -TANK_GAP / 2;
    const tankX2 = TANK_GAP / 2;

    // Connecting pipe (tank 1 bottom → tank 2 side)
    const pipeY = 0.15;
    const pipeMat = new THREE.MeshStandardMaterial({
      color: COLORS.pipe, emissive: COLORS.pipeEmissive, emissiveIntensity: 0.3,
      roughness: 0.2, metalness: 0.8,
    });

    // Horizontal pipe
    const pipeLen = TANK_GAP - TANK_RADIUS * 2;
    const pipeGeo = new THREE.CylinderGeometry(0.04, 0.04, pipeLen, 12);
    const connPipe = new THREE.Mesh(pipeGeo, pipeMat);
    connPipe.rotation.z = Math.PI / 2;
    connPipe.position.set(0, pipeY, 0);
    scene.add(connPipe);

    // Pipe connection rings
    const cRingGeo = new THREE.TorusGeometry(0.05, 0.01, 8, 16);
    const cRingMat = new THREE.MeshStandardMaterial({
      color: 0x00ffff, emissive: 0x00ffff, emissiveIntensity: 0.4,
      roughness: 0.1, metalness: 0.9,
    });
    [tankX1 + TANK_RADIUS, tankX2 - TANK_RADIUS].forEach(xPos => {
      const ring = new THREE.Mesh(cRingGeo, cRingMat);
      ring.rotation.y = Math.PI / 2;
      ring.position.set(xPos, pipeY, 0);
      scene.add(ring);
    });

    // Flow indicator spheres in connecting pipe
    const flowSpheres = [];
    for (let i = 0; i < 5; i++) {
      const sGeo = new THREE.SphereGeometry(0.02, 8, 8);
      const sMat = new THREE.MeshBasicMaterial({
        color: COLORS.tank1Water, transparent: true, opacity: 0.6,
      });
      const sphere = new THREE.Mesh(sGeo, sMat);
      sphere.position.set(0, pipeY, 0);
      sphere.visible = false;
      scene.add(sphere);
      flowSpheres.push({ mesh: sphere, mat: sMat, phase: i / 5 });
    }
    obj.flowSpheres = flowSpheres;
    obj.pipeY = pipeY;

    // Top inflow pipes
    const inflowGeo = new THREE.CylinderGeometry(0.03, 0.03, 0.6, 12);
    const inflowMat1 = new THREE.MeshStandardMaterial({
      color: COLORS.inflow1, emissive: COLORS.inflow1, emissiveIntensity: 0.3,
      roughness: 0.2, metalness: 0.7,
    });
    const inflow1 = new THREE.Mesh(inflowGeo, inflowMat1);
    inflow1.position.set(tankX1, MAX_TANK_HEIGHT + 0.3, 0);
    scene.add(inflow1);

    const inflowMat2 = new THREE.MeshStandardMaterial({
      color: COLORS.inflow2, emissive: COLORS.inflow2, emissiveIntensity: 0.3,
      roughness: 0.2, metalness: 0.7,
    });
    const inflow2 = new THREE.Mesh(inflowGeo.clone(), inflowMat2);
    inflow2.position.set(tankX2, MAX_TANK_HEIGHT + 0.3, 0);
    scene.add(inflow2);

    // Drain pipe from tank 2 bottom
    const drainGeo = new THREE.CylinderGeometry(0.03, 0.03, 0.3, 12);
    const drainMat = new THREE.MeshStandardMaterial({
      color: COLORS.pipe, emissive: COLORS.pipeEmissive, emissiveIntensity: 0.2,
      roughness: 0.3, metalness: 0.7,
    });
    const drain = new THREE.Mesh(drainGeo, drainMat);
    drain.position.set(tankX2, -0.15, 0);
    scene.add(drain);
  };

  const createDroplets = (scene) => {
    const obj = objectsRef.current;
    const tankX1 = -TANK_GAP / 2;
    const tankX2 = TANK_GAP / 2;

    const droplets1 = [];
    const droplets2 = [];

    const dropletGeoTemplate = new THREE.SphereGeometry(0.015, 6, 6);
    for (let i = 0; i < NUM_DROPLETS; i++) {
      // Tank 1 droplets — each gets its own geometry clone
      const dMat1 = new THREE.MeshBasicMaterial({
        color: COLORS.droplet1, transparent: true, opacity: 0.7,
      });
      const d1 = new THREE.Mesh(dropletGeoTemplate.clone(), dMat1);
      d1.position.set(tankX1, MAX_TANK_HEIGHT, 0);
      d1.visible = false;
      scene.add(d1);
      droplets1.push({ mesh: d1, mat: dMat1, phase: i / NUM_DROPLETS, active: false });

      // Tank 2 droplets
      const dMat2 = new THREE.MeshBasicMaterial({
        color: COLORS.droplet2, transparent: true, opacity: 0.7,
      });
      const d2 = new THREE.Mesh(dropletGeoTemplate.clone(), dMat2);
      d2.position.set(tankX2, MAX_TANK_HEIGHT, 0);
      d2.visible = false;
      scene.add(d2);
      droplets2.push({ mesh: d2, mat: dMat2, phase: i / NUM_DROPLETS, active: false });
    }
    dropletGeoTemplate.dispose();

    obj.droplets1 = droplets1;
    obj.droplets2 = droplets2;
  };

  const updateGlowEffects = (elapsed) => {
    const obj = objectsRef.current;

    // Pulsing water surface opacity
    const pulse = 0.2 + Math.sin(elapsed * 3) * 0.05;
    if (obj.surfMat1) obj.surfMat1.opacity = pulse;
    if (obj.surfMat2) obj.surfMat2.opacity = pulse;

    // Tank light intensities
    if (obj.light1) obj.light1.intensity = 0.3 + Math.sin(elapsed * 2) * 0.1;
    if (obj.light2) obj.light2.intensity = 0.3 + Math.sin(elapsed * 2 + 1) * 0.1;
  };

  const updatePositions = useCallback((anim, frameIdx) => {
    const obj = objectsRef.current;
    if (!obj.water1 || !obj.water2 || !anim) return;

    const idx = Math.min(frameIdx, anim.num_frames - 1);
    const h1 = Math.max(anim.h1[idx] || 0.01, 0.01);
    const h2 = Math.max(anim.h2[idx] || 0.01, 0.01);
    const q1 = anim.q1[idx] || 0;
    const q2 = anim.q2[idx] || 0;
    const h1Ref = anim.h1_ref || 1.0;
    const h2Ref = anim.h2_ref || 0.5;

    const tankX1 = obj.tankX1;
    const tankX2 = obj.tankX2;

    // Clamp display heights to tank
    const dispH1 = Math.min(h1, MAX_TANK_HEIGHT - 0.05);
    const dispH2 = Math.min(h2, MAX_TANK_HEIGHT - 0.05);

    // Water 1 — scale and position
    obj.water1.scale.y = dispH1;
    obj.water1.position.y = dispH1 / 2;

    // Water 2
    obj.water2.scale.y = dispH2;
    obj.water2.position.y = dispH2 / 2;

    // Surface discs
    if (obj.surface1) obj.surface1.position.y = dispH1;
    if (obj.surface2) obj.surface2.position.y = dispH2;

    // Lights follow water level
    if (obj.light1) obj.light1.position.y = dispH1 / 2;
    if (obj.light2) obj.light2.position.y = dispH2 / 2;

    // Reference rings
    if (obj.ref1) obj.ref1.position.y = Math.min(h1Ref, MAX_TANK_HEIGHT - 0.1);
    if (obj.ref2) obj.ref2.position.y = Math.min(h2Ref, MAX_TANK_HEIGHT - 0.1);

    // Water color intensity based on proximity to reference
    const err1 = Math.abs(h1 - h1Ref);
    const err2 = Math.abs(h2 - h2Ref);
    if (obj.waterMat1) obj.waterMat1.opacity = 0.35 + Math.min(err1, 0.5) * 0.3;
    if (obj.waterMat2) obj.waterMat2.opacity = 0.35 + Math.min(err2, 0.5) * 0.3;

    // Flow spheres in connecting pipe (animate position)
    const elapsed = clockRef.current.getElapsedTime();
    if (obj.flowSpheres) {
      const flowRate = Math.max(0, q1 * 0.3); // proportional to outflow
      obj.flowSpheres.forEach((fs, i) => {
        if (flowRate > 0.05) {
          fs.mesh.visible = true;
          const t = ((elapsed * flowRate * 2 + fs.phase) % 1);
          const x = lerp(tankX1 + TANK_RADIUS, tankX2 - TANK_RADIUS, t);
          fs.mesh.position.x = x;
          fs.mat.opacity = 0.4 + (1 - Math.abs(t - 0.5) * 2) * 0.4;
        } else {
          fs.mesh.visible = false;
        }
      });
    }

    // Droplets for tank 1
    if (obj.droplets1) {
      const rate1 = Math.max(0, q1);
      obj.droplets1.forEach((d, i) => {
        if (rate1 > 0.1) {
          d.active = true;
          d.mesh.visible = true;
          const t = ((elapsed * rate1 * 1.5 + d.phase) % 1);
          const y = lerp(MAX_TANK_HEIGHT, dispH1 + 0.05, t);
          const spread = 0.05 * Math.sin(d.phase * Math.PI * 6 + elapsed * 3);
          d.mesh.position.set(tankX1 + spread, y, spread * 0.7);
          d.mat.opacity = 0.6 * (1 - t * 0.5);
        } else {
          d.mesh.visible = false;
          d.active = false;
        }
      });
    }

    // Droplets for tank 2
    if (obj.droplets2) {
      const rate2 = Math.max(0, q2);
      obj.droplets2.forEach((d, i) => {
        if (rate2 > 0.1) {
          d.active = true;
          d.mesh.visible = true;
          const t = ((elapsed * rate2 * 1.5 + d.phase) % 1);
          const y = lerp(MAX_TANK_HEIGHT, dispH2 + 0.05, t);
          const spread = 0.05 * Math.sin(d.phase * Math.PI * 6 + elapsed * 3);
          d.mesh.position.set(tankX2 + spread, y, spread * 0.7);
          d.mat.opacity = 0.6 * (1 - t * 0.5);
        } else {
          d.mesh.visible = false;
          d.active = false;
        }
      });
    }
  }, [COLORS]);

  // Init scene
  useEffect(() => {
    const cleanup = initScene();
    return cleanup;
  }, [initScene]);

  // Track animation data in ref for the merged render loop
  useEffect(() => {
    animationRef.current = animation;
    frameRef.current = 0;
    lastFrameTimeRef.current = performance.now();
    setCurrentTime(0);
    setIsPlaying(true);
  }, [animation]);

  const togglePlay = () => setIsPlaying(p => !p);
  const restart = () => {
    frameRef.current = 0;
    lastFrameTimeRef.current = performance.now();
    setCurrentTime(0);
  };
  const cycleSpeed = () => {
    setSpeed(s => {
      const i = SPEED_OPTIONS.indexOf(s);
      return SPEED_OPTIONS[(i + 1) % SPEED_OPTIONS.length];
    });
  };

  return (
    <div className="ct3d-animation-panel">
      <div ref={containerRef} className="ct3d-canvas-3d" role="img" aria-label="3D coupled tanks visualization">
        <div className="ct3d-3d-hint">
          Drag to rotate &middot; Scroll to zoom
        </div>
      </div>
      <div className="ct3d-animation-controls">
        <button className="ct3d-ctrl-btn" onClick={togglePlay} aria-label={isPlaying ? 'Pause animation' : 'Play animation'} title={isPlaying ? 'Pause' : 'Play'}>
          {isPlaying ? '\u23F8' : '\u25B6'}
        </button>
        <button className="ct3d-ctrl-btn" onClick={restart} aria-label="Restart animation" title="Restart">
          {'\u21BA'}
        </button>
        <button className="ct3d-ctrl-btn ct3d-speed-btn" onClick={cycleSpeed} aria-label={`Playback speed: ${speed}x`} title={`Speed: ${speed}x`}>
          {speed}&times;
        </button>
        <span className="ct3d-time-label">
          {currentTime.toFixed(2)} / {animation?.t?.[animation.num_frames - 1]?.toFixed(1) ?? '?'} s
        </span>
        <span className={`ct3d-stability-badge ${isStable ? 'stable' : 'unstable'}`}>
          {isStable ? 'STABLE' : 'UNSTABLE'}
        </span>
      </div>
    </div>
  );
}

export default CoupledTanks3D;
