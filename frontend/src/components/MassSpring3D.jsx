/**
 * MassSpring3D Component - Ultra-Premium Three.js 3D Visualization
 *
 * Neon-aesthetic mass-spring-damper system featuring:
 * - Electric cyan spring coil with emissive glow
 * - Hot magenta damper cylinder with pulsing rings
 * - Energy-reactive mass (orange → pink when fast, → green when slow)
 * - Multi-layered glow spheres on mass with pulsing
 * - Rainbow gradient motion trail (cyan → magenta → orange)
 * - Dynamic point lights following mass
 * - Premium PBR materials with high metalness
 * - Deep space background with neon grid
 * - All GPU-rendered — zero backend cost
 */

import React, { useRef, useEffect, useCallback, useState, useMemo } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

const lerp = (a, b, t) => a + (b - a) * t;
const SPEED_OPTIONS = [0.5, 1, 2, 4];
const TRAIL_LENGTH = 25;

function MassSpring3D({ visualization2D, systemInfo }) {
  const containerRef = useRef(null);
  const rendererRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const controlsRef = useRef(null);
  const clockRef = useRef(new THREE.Clock());
  const objectsRef = useRef({});
  const trailRef = useRef([]);
  const glowPulseRef = useRef(0);
  const physicsRef = useRef({ velNorm: 0, maxVel: 1 });

  // Animation state
  const frameRef = useRef(0);
  const lastFrameTimeRef = useRef(0);
  const playingRef = useRef(true);
  const speedRef = useRef(1);

  const [isPlaying, setIsPlaying] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);
  const [speed, setSpeed] = useState(1);

  useEffect(() => { playingRef.current = isPlaying; }, [isPlaying]);
  useEffect(() => { speedRef.current = speed; }, [speed]);

  // Ultra-vibrant neon color palette (matching Furuta aesthetic)
  const COLORS = useMemo(() => ({
    // Spring - electric cyan
    spring: 0x00ffff,
    springEmissive: 0x00e5ff,

    // Damper - hot magenta
    damper: 0xff6fff,
    damperEmissive: 0xff00ff,
    damperPiston: 0xc0c0c0,

    // Mass - energy reactive orange/gold
    mass: 0xff8c00,
    massEmissive: 0xff6600,
    massGlow: 0xffaa00,
    massHighEnergy: 0xff0066,
    massLowEnergy: 0x00ff88,

    // Ceiling - chrome metallic
    ceiling: 0xc0c0c0,
    ceilingAccent: 0x00ffff,

    // Mounting - bright white/silver
    mount: 0xffffff,
    mountMetal: 0xe0e0e0,

    // Trail - rainbow gradient
    trailStart: 0x00ffff,
    trailMid: 0xff00ff,
    trailEnd: 0xff6600,

    // Environment
    ground: 0x080e1a,
    groundAccent: 0x1a2744,
    gridMain: 0x00ffff,
    gridSecondary: 0x2a3f5f,

    // Background — deep dark
    background: 0x060c18,
  }), []);

  // 3D coordinate mapping (compact scale)
  const CEILING_REST_Y = 1.05;
  const MASS_REST_Y = 0.25;
  const CEILING_MAX_TRAVEL = 0.1;
  const MASS_MAX_TRAVEL = 0.35;

  // Build spring as a glowing helix tube
  const createSpringGeometry = useCallback((topY, bottomY, numCoils = 12, radius = 0.045) => {
    const points = [];
    const totalHeight = topY - bottomY;
    if (Math.abs(totalHeight) < 0.05) {
      return new THREE.BufferGeometry();
    }
    const leaderLen = Math.abs(totalHeight) * 0.05;
    const coilHeight = Math.abs(totalHeight) - 2 * leaderLen;
    const pointsPerCoil = 28;
    const totalPts = numCoils * pointsPerCoil;

    points.push(new THREE.Vector3(0, topY, 0));
    points.push(new THREE.Vector3(0, topY - leaderLen, 0));

    for (let i = 0; i <= totalPts; i++) {
      const t = i / totalPts;
      const y = topY - leaderLen - t * coilHeight;
      const angle = t * numCoils * Math.PI * 2;
      const x = radius * Math.cos(angle);
      const z = radius * Math.sin(angle);
      points.push(new THREE.Vector3(x, y, z));
    }

    points.push(new THREE.Vector3(0, bottomY + leaderLen, 0));
    points.push(new THREE.Vector3(0, bottomY, 0));

    const curve = new THREE.CatmullRomCurve3(points, false);
    return new THREE.TubeGeometry(curve, totalPts + 10, 0.005, 8, false);
  }, []);

  // --- Scene setup ---
  const initScene = useCallback(() => {
    if (!containerRef.current) return;
    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    // Scene with fog
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(COLORS.background);
    scene.fog = new THREE.Fog(COLORS.background, 2.5, 5.5);
    sceneRef.current = scene;

    // Camera — pulled back so the system looks compact
    const camera = new THREE.PerspectiveCamera(35, width / height, 0.01, 100);
    camera.position.set(1.6, 1.1, 1.6);
    camera.lookAt(0, 0.45, 0);
    cameraRef.current = camera;

    // High-quality renderer
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance',
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

    // Smooth orbit controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.rotateSpeed = 0.5;
    controls.zoomSpeed = 0.8;
    controls.minDistance = 0.5;
    controls.maxDistance = 3.5;
    controls.maxPolarAngle = Math.PI * 0.85;
    controls.target.set(0, 0.45, 0);
    controls.update();
    controlsRef.current = controls;

    // Build everything
    setupLighting(scene);
    setupEnvironment(scene);
    buildSystem(scene);
    createTrailObjects(scene);

    // Resize
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

    // Render loop with glow updates
    clockRef.current.start();
    let animId;
    const renderLoop = () => {
      const elapsed = clockRef.current.getElapsedTime();
      controls.update();
      updateGlowEffects(elapsed);
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
          if (Array.isArray(obj.material)) obj.material.forEach((m) => m.dispose());
          else obj.material.dispose();
        }
      });
      if (containerRef.current && renderer.domElement.parentNode === containerRef.current) {
        containerRef.current.removeChild(renderer.domElement);
      }
    };
  }, [COLORS]);

  // Premium multi-light setup with dramatic neon lighting
  const setupLighting = (scene) => {
    const obj = objectsRef.current;

    // Low ambient — keeps it dark, neons do the work
    scene.add(new THREE.AmbientLight(0xffffff, 0.18));

    // Hemisphere for sky/ground gradient
    scene.add(new THREE.HemisphereLight(0x0066ff, 0xff0066, 0.2));

    // Key light with shadows
    const key = new THREE.DirectionalLight(0xffffff, 1.5);
    key.position.set(3, 6, 4);
    key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048);
    key.shadow.camera.near = 0.1;
    key.shadow.camera.far = 20;
    key.shadow.camera.left = -2;
    key.shadow.camera.right = 2;
    key.shadow.camera.top = 2;
    key.shadow.camera.bottom = -1;
    key.shadow.bias = -0.0003;
    key.shadow.radius = 3;
    scene.add(key);

    // Subtle fill from opposite side
    const fill = new THREE.DirectionalLight(0x88aacc, 0.15);
    fill.position.set(-3, 3, -2);
    scene.add(fill);

    // Cyan accent light - left side
    const cyanLight = new THREE.DirectionalLight(0x00ffff, 0.7);
    cyanLight.position.set(-4, 2, 2);
    scene.add(cyanLight);

    // Magenta accent light - right side
    const magentaLight = new THREE.DirectionalLight(0xff00ff, 0.45);
    magentaLight.position.set(4, 2, -2);
    scene.add(magentaLight);

    // Bottom cyan uplighting — illuminates floor
    const bottomCyan = new THREE.DirectionalLight(0x00ffff, 0.3);
    bottomCyan.position.set(0, -2, 0);
    scene.add(bottomCyan);

    // Ceiling glow light
    const ceilGlow = new THREE.PointLight(0x00ffff, 0.7, 1.2);
    ceilGlow.position.set(0, CEILING_REST_Y + 0.05, 0);
    obj.ceilGlow = ceilGlow;
    scene.add(ceilGlow);

    // Dynamic mass light 1 - orange glow
    const massLight1 = new THREE.PointLight(0xff8800, 0.7, 1.0);
    massLight1.position.set(0, MASS_REST_Y, 0);
    obj.massLight1 = massLight1;
    scene.add(massLight1);

    // Dynamic mass light 2 - pink glow
    const massLight2 = new THREE.PointLight(0xff0066, 0.35, 0.6);
    massLight2.position.set(0, MASS_REST_Y, 0);
    obj.massLight2 = massLight2;
    scene.add(massLight2);
  };

  // Ground plane well below mass's lowest possible position
  // Mass min Y = MASS_REST_Y - MASS_MAX_TRAVEL = 0.25 - 0.35 = -0.10
  // Floor at Y = -0.35 gives 0.25 clearance — mass never reaches it
  const FLOOR_Y = -0.35;

  const setupEnvironment = (scene) => {
    // Ground disc
    const groundGeo = new THREE.CircleGeometry(2.0, 64);
    const groundMat = new THREE.MeshStandardMaterial({
      color: COLORS.ground,
      roughness: 0.85,
      metalness: 0.15,
    });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = FLOOR_Y;
    ground.receiveShadow = true;
    scene.add(ground);

    // Radial neon grid lines
    const gridGroup = new THREE.Group();
    gridGroup.position.y = FLOOR_Y + 0.001;

    // Concentric circles
    const circleRadii = [0.2, 0.4, 0.7, 1.0, 1.4];
    circleRadii.forEach((r, idx) => {
      const pts = [];
      for (let i = 0; i <= 64; i++) {
        const a = (i / 64) * Math.PI * 2;
        pts.push(new THREE.Vector3(Math.cos(a) * r, 0, Math.sin(a) * r));
      }
      const geo = new THREE.BufferGeometry().setFromPoints(pts);
      const mat = new THREE.LineBasicMaterial({
        color: idx === 0 ? COLORS.gridMain : COLORS.gridSecondary,
        transparent: true,
        opacity: idx === 0 ? 0.35 : 0.15,
      });
      gridGroup.add(new THREE.Line(geo, mat));
    });

    // Radial spokes
    for (let i = 0; i < 12; i++) {
      const angle = (i / 12) * Math.PI * 2;
      const pts = [
        new THREE.Vector3(0, 0, 0),
        new THREE.Vector3(Math.cos(angle) * 1.5, 0, Math.sin(angle) * 1.5),
      ];
      const geo = new THREE.BufferGeometry().setFromPoints(pts);
      const mat = new THREE.LineBasicMaterial({
        color: COLORS.gridSecondary,
        transparent: true,
        opacity: 0.12,
      });
      gridGroup.add(new THREE.Line(geo, mat));
    }

    scene.add(gridGroup);

    // Outer glow ring on floor
    const glowRingGeo = new THREE.TorusGeometry(0.4, 0.003, 8, 64);
    const glowRingMat = new THREE.MeshBasicMaterial({
      color: COLORS.gridMain,
      transparent: true,
      opacity: 0.2,
    });
    const glowRing = new THREE.Mesh(glowRingGeo, glowRingMat);
    glowRing.rotation.x = Math.PI / 2;
    glowRing.position.y = FLOOR_Y + 0.002;
    scene.add(glowRing);
  };

  const buildSystem = (scene) => {
    const obj = objectsRef.current;

    // ═══════════════════════════════════
    // CEILING PLATE — chrome with cyan glow
    // ═══════════════════════════════════
    const ceilGeo = new THREE.BoxGeometry(0.36, 0.028, 0.2);
    const ceilMat = new THREE.MeshStandardMaterial({
      color: COLORS.ceiling,
      roughness: 0.15,
      metalness: 0.95,
    });
    const ceiling = new THREE.Mesh(ceilGeo, ceilMat);
    ceiling.position.y = CEILING_REST_Y;
    ceiling.castShadow = true;
    ceiling.receiveShadow = true;
    scene.add(ceiling);
    obj.ceiling = ceiling;

    // Support rod going UP from ceiling — long enough to vanish into fog
    const supportRodLen = 2.5;
    const supportRodGeo = new THREE.CylinderGeometry(0.008, 0.008, supportRodLen, 12);
    const supportRodMat = new THREE.MeshStandardMaterial({
      color: COLORS.ceiling,
      roughness: 0.15,
      metalness: 0.95,
    });
    const supportRod = new THREE.Mesh(supportRodGeo, supportRodMat);
    supportRod.position.y = 0.014 + supportRodLen / 2;
    supportRod.castShadow = true;
    ceiling.add(supportRod);

    // Ceiling edge glow ring
    const ceilRingGeo = new THREE.TorusGeometry(0.21, 0.003, 12, 64);
    const ceilRingMat = new THREE.MeshBasicMaterial({
      color: COLORS.ceilingAccent,
      transparent: true,
      opacity: 0.7,
    });
    const ceilRing = new THREE.Mesh(ceilRingGeo, ceilRingMat);
    ceilRing.rotation.x = Math.PI / 2;
    ceilRing.position.y = -0.018;
    obj.ceilRing = ceilRing;
    ceiling.add(ceilRing);

    // Ceiling hatching
    const hatchGroup = new THREE.Group();
    for (let i = -4; i <= 4; i++) {
      const xOff = i * 0.035;
      const pts = [
        new THREE.Vector3(xOff - 0.012, -0.015, -0.09),
        new THREE.Vector3(xOff + 0.012, -0.015, 0.09),
      ];
      const geo = new THREE.BufferGeometry().setFromPoints(pts);
      const mat = new THREE.LineBasicMaterial({
        color: 0x666666,
        transparent: true,
        opacity: 0.3,
      });
      hatchGroup.add(new THREE.Line(geo, mat));
    }
    ceiling.add(hatchGroup);

    // Ceiling wireframe edges
    const ceilEdgeGeo = new THREE.EdgesGeometry(ceilGeo);
    const ceilEdgeMat = new THREE.LineBasicMaterial({
      color: COLORS.ceilingAccent,
      transparent: true,
      opacity: 0.4,
    });
    ceiling.add(new THREE.LineSegments(ceilEdgeGeo, ceilEdgeMat));

    // ═══════════════════════════════════
    // MOUNTING BRACKETS — chrome pivots
    // ═══════════════════════════════════
    const mountGeo = new THREE.CylinderGeometry(0.007, 0.007, 0.02, 12);
    const mountMat = new THREE.MeshStandardMaterial({
      color: COLORS.mount,
      roughness: 0.05,
      metalness: 1.0,
    });

    // Spring mount
    const springMount = new THREE.Mesh(mountGeo, mountMat);
    springMount.position.set(-0.07, -0.024, 0);
    springMount.castShadow = true;
    ceiling.add(springMount);

    // Damper mount
    const damperMount = new THREE.Mesh(mountGeo, mountMat);
    damperMount.position.set(0.07, -0.024, 0);
    damperMount.castShadow = true;
    ceiling.add(damperMount);

    // Mounting point glow rings
    const mountRingGeo = new THREE.TorusGeometry(0.01, 0.002, 8, 24);
    const mountRingMat = new THREE.MeshBasicMaterial({
      color: 0x00ffff,
      transparent: true,
      opacity: 0.6,
    });
    const springMountRing = new THREE.Mesh(mountRingGeo, mountRingMat);
    springMountRing.rotation.x = Math.PI / 2;
    springMountRing.position.set(-0.07, -0.035, 0);
    obj.springMountRing = springMountRing;
    ceiling.add(springMountRing);

    const damperMountRing = new THREE.Mesh(mountRingGeo.clone(), mountRingMat.clone());
    damperMountRing.rotation.x = Math.PI / 2;
    damperMountRing.position.set(0.07, -0.035, 0);
    obj.damperMountRing = damperMountRing;
    ceiling.add(damperMountRing);

    // ═══════════════════════════════════
    // SPRING — electric cyan helix with glow
    // ═══════════════════════════════════
    const springMat = new THREE.MeshStandardMaterial({
      color: COLORS.spring,
      emissive: COLORS.springEmissive,
      emissiveIntensity: 0.65,
      roughness: 0.12,
      metalness: 0.6,
    });
    const springGeo = createSpringGeometry(
      CEILING_REST_Y - 0.04,
      MASS_REST_Y + 0.06,
      10,
      0.035,
    );
    const spring = new THREE.Mesh(springGeo, springMat);
    spring.position.x = -0.07;
    spring.castShadow = true;
    scene.add(spring);
    obj.spring = spring;
    obj.springMat = springMat;

    // Spring glow cylinder (subtle ambient glow around spring)
    const springGlowGeo = new THREE.CylinderGeometry(0.045, 0.045,
      CEILING_REST_Y - MASS_REST_Y - 0.08, 8, 1, true);
    const springGlowMat = new THREE.MeshBasicMaterial({
      color: COLORS.spring,
      transparent: true,
      opacity: 0.04,
      side: THREE.DoubleSide,
    });
    const springGlow = new THREE.Mesh(springGlowGeo, springGlowMat);
    springGlow.position.set(-0.07, (CEILING_REST_Y + MASS_REST_Y) / 2, 0);
    obj.springGlow = springGlow;
    scene.add(springGlow);

    // ═══════════════════════════════════
    // DAMPER — hot magenta cylinder
    // ═══════════════════════════════════
    const damperGroup = new THREE.Group();
    damperGroup.position.x = 0.07;
    scene.add(damperGroup);
    obj.damperGroup = damperGroup;

    // Piston rod (top)
    const pistonRodGeo = new THREE.CylinderGeometry(0.004, 0.004, 0.2, 12);
    const pistonRodMat = new THREE.MeshStandardMaterial({
      color: COLORS.damperPiston,
      roughness: 0.1,
      metalness: 0.95,
    });
    const pistonRod = new THREE.Mesh(pistonRodGeo, pistonRodMat);
    pistonRod.position.y = CEILING_REST_Y - 0.2;
    pistonRod.castShadow = true;
    damperGroup.add(pistonRod);
    obj.pistonRod = pistonRod;

    // Piston head disc
    const pistonHeadGeo = new THREE.CylinderGeometry(0.02, 0.02, 0.005, 20);
    const pistonHeadMat = new THREE.MeshStandardMaterial({
      color: COLORS.damperPiston,
      roughness: 0.1,
      metalness: 0.95,
    });
    const pistonHead = new THREE.Mesh(pistonHeadGeo, pistonHeadMat);
    pistonHead.position.y = CEILING_REST_Y - 0.35;
    pistonHead.castShadow = true;
    damperGroup.add(pistonHead);
    obj.pistonHead = pistonHead;

    // Cylinder body - hot magenta with glow
    const cylGeo = new THREE.CylinderGeometry(0.025, 0.025, 0.16, 20, 1, true);
    const cylMat = new THREE.MeshStandardMaterial({
      color: COLORS.damper,
      emissive: COLORS.damperEmissive,
      emissiveIntensity: 0.5,
      roughness: 0.2,
      metalness: 0.6,
      transparent: true,
      opacity: 0.8,
      side: THREE.DoubleSide,
    });
    const cylinder = new THREE.Mesh(cylGeo, cylMat);
    cylinder.position.y = (CEILING_REST_Y + MASS_REST_Y) / 2;
    damperGroup.add(cylinder);
    obj.damperCylinder = cylinder;
    obj.damperCylMat = cylMat;

    // Cylinder glow rings - top & bottom
    const cylRingGeo = new THREE.TorusGeometry(0.026, 0.002, 12, 32);
    const cylRingMat = new THREE.MeshBasicMaterial({
      color: COLORS.damper,
      transparent: true,
      opacity: 0.8,
    });
    const topRing = new THREE.Mesh(cylRingGeo, cylRingMat);
    topRing.rotation.x = Math.PI / 2;
    topRing.position.y = cylinder.position.y + 0.08;
    damperGroup.add(topRing);
    obj.damperTopRing = topRing;

    const botRing = new THREE.Mesh(cylRingGeo.clone(), cylRingMat.clone());
    botRing.rotation.x = Math.PI / 2;
    botRing.position.y = cylinder.position.y - 0.08;
    damperGroup.add(botRing);
    obj.damperBotRing = botRing;

    // Bottom rod (from cylinder to mass)
    const bottomRodGeo = new THREE.CylinderGeometry(0.004, 0.004, 0.18, 12);
    const bottomRod = new THREE.Mesh(bottomRodGeo, pistonRodMat.clone());
    bottomRod.position.y = MASS_REST_Y + 0.2;
    bottomRod.castShadow = true;
    damperGroup.add(bottomRod);
    obj.damperBottomRod = bottomRod;

    // ═══════════════════════════════════
    // MASS BLOCK — energy-reactive with multi-layer glow
    // ═══════════════════════════════════
    const massGeo = new THREE.BoxGeometry(0.14, 0.07, 0.1);
    const massMat = new THREE.MeshStandardMaterial({
      color: COLORS.mass,
      emissive: COLORS.massEmissive,
      emissiveIntensity: 0.7,
      roughness: 0.08,
      metalness: 0.5,
    });
    const mass = new THREE.Mesh(massGeo, massMat);
    mass.position.y = MASS_REST_Y;
    mass.castShadow = true;
    mass.receiveShadow = true;
    scene.add(mass);
    obj.mass = mass;
    obj.massMat = massMat;

    // Mass wireframe edges
    const massEdgeGeo = new THREE.EdgesGeometry(massGeo);
    const massEdgeMat = new THREE.LineBasicMaterial({
      color: COLORS.massGlow,
      transparent: true,
      opacity: 0.35,
    });
    mass.add(new THREE.LineSegments(massEdgeGeo, massEdgeMat));

    // Inner glow sphere (on mass)
    const innerGlowGeo = new THREE.SphereGeometry(0.07, 24, 24);
    const innerGlowMat = new THREE.MeshBasicMaterial({
      color: COLORS.massGlow,
      transparent: true,
      opacity: 0.25,
    });
    const innerGlow = new THREE.Mesh(innerGlowGeo, innerGlowMat);
    obj.innerGlow = innerGlow;
    obj.innerGlowMat = innerGlowMat;
    mass.add(innerGlow);

    // Outer glow sphere
    const outerGlowGeo = new THREE.SphereGeometry(0.1, 20, 20);
    const outerGlowMat = new THREE.MeshBasicMaterial({
      color: COLORS.massGlow,
      transparent: true,
      opacity: 0.1,
    });
    const outerGlow = new THREE.Mesh(outerGlowGeo, outerGlowMat);
    obj.outerGlow = outerGlow;
    obj.outerGlowMat = outerGlowMat;
    mass.add(outerGlow);

    // "m" label sprite
    const mCanvas = document.createElement('canvas');
    mCanvas.width = 128;
    mCanvas.height = 128;
    const mCtx = mCanvas.getContext('2d');
    mCtx.fillStyle = '#ffffff';
    mCtx.font = 'bold 80px Inter, -apple-system, sans-serif';
    mCtx.textAlign = 'center';
    mCtx.textBaseline = 'middle';
    mCtx.fillText('m', 64, 64);
    const mTex = new THREE.CanvasTexture(mCanvas);
    const mSpriteMat = new THREE.SpriteMaterial({ map: mTex, transparent: true, opacity: 0.95 });
    const mSprite = new THREE.Sprite(mSpriteMat);
    mSprite.scale.set(0.07, 0.07, 1);
    mSprite.position.set(0, 0, 0.08);
    mass.add(mSprite);

    // Mass connection bars (spring and damper to mass top)
    const barMat = new THREE.MeshStandardMaterial({
      color: COLORS.mountMetal,
      roughness: 0.2,
      metalness: 0.9,
    });
    // left bar (spring side)
    const leftBarGeo = new THREE.CylinderGeometry(0.003, 0.003, 0.08, 8);
    const leftBar = new THREE.Mesh(leftBarGeo, barMat);
    leftBar.rotation.z = Math.PI / 2;
    leftBar.position.set(-0.03, 0.035, 0);
    mass.add(leftBar);

    // right bar (damper side)
    const rightBar = new THREE.Mesh(leftBarGeo.clone(), barMat);
    rightBar.rotation.z = Math.PI / 2;
    rightBar.position.set(0.03, 0.035, 0);
    mass.add(rightBar);

    // Connection point glow dots on mass top
    const dotGeo = new THREE.SphereGeometry(0.006, 12, 12);
    const dotMatCyan = new THREE.MeshBasicMaterial({
      color: 0x00ffff,
      transparent: true,
      opacity: 0.8,
    });
    const dotMatMagenta = new THREE.MeshBasicMaterial({
      color: 0xff00ff,
      transparent: true,
      opacity: 0.8,
    });
    const leftDot = new THREE.Mesh(dotGeo, dotMatCyan);
    leftDot.position.set(-0.07, 0.035, 0);
    mass.add(leftDot);
    obj.leftDot = leftDot;

    const rightDot = new THREE.Mesh(dotGeo.clone(), dotMatMagenta);
    rightDot.position.set(0.07, 0.035, 0);
    mass.add(rightDot);
    obj.rightDot = rightDot;

    // ═══════════════════════════════════
    // EQUILIBRIUM REFERENCE
    // ═══════════════════════════════════
    const refPts = [
      new THREE.Vector3(-0.12, MASS_REST_Y, 0),
      new THREE.Vector3(0.12, MASS_REST_Y, 0),
    ];
    const refGeo = new THREE.BufferGeometry().setFromPoints(refPts);
    const refMat = new THREE.LineDashedMaterial({
      color: 0x00ffff,
      transparent: true,
      opacity: 0.15,
      dashSize: 0.02,
      gapSize: 0.02,
    });
    const refLine = new THREE.Line(refGeo, refMat);
    refLine.computeLineDistances();
    scene.add(refLine);

    // ═══════════════════════════════════
    // k & b LABEL SPRITES
    // ═══════════════════════════════════
    const makeLabel = (text, color) => {
      const c = document.createElement('canvas');
      c.width = 96;
      c.height = 96;
      const cx = c.getContext('2d');
      cx.fillStyle = color;
      cx.font = 'bold 60px "Fira Code", monospace';
      cx.textAlign = 'center';
      cx.textBaseline = 'middle';
      cx.fillText(text, 48, 48);
      const tex = new THREE.CanvasTexture(c);
      const mat = new THREE.SpriteMaterial({ map: tex, transparent: true, opacity: 0.9 });
      const sprite = new THREE.Sprite(mat);
      sprite.scale.set(0.08, 0.08, 1);
      return sprite;
    };

    const kLabel = makeLabel('k', '#00ffff');
    kLabel.position.set(-0.16, (CEILING_REST_Y + MASS_REST_Y) / 2, 0);
    scene.add(kLabel);
    obj.kLabel = kLabel;

    const bLabel = makeLabel('b', '#ff6fff');
    bLabel.position.set(0.16, (CEILING_REST_Y + MASS_REST_Y) / 2, 0);
    scene.add(bLabel);
    obj.bLabel = bLabel;

  };

  // Rainbow gradient motion trail
  const createTrailObjects = (scene) => {
    const obj = objectsRef.current;
    const trailGroup = new THREE.Group();
    const trails = [];

    for (let i = 0; i < TRAIL_LENGTH; i++) {
      const t = i / TRAIL_LENGTH;
      const size = 0.016 * (1 - t * 0.5);
      const opacity = 0.8 * Math.pow(1 - t, 0.7);

      // Rainbow: cyan → magenta → orange
      const color = new THREE.Color();
      if (t < 0.5) {
        color.setHex(COLORS.trailStart);
        color.lerp(new THREE.Color(COLORS.trailMid), t * 2);
      } else {
        color.setHex(COLORS.trailMid);
        color.lerp(new THREE.Color(COLORS.trailEnd), (t - 0.5) * 2);
      }

      const geo = new THREE.SphereGeometry(size, 12, 12);
      const mat = new THREE.MeshBasicMaterial({
        color,
        transparent: true,
        opacity,
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.visible = false;
      trailGroup.add(mesh);
      trails.push({
        mesh,
        position: new THREE.Vector3(0, MASS_REST_Y, 0),
        active: false,
        baseOpacity: opacity,
      });
    }
    scene.add(trailGroup);
    obj.trails = trails;
  };

  // Animate glow effects with physics-reactive behavior
  const updateGlowEffects = (elapsed) => {
    const obj = objectsRef.current;
    const velNorm = physicsRef.current.velNorm || 0;

    // Ceiling glow ring pulse
    if (obj.ceilRing) {
      const pulse = 0.6 + Math.sin(elapsed * 3) * 0.15;
      obj.ceilRing.material.opacity = pulse;
    }

    // Mount point ring pulses
    if (obj.springMountRing) {
      obj.springMountRing.material.opacity = 0.5 + Math.sin(elapsed * 4) * 0.15;
    }
    if (obj.damperMountRing) {
      obj.damperMountRing.material.opacity = 0.5 + Math.sin(elapsed * 4 + 1) * 0.15;
    }

    // Ceiling glow light pulse
    if (obj.ceilGlow) {
      obj.ceilGlow.intensity = 0.4 + Math.sin(elapsed * 2) * 0.15;
    }

    // Inner mass glow - brighter when fast
    if (obj.innerGlowMat) {
      const baseGlow = 0.2 + velNorm * 0.35;
      obj.innerGlowMat.opacity = baseGlow + Math.sin(elapsed * 5) * 0.08;
    }

    // Outer mass glow
    if (obj.outerGlowMat) {
      obj.outerGlowMat.opacity = 0.08 + velNorm * 0.25;
    }

    // Dynamic mass color based on velocity
    if (obj.massMat) {
      const massColor = new THREE.Color(COLORS.mass);
      if (velNorm > 0.5) {
        massColor.lerp(new THREE.Color(COLORS.massHighEnergy), (velNorm - 0.5) * 2);
      } else if (velNorm < 0.15) {
        massColor.lerp(new THREE.Color(COLORS.massLowEnergy), (0.15 - velNorm) / 0.15 * 0.4);
      }
      obj.massMat.color.copy(massColor);
      obj.massMat.emissiveIntensity = 0.5 + velNorm * 0.5;
    }

    // Mass glow color follows mass
    if (obj.innerGlowMat) {
      const glowColor = new THREE.Color(COLORS.massGlow);
      if (velNorm > 0.5) {
        glowColor.lerp(new THREE.Color(COLORS.massHighEnergy), (velNorm - 0.5) * 2);
      }
      obj.innerGlowMat.color.copy(glowColor);
    }

    // Mass lights intensity
    if (obj.massLight1) {
      obj.massLight1.intensity = 0.4 + velNorm * 0.8;
    }
    if (obj.massLight2) {
      obj.massLight2.intensity = 0.2 + velNorm * 0.5;
    }

    // Spring emissive intensity
    if (obj.springMat) {
      obj.springMat.emissiveIntensity = 0.5 + velNorm * 0.3;
    }

    // Damper emissive intensity + ring pulses
    if (obj.damperCylMat) {
      obj.damperCylMat.emissiveIntensity = 0.4 + velNorm * 0.4;
    }
    if (obj.damperTopRing) {
      const pulse = 0.7 + Math.sin(elapsed * 4) * 0.15;
      obj.damperTopRing.material.opacity = pulse;
    }
    if (obj.damperBotRing) {
      const pulse = 0.7 + Math.sin(elapsed * 4 + Math.PI) * 0.15;
      obj.damperBotRing.material.opacity = pulse;
    }

    // Connection dots pulse
    if (obj.leftDot) {
      obj.leftDot.material.opacity = 0.7 + Math.sin(elapsed * 5) * 0.2;
    }
    if (obj.rightDot) {
      obj.rightDot.material.opacity = 0.7 + Math.sin(elapsed * 5 + 1.5) * 0.2;
    }

  };

  // --- Update system positions ---
  const updatePositions = useCallback((viz, frameIdx) => {
    const obj = objectsRef.current;
    if (!obj.ceiling || !obj.mass || !viz) return;

    const { input_position, mass_position, velocity } = viz;
    const idx = Math.min(frameIdx, viz.num_frames - 1);
    const baseDisp = input_position[idx] || 0;
    const massDisp = mass_position[idx] || 0;
    const vel = velocity?.[idx] || 0;

    // Shared scale: both ceiling and mass use the same pixels-per-unit so
    // resonance magnification (output >> input) is visually obvious.
    const globalMaxAbs = Math.max(0.1,
      Math.max(...input_position.map(Math.abs)),
      Math.max(...mass_position.map(Math.abs)),
    );
    const sharedScale = MASS_MAX_TRAVEL / globalMaxAbs;
    // Ceiling uses a tighter range since it's near the top
    const ceilScale = Math.min(sharedScale, CEILING_MAX_TRAVEL / Math.max(0.1, Math.max(...input_position.map(Math.abs))));

    // Ceiling Y — negate so positive displacement moves downward
    // (matches 2D: hanging system, positive = stretching spring)
    const ceilY = CEILING_REST_Y - baseDisp * ceilScale;
    obj.ceiling.position.y = ceilY;

    // Mass Y — same convention: positive displacement = downward
    const massY = MASS_REST_Y - massDisp * sharedScale;
    obj.mass.position.y = massY;

    // Update ceiling glow light
    if (obj.ceilGlow) obj.ceilGlow.position.y = ceilY + 0.05;

    // Mass lights follow mass
    if (obj.massLight1) obj.massLight1.position.y = massY;
    if (obj.massLight2) obj.massLight2.position.y = massY;

    // --- Rebuild spring geometry ---
    const springTopY = ceilY - 0.04;
    const springBottomY = massY + 0.04;
    if (springTopY - springBottomY > 0.05 && obj.spring) {
      obj.spring.geometry.dispose();
      obj.spring.geometry = createSpringGeometry(springTopY, springBottomY, 10, 0.035);
    }

    // Spring ambient glow
    if (obj.springGlow) {
      const h = Math.max(0.05, springTopY - springBottomY);
      obj.springGlow.scale.y = h / (CEILING_REST_Y - MASS_REST_Y - 0.08);
      obj.springGlow.position.y = (springTopY + springBottomY) / 2;
    }

    // --- Update damper positions ---
    const damperTopY = ceilY - 0.04;
    const damperBottomY = massY + 0.04;
    const damperMidY = (damperTopY + damperBottomY) / 2;

    if (obj.pistonRod) {
      const rodLen = Math.max(0.02, damperTopY - (damperMidY + 0.06));
      obj.pistonRod.scale.y = rodLen / 0.2;
      obj.pistonRod.position.y = damperTopY - rodLen / 2;
    }
    if (obj.pistonHead) {
      obj.pistonHead.position.y = damperMidY + 0.06;
    }
    if (obj.damperCylinder) {
      const cylH = Math.max(0.04, (damperBottomY - (damperMidY - 0.08)));
      obj.damperCylinder.scale.y = cylH / 0.16;
      obj.damperCylinder.position.y = damperMidY - 0.01;
    }
    if (obj.damperTopRing) obj.damperTopRing.position.y = damperMidY + 0.06;
    if (obj.damperBotRing) obj.damperBotRing.position.y = damperMidY - 0.08;
    if (obj.damperBottomRod) {
      const rodLen = Math.max(0.02, (damperMidY - 0.08) - damperBottomY);
      obj.damperBottomRod.scale.y = Math.max(0.01, rodLen / 0.18);
      obj.damperBottomRod.position.y = damperBottomY + rodLen / 2;
    }

    // Labels mid-height
    const midY = (ceilY + massY) / 2;
    if (obj.kLabel) obj.kLabel.position.y = midY;
    if (obj.bLabel) obj.bLabel.position.y = midY;

    // --- Velocity norm for glow effects ---
    const maxVel = Math.max(0.1, ...velocity.map(Math.abs));
    const velNorm = Math.min(1, Math.abs(vel) / maxVel);
    physicsRef.current.velNorm = velNorm;
    physicsRef.current.maxVel = maxVel;

    // --- Motion trail ---
    if (obj.trails) {
      const speedRatio = velNorm;
      const opacityBoost = 0.6 + speedRatio * 0.4;

      // Shift trail positions
      for (let i = TRAIL_LENGTH - 1; i > 0; i--) {
        obj.trails[i].position.copy(obj.trails[i - 1].position);
        obj.trails[i].active = obj.trails[i - 1].active;
      }
      obj.trails[0].position.set(0, massY, 0);
      obj.trails[0].active = true;

      for (let i = 0; i < TRAIL_LENGTH; i++) {
        const trail = obj.trails[i];
        trail.mesh.visible = trail.active && i > 0;
        if (trail.active) {
          trail.mesh.position.copy(trail.position);
          trail.mesh.material.opacity = trail.baseOpacity * opacityBoost;
        }
      }
    }
  }, [createSpringGeometry]);

  // Init scene once
  useEffect(() => {
    const cleanup = initScene();
    return cleanup;
  }, [initScene]);

  // Animation loop for frame advancement
  useEffect(() => {
    if (!visualization2D || visualization2D.num_frames < 2) return;

    const frameDt = visualization2D.dt * 1000;
    lastFrameTimeRef.current = performance.now();
    let animId;

    const loop = (ts) => {
      if (playingRef.current) {
        const elapsed = ts - lastFrameTimeRef.current;
        const adjusted = frameDt / speedRef.current;
        if (elapsed >= adjusted) {
          lastFrameTimeRef.current = ts;
          frameRef.current = (frameRef.current + 1) % visualization2D.num_frames;
          setCurrentTime(visualization2D.time[frameRef.current] || 0);
        }
      }
      updatePositions(visualization2D, frameRef.current);
      animId = requestAnimationFrame(loop);
    };

    animId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animId);
  }, [visualization2D, updatePositions]);

  // Reset on data change
  useEffect(() => {
    frameRef.current = 0;
    lastFrameTimeRef.current = performance.now();
    // Clear trail
    if (objectsRef.current.trails) {
      objectsRef.current.trails.forEach((t) => {
        t.active = false;
        t.mesh.visible = false;
      });
    }
    setCurrentTime(0);
    setIsPlaying(true);
  }, [visualization2D]);

  // Controls
  const togglePlay = () => setIsPlaying((p) => !p);
  const restart = () => {
    frameRef.current = 0;
    lastFrameTimeRef.current = performance.now();
    if (objectsRef.current.trails) {
      objectsRef.current.trails.forEach((t) => {
        t.active = false;
        t.mesh.visible = false;
      });
    }
    setCurrentTime(0);
  };
  const cycleSpeed = () => {
    setSpeed((s) => {
      const i = SPEED_OPTIONS.indexOf(s);
      return SPEED_OPTIONS[(i + 1) % SPEED_OPTIONS.length];
    });
  };

  return (
    <div className="ms-animation-panel">
      <div
        ref={containerRef}
        className="ms-canvas-3d"
      >
        <div className="ms-3d-hint">
          Drag to rotate &middot; Scroll to zoom
        </div>
      </div>
      <div className="ms-animation-controls">
        <button className="ms-ctrl-btn" onClick={togglePlay} title={isPlaying ? 'Pause' : 'Play'}>
          {isPlaying ? '\u23F8' : '\u25B6'}
        </button>
        <button className="ms-ctrl-btn" onClick={restart} title="Restart">
          {'\u21BA'}
        </button>
        <button className="ms-ctrl-btn ms-speed-btn" onClick={cycleSpeed} title="Playback speed">
          {speed}&times;
        </button>
        <span className="ms-time-label">
          {currentTime.toFixed(2)} / {visualization2D?.total_time?.toFixed(1) ?? '?'} s
        </span>
      </div>
    </div>
  );
}

export default MassSpring3D;
