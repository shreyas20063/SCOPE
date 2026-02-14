/**
 * FurutaPendulum3D Component - Ultra-Smooth Professional 3D Visualization
 *
 * Premium Three.js visualization featuring:
 * - Buttery smooth frame interpolation (60fps regardless of data rate)
 * - Motion trail effects with fading ghost spheres
 * - Premium PBR materials with environment reflections
 * - Dynamic glow and pulsing effects
 * - Smooth orbit controls with damping
 * - Professional lighting and shadows
 */

import React, { useRef, useEffect, useCallback, useState, useMemo } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

// Smooth interpolation utilities
const lerp = (a, b, t) => a + (b - a) * t;
const lerpAngle = (a, b, t) => {
  let diff = b - a;
  while (diff > Math.PI) diff -= Math.PI * 2;
  while (diff < -Math.PI) diff += Math.PI * 2;
  return a + diff * t;
};
const smoothstep = (t) => t * t * (3 - 2 * t);
const easeOutQuart = (t) => 1 - Math.pow(1 - t, 4);

/**
 * Furuta Pendulum 3D Visualization with Ultra-Smooth Animation
 */
function FurutaPendulum3D({ visualization3D, isStable, onFrameChange }) {
  const containerRef = useRef(null);
  const rendererRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const controlsRef = useRef(null);
  const clockRef = useRef(new THREE.Clock());
  const objectsRef = useRef({});
  const animationStateRef = useRef({
    currentPhi: 0,
    currentTheta: 0,
    targetPhi: 0,
    targetTheta: 0,
    velocity: { phi: 0, theta: 0 },
  });
  const trailRef = useRef([]);
  const glowPulseRef = useRef(0);
  const physicsStateRef = useRef({
    currentSpeed: 0,
    currentEnergy: 0,
    normalizedEnergy: 0,
    maxSpeed: 1,
    maxEnergy: 1,
  });

  // Animation state
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [animationSpeed, setAnimationSpeed] = useState(1.0);
  const [totalFrames, setTotalFrames] = useState(0);
  const frameRef = useRef(0);
  const lastFrameTimeRef = useRef(0);

  // Premium VIBRANT color palette - Electric neon theme
  const COLORS = useMemo(() => ({
    // Primary elements - ULTRA VIBRANT neon
    arm: 0xff6fff,           // Hot magenta
    armEmissive: 0xff00ff,   // Pure magenta glow
    pendulum: 0x00ffff,      // Electric cyan
    pendulumEmissive: 0x00e5ff, // Bright cyan glow
    pivot: 0xffffff,         // Bright white
    pivotMetal: 0xc0c0c0,    // Silver

    // Mass - dynamic orange/gold (energy reactive)
    mass: 0xff8c00,          // Vivid orange
    massEmissive: 0xff6600,  // Hot orange glow
    massGlow: 0xffaa00,      // Golden glow
    massHighEnergy: 0xff0066, // Pink when high energy
    massLowEnergy: 0x00ff88, // Green when stabilized

    // Environment - darker for contrast
    ground: 0x0a0f1a,        // Deep navy
    groundAccent: 0x1a2744,  // Subtle blue accent
    gridMain: 0x00ffff,      // Cyan grid
    gridSecondary: 0x2a3f5f, // Dim blue-gray

    // Trail effects - rainbow gradient
    trailStart: 0x00ffff,    // Cyan (newest)
    trailMid: 0xff00ff,      // Magenta (middle)
    trailEnd: 0xff6600,      // Orange (oldest)

    // Status - more vivid
    stable: 0x00ff88,        // Bright mint green
    unstable: 0xff3366,      // Hot pink-red

    // Accent colors for physics viz
    velocityArrow: 0xffff00, // Yellow velocity
    forceArrow: 0xff4444,    // Red force
    energyHigh: 0xff0088,    // Pink high energy
    energyLow: 0x00ff88,     // Green low energy

    // Background - deep space
    background: 0x050a15,    // Near black with blue tint
  }), []);

  // Enhanced motion trail configuration
  const TRAIL_LENGTH = 20;
  const TRAIL_OPACITY_START = 0.85;
  const TRAIL_SIZE_START = 0.018;

  // Initialize Three.js scene with premium setup
  const initScene = useCallback(() => {
    if (!containerRef.current) return;

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    // Scene with fog for depth
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(COLORS.background);
    scene.fog = new THREE.Fog(COLORS.background, 1.5, 4);
    sceneRef.current = scene;

    // Camera with cinematic FOV
    const camera = new THREE.PerspectiveCamera(35, width / height, 0.01, 100);
    camera.position.set(0.85, 0.55, 0.85);
    camera.lookAt(0, 0.15, 0);
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
    renderer.toneMappingExposure = 1.2;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    containerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Smooth orbit controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.rotateSpeed = 0.5;
    controls.zoomSpeed = 0.8;
    controls.minDistance = 0.35;
    controls.maxDistance = 2.0;
    controls.maxPolarAngle = Math.PI / 2 + 0.15;
    controls.target.set(0, 0.12, 0);
    controls.update();
    controlsRef.current = controls;

    // Setup scene elements
    setupPremiumLighting(scene);
    setupEnvironment(scene);
    buildPremiumPendulum(scene);
    createMotionTrail(scene);
    addAxisIndicators(scene);

    // Start render loop
    clockRef.current.start();
    const renderLoop = () => {
      const delta = clockRef.current.getDelta();
      const elapsed = clockRef.current.getElapsedTime();

      // Update controls smoothly
      controls.update();

      // Animate glow effects
      updateGlowEffects(elapsed);

      // Smooth position interpolation
      updateSmoothPositions(delta);

      // Update motion trail
      updateMotionTrail();

      renderer.render(scene, camera);
      requestAnimationFrame(renderLoop);
    };
    renderLoop();
  }, [COLORS]);

  // Premium multi-light setup with dramatic neon lighting
  const setupPremiumLighting = (scene) => {
    // Soft ambient - keep low for dramatic contrast
    const ambient = new THREE.AmbientLight(0xffffff, 0.25);
    scene.add(ambient);

    // Hemisphere for subtle sky/ground gradient
    const hemisphere = new THREE.HemisphereLight(0x0066ff, 0xff0066, 0.3);
    scene.add(hemisphere);

    // Key light - main illumination with soft shadows
    const keyLight = new THREE.DirectionalLight(0xffffff, 1.6);
    keyLight.position.set(3, 6, 4);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.width = 2048;
    keyLight.shadow.mapSize.height = 2048;
    keyLight.shadow.camera.near = 0.1;
    keyLight.shadow.camera.far = 20;
    keyLight.shadow.camera.left = -1.5;
    keyLight.shadow.camera.right = 1.5;
    keyLight.shadow.camera.top = 1.5;
    keyLight.shadow.camera.bottom = -1.5;
    keyLight.shadow.bias = -0.0003;
    keyLight.shadow.radius = 3;
    scene.add(keyLight);

    // Cyan accent light - left side
    const cyanLight = new THREE.DirectionalLight(0x00ffff, 0.6);
    cyanLight.position.set(-4, 2, 2);
    scene.add(cyanLight);

    // Magenta accent light - right side
    const magentaLight = new THREE.DirectionalLight(0xff00ff, 0.5);
    magentaLight.position.set(4, 2, -2);
    scene.add(magentaLight);

    // Bottom cyan uplighting
    const bottomCyan = new THREE.DirectionalLight(0x00ffff, 0.25);
    bottomCyan.position.set(0, -2, 0);
    scene.add(bottomCyan);

    // Point light at base - electric cyan glow
    const baseGlow = new THREE.PointLight(0x00ffff, 0.8, 0.8);
    baseGlow.position.set(0, 0.05, 0);
    objectsRef.current.baseGlow = baseGlow;
    scene.add(baseGlow);

    // Dynamic point light that follows mass - energy reactive
    const massLight = new THREE.PointLight(0xff8800, 0.6, 0.5);
    massLight.position.set(0, 0.3, 0);
    objectsRef.current.massLight = massLight;
    scene.add(massLight);

    // Secondary mass light for double glow effect
    const massLight2 = new THREE.PointLight(0xff0066, 0.4, 0.3);
    massLight2.position.set(0, 0.3, 0);
    objectsRef.current.massLight2 = massLight2;
    scene.add(massLight2);
  };

  // Enhanced environment
  const setupEnvironment = (scene) => {
    // Ground with subtle gradient
    const groundGeometry = new THREE.CircleGeometry(1.8, 64);
    const groundMaterial = new THREE.MeshStandardMaterial({
      color: COLORS.ground,
      roughness: 0.9,
      metalness: 0.02,
    });
    const ground = new THREE.Mesh(groundGeometry, groundMaterial);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.002;
    ground.receiveShadow = true;
    scene.add(ground);

    // Inner highlight circle
    const highlightGeometry = new THREE.RingGeometry(0, 0.5, 64);
    const highlightMaterial = new THREE.MeshBasicMaterial({
      color: COLORS.groundAccent,
      transparent: true,
      opacity: 0.35,
    });
    const highlight = new THREE.Mesh(highlightGeometry, highlightMaterial);
    highlight.rotation.x = -Math.PI / 2;
    highlight.position.y = 0.001;
    scene.add(highlight);

    // Radial grid lines
    const gridGroup = new THREE.Group();
    for (let i = 0; i < 16; i++) {
      const angle = (i / 16) * Math.PI * 2;
      const isMain = i % 4 === 0;
      const points = [
        new THREE.Vector3(0.04, 0.003, 0),
        new THREE.Vector3(0.48, 0.003, 0),
      ];
      const geometry = new THREE.BufferGeometry().setFromPoints(points);
      const material = new THREE.LineBasicMaterial({
        color: isMain ? COLORS.gridMain : COLORS.gridSecondary,
        transparent: true,
        opacity: isMain ? 0.45 : 0.2,
      });
      const line = new THREE.Line(geometry, material);
      line.rotation.y = angle;
      gridGroup.add(line);
    }

    // Concentric circles
    [0.12, 0.24, 0.36, 0.48].forEach((r, i) => {
      const isAccent = i === 2;
      const segments = 64;
      const points = [];
      for (let j = 0; j <= segments; j++) {
        const theta = (j / segments) * Math.PI * 2;
        points.push(new THREE.Vector3(Math.cos(theta) * r, 0.003, Math.sin(theta) * r));
      }
      const geometry = new THREE.BufferGeometry().setFromPoints(points);
      const material = new THREE.LineBasicMaterial({
        color: isAccent ? COLORS.gridMain : COLORS.gridSecondary,
        transparent: true,
        opacity: isAccent ? 0.55 : 0.25,
      });
      gridGroup.add(new THREE.Line(geometry, material));
    });
    scene.add(gridGroup);

    // Outer glow ring
    const glowRingGeometry = new THREE.RingGeometry(0.52, 0.56, 64);
    const glowRingMaterial = new THREE.MeshBasicMaterial({
      color: COLORS.gridMain,
      transparent: true,
      opacity: 0.12,
      side: THREE.DoubleSide,
    });
    const outerGlow = new THREE.Mesh(glowRingGeometry, glowRingMaterial);
    outerGlow.rotation.x = -Math.PI / 2;
    outerGlow.position.y = 0.002;
    objectsRef.current.outerGlowRing = outerGlow;
    scene.add(outerGlow);
  };

  // Premium pendulum with ultra-vibrant materials
  const buildPremiumPendulum = (scene) => {
    // Base plate - metallic with cyan edge glow
    const basePlateGeometry = new THREE.CylinderGeometry(0.048, 0.052, 0.014, 32);
    const basePlateMaterial = new THREE.MeshStandardMaterial({
      color: COLORS.pivotMetal,
      roughness: 0.15,
      metalness: 0.95,
    });
    const basePlate = new THREE.Mesh(basePlateGeometry, basePlateMaterial);
    basePlate.position.y = 0.007;
    basePlate.castShadow = true;
    basePlate.receiveShadow = true;
    scene.add(basePlate);

    // Base glow ring
    const baseRingGeometry = new THREE.TorusGeometry(0.05, 0.004, 16, 48);
    const baseRingMaterial = new THREE.MeshBasicMaterial({
      color: 0x00ffff,
      transparent: true,
      opacity: 0.8,
    });
    const baseRing = new THREE.Mesh(baseRingGeometry, baseRingMaterial);
    baseRing.rotation.x = -Math.PI / 2;
    baseRing.position.y = 0.014;
    objectsRef.current.baseRing = baseRing;
    scene.add(baseRing);

    // Motor housing
    const motorGeometry = new THREE.CylinderGeometry(0.032, 0.036, 0.032, 28);
    const motorMaterial = new THREE.MeshStandardMaterial({
      color: COLORS.pivot,
      roughness: 0.2,
      metalness: 0.8,
    });
    const motor = new THREE.Mesh(motorGeometry, motorMaterial);
    motor.position.y = 0.03;
    motor.castShadow = true;
    scene.add(motor);

    // Shaft with chrome finish
    const shaftGeometry = new THREE.CylinderGeometry(0.008, 0.008, 0.022, 20);
    const shaftMaterial = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      roughness: 0.05,
      metalness: 1.0,
    });
    const shaft = new THREE.Mesh(shaftGeometry, shaftMaterial);
    shaft.position.y = 0.057;
    shaft.castShadow = true;
    scene.add(shaft);

    // Arm group (rotates around Y)
    const armGroup = new THREE.Group();
    armGroup.position.y = 0.068;
    objectsRef.current.armGroup = armGroup;
    scene.add(armGroup);

    // Arm hub with intense magenta glow
    const hubGeometry = new THREE.CylinderGeometry(0.016, 0.016, 0.014, 24);
    const hubMaterial = new THREE.MeshStandardMaterial({
      color: COLORS.arm,
      roughness: 0.2,
      metalness: 0.6,
      emissive: COLORS.armEmissive,
      emissiveIntensity: 0.6,
    });
    const hub = new THREE.Mesh(hubGeometry, hubMaterial);
    hub.castShadow = true;
    objectsRef.current.hub = hub;
    armGroup.add(hub);

    // Arm rod - hot magenta with glow
    const armLength = 0.2;
    const armGeometry = new THREE.CylinderGeometry(0.006, 0.008, armLength, 14);
    const armMaterial = new THREE.MeshStandardMaterial({
      color: COLORS.arm,
      roughness: 0.15,
      metalness: 0.7,
      emissive: COLORS.armEmissive,
      emissiveIntensity: 0.5,
    });
    const arm = new THREE.Mesh(armGeometry, armMaterial);
    arm.rotation.z = Math.PI / 2;
    arm.position.x = armLength / 2;
    arm.castShadow = true;
    objectsRef.current.arm = arm;
    objectsRef.current.armMaterial = armMaterial;
    armGroup.add(arm);

    // Joint sphere - bright white
    const jointGeometry = new THREE.SphereGeometry(0.012, 24, 24);
    const jointMaterial = new THREE.MeshStandardMaterial({
      color: COLORS.pivot,
      roughness: 0.1,
      metalness: 0.9,
    });
    const joint = new THREE.Mesh(jointGeometry, jointMaterial);
    joint.position.set(armLength, 0, 0);
    joint.castShadow = true;
    objectsRef.current.joint = joint;
    armGroup.add(joint);

    // Decorative joint ring - cyan glow
    const jointRingGeometry = new THREE.TorusGeometry(0.016, 0.003, 12, 28);
    const jointRingMaterial = new THREE.MeshBasicMaterial({
      color: 0x00ffff,
      transparent: true,
      opacity: 0.9,
    });
    const jointRing = new THREE.Mesh(jointRingGeometry, jointRingMaterial);
    jointRing.position.set(armLength, 0, 0);
    jointRing.rotation.x = Math.PI / 2;
    objectsRef.current.jointRing = jointRing;
    armGroup.add(jointRing);

    // Pendulum group (swings around local X after arm rotation)
    const pendulumGroup = new THREE.Group();
    pendulumGroup.position.set(armLength, 0, 0);
    objectsRef.current.pendulumGroup = pendulumGroup;
    armGroup.add(pendulumGroup);

    // Pendulum rod - electric cyan
    const pendulumLength = 0.3;
    const pendulumGeometry = new THREE.CylinderGeometry(0.005, 0.006, pendulumLength, 14);
    const pendulumMaterial = new THREE.MeshStandardMaterial({
      color: COLORS.pendulum,
      roughness: 0.12,
      metalness: 0.6,
      emissive: COLORS.pendulumEmissive,
      emissiveIntensity: 0.65,
    });
    const pendulum = new THREE.Mesh(pendulumGeometry, pendulumMaterial);
    pendulum.position.y = pendulumLength / 2;
    pendulum.castShadow = true;
    objectsRef.current.pendulum = pendulum;
    objectsRef.current.pendulumMaterial = pendulumMaterial;
    pendulumGroup.add(pendulum);

    // Mass bob - ENERGY REACTIVE (changes color with speed/energy)
    const massGeometry = new THREE.SphereGeometry(0.024, 36, 36);
    const massMaterial = new THREE.MeshStandardMaterial({
      color: COLORS.mass,
      roughness: 0.08,
      metalness: 0.5,
      emissive: COLORS.massEmissive,
      emissiveIntensity: 0.7,
    });
    const mass = new THREE.Mesh(massGeometry, massMaterial);
    mass.position.y = pendulumLength;
    mass.castShadow = true;
    objectsRef.current.mass = mass;
    objectsRef.current.massMaterial = massMaterial;
    pendulumGroup.add(mass);

    // Inner glow sphere - larger, more visible
    const glowGeometry = new THREE.SphereGeometry(0.032, 28, 28);
    const glowMaterial = new THREE.MeshBasicMaterial({
      color: COLORS.massGlow,
      transparent: true,
      opacity: 0.35,
    });
    const massGlow = new THREE.Mesh(glowGeometry, glowMaterial);
    massGlow.position.y = pendulumLength;
    objectsRef.current.massGlow = massGlow;
    objectsRef.current.massGlowMaterial = glowMaterial;
    pendulumGroup.add(massGlow);

    // Outer glow sphere - even larger, subtle
    const outerGlowGeometry = new THREE.SphereGeometry(0.042, 24, 24);
    const outerGlowMaterial = new THREE.MeshBasicMaterial({
      color: COLORS.massGlow,
      transparent: true,
      opacity: 0.15,
    });
    const outerMassGlow = new THREE.Mesh(outerGlowGeometry, outerGlowMaterial);
    outerMassGlow.position.y = pendulumLength;
    objectsRef.current.outerMassGlow = outerMassGlow;
    objectsRef.current.outerMassGlowMaterial = outerGlowMaterial;
    pendulumGroup.add(outerMassGlow);

    // Status ring (inner) - more vibrant
    const statusRingGeometry = new THREE.TorusGeometry(0.032, 0.004, 16, 48);
    const statusRingMaterial = new THREE.MeshBasicMaterial({
      color: isStable ? COLORS.stable : COLORS.unstable,
      transparent: true,
      opacity: 0.95,
    });
    const statusRing = new THREE.Mesh(statusRingGeometry, statusRingMaterial);
    statusRing.position.y = pendulumLength;
    statusRing.rotation.x = Math.PI / 2;
    objectsRef.current.statusRing = statusRing;
    pendulumGroup.add(statusRing);

    // Outer pulsing ring - more dramatic
    const outerStatusGeometry = new THREE.TorusGeometry(0.042, 0.002, 12, 48);
    const outerStatusMaterial = new THREE.MeshBasicMaterial({
      color: isStable ? COLORS.stable : COLORS.unstable,
      transparent: true,
      opacity: 0.5,
    });
    const outerStatusRing = new THREE.Mesh(outerStatusGeometry, outerStatusMaterial);
    outerStatusRing.position.y = pendulumLength;
    outerStatusRing.rotation.x = Math.PI / 2;
    objectsRef.current.outerStatusRing = outerStatusRing;
    pendulumGroup.add(outerStatusRing);

    // Trajectory line (full path, dimmed cyan)
    const trajectoryMaterial = new THREE.LineBasicMaterial({
      color: 0x00ffff,
      transparent: true,
      opacity: 0.15,
    });
    const trajectoryGeometry = new THREE.BufferGeometry();
    const trajectoryLine = new THREE.Line(trajectoryGeometry, trajectoryMaterial);
    objectsRef.current.trajectoryLine = trajectoryLine;
    scene.add(trajectoryLine);

    // Played trajectory (bright, follows playback)
    const playedMaterial = new THREE.LineBasicMaterial({
      color: 0x00ffff,
      transparent: true,
      opacity: 0.85,
      linewidth: 2,
    });
    const playedGeometry = new THREE.BufferGeometry();
    const playedLine = new THREE.Line(playedGeometry, playedMaterial);
    objectsRef.current.playedLine = playedLine;
    scene.add(playedLine);
  };

  // Create motion trail spheres with rainbow gradient
  const createMotionTrail = (scene) => {
    const trailGroup = new THREE.Group();
    trailRef.current = [];

    for (let i = 0; i < TRAIL_LENGTH; i++) {
      const t = i / TRAIL_LENGTH;
      const size = TRAIL_SIZE_START * (1 - t * 0.5);
      const opacity = TRAIL_OPACITY_START * Math.pow(1 - t, 0.7);

      // Rainbow gradient: cyan -> magenta -> orange
      const color = new THREE.Color();
      if (t < 0.5) {
        // Cyan to Magenta
        color.setHex(COLORS.trailStart);
        color.lerp(new THREE.Color(COLORS.trailMid), t * 2);
      } else {
        // Magenta to Orange
        color.setHex(COLORS.trailMid);
        color.lerp(new THREE.Color(COLORS.trailEnd), (t - 0.5) * 2);
      }

      const geometry = new THREE.SphereGeometry(size, 16, 16);
      const material = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: opacity,
      });
      const sphere = new THREE.Mesh(geometry, material);
      sphere.visible = false;
      trailGroup.add(sphere);
      trailRef.current.push({
        mesh: sphere,
        position: new THREE.Vector3(0, 0, 0),
        active: false,
        baseOpacity: opacity,
      });
    }

    objectsRef.current.trailGroup = trailGroup;
    scene.add(trailGroup);
  };

  // Update motion trail positions with speed-reactive opacity
  const updateMotionTrail = () => {
    if (!objectsRef.current.mass || !trailRef.current.length) return;

    // Get current mass world position
    const massWorldPos = new THREE.Vector3();
    objectsRef.current.mass.getWorldPosition(massWorldPos);

    // Get speed ratio for opacity boost
    const physics = physicsStateRef.current;
    const speedRatio = physics.maxSpeed > 0 ? physics.currentSpeed / physics.maxSpeed : 0;
    const opacityBoost = 0.6 + speedRatio * 0.4; // More visible when fast

    // Shift trail positions
    for (let i = TRAIL_LENGTH - 1; i > 0; i--) {
      trailRef.current[i].position.copy(trailRef.current[i - 1].position);
      trailRef.current[i].active = trailRef.current[i - 1].active;
    }

    // Add new position at front
    trailRef.current[0].position.copy(massWorldPos);
    trailRef.current[0].active = true;

    // Update mesh positions, visibility, and opacity
    trailRef.current.forEach((trail, i) => {
      trail.mesh.visible = trail.active && i > 0;
      if (trail.active) {
        trail.mesh.position.copy(trail.position);
        // Boost opacity based on speed
        trail.mesh.material.opacity = trail.baseOpacity * opacityBoost;
      }
    });
  };

  // Animate glow effects with physics-reactive behavior
  const updateGlowEffects = (elapsed) => {
    glowPulseRef.current = elapsed;
    const physics = physicsStateRef.current;
    const normalizedEnergy = physics.normalizedEnergy || 0;
    const speedRatio = physics.maxSpeed > 0 ? physics.currentSpeed / physics.maxSpeed : 0;

    // Pulse the outer status ring - faster when high energy
    if (objectsRef.current.outerStatusRing) {
      const pulseSpeed = 3 + speedRatio * 4;
      const pulse = 0.4 + Math.sin(elapsed * pulseSpeed) * 0.25;
      objectsRef.current.outerStatusRing.material.opacity = pulse;
      const scale = 1 + Math.sin(elapsed * 2.5) * 0.1 + speedRatio * 0.15;
      objectsRef.current.outerStatusRing.scale.setScalar(scale);
    }

    // Pulse the mass glow - brighter when moving fast
    if (objectsRef.current.massGlow) {
      const baseGlow = 0.25 + speedRatio * 0.4;
      const glowPulse = baseGlow + Math.sin(elapsed * 5) * 0.1;
      objectsRef.current.massGlow.material.opacity = glowPulse;
    }

    // Outer mass glow - even more reactive
    if (objectsRef.current.outerMassGlow) {
      const outerGlow = 0.1 + speedRatio * 0.3;
      objectsRef.current.outerMassGlow.material.opacity = outerGlow;
    }

    // Dynamic mass color based on energy/speed
    if (objectsRef.current.massMaterial) {
      const massColor = new THREE.Color(COLORS.mass);
      if (speedRatio > 0.5) {
        // High speed - shift toward pink/red
        massColor.lerp(new THREE.Color(COLORS.massHighEnergy), (speedRatio - 0.5) * 2);
      } else if (isStable && speedRatio < 0.2) {
        // Stable and slow - shift toward green
        massColor.lerp(new THREE.Color(COLORS.massLowEnergy), (0.2 - speedRatio) * 5 * 0.5);
      }
      objectsRef.current.massMaterial.color.copy(massColor);
      objectsRef.current.massMaterial.emissiveIntensity = 0.5 + speedRatio * 0.5;
    }

    // Mass glow color follows mass color
    if (objectsRef.current.massGlowMaterial) {
      const glowColor = new THREE.Color(COLORS.massGlow);
      if (speedRatio > 0.5) {
        glowColor.lerp(new THREE.Color(COLORS.massHighEnergy), (speedRatio - 0.5) * 2);
      }
      objectsRef.current.massGlowMaterial.color.copy(glowColor);
    }

    // Subtle base glow pulsing
    if (objectsRef.current.baseGlow) {
      objectsRef.current.baseGlow.intensity = 0.6 + Math.sin(elapsed * 2) * 0.2;
    }

    // Base ring pulse
    if (objectsRef.current.baseRing) {
      const ringPulse = 0.7 + Math.sin(elapsed * 3) * 0.15;
      objectsRef.current.baseRing.material.opacity = ringPulse;
    }

    // Joint ring pulse
    if (objectsRef.current.jointRing) {
      const jRingPulse = 0.8 + Math.sin(elapsed * 4) * 0.1;
      objectsRef.current.jointRing.material.opacity = jRingPulse;
    }

    // Mass light follows mass position - intensity based on speed
    if (objectsRef.current.massLight && objectsRef.current.mass) {
      const massPos = new THREE.Vector3();
      objectsRef.current.mass.getWorldPosition(massPos);
      objectsRef.current.massLight.position.copy(massPos);
      objectsRef.current.massLight.intensity = 0.4 + speedRatio * 0.6;
    }

    // Secondary mass light
    if (objectsRef.current.massLight2 && objectsRef.current.mass) {
      const massPos = new THREE.Vector3();
      objectsRef.current.mass.getWorldPosition(massPos);
      objectsRef.current.massLight2.position.copy(massPos);
      objectsRef.current.massLight2.intensity = 0.2 + speedRatio * 0.4;
    }

    // Pendulum rod emissive intensity based on motion
    if (objectsRef.current.pendulumMaterial) {
      objectsRef.current.pendulumMaterial.emissiveIntensity = 0.5 + speedRatio * 0.3;
    }

    // Arm emissive intensity
    if (objectsRef.current.armMaterial) {
      objectsRef.current.armMaterial.emissiveIntensity = 0.4 + speedRatio * 0.3;
    }
  };

  // Smooth position interpolation for buttery animation
  const updateSmoothPositions = (delta) => {
    const state = animationStateRef.current;
    const smoothFactor = 1 - Math.pow(0.001, delta); // Framerate-independent smoothing

    // Smoothly interpolate arm rotation
    state.currentPhi = lerpAngle(state.currentPhi, state.targetPhi, smoothFactor);

    // Smoothly interpolate pendulum angle
    state.currentTheta = lerp(state.currentTheta, state.targetTheta, smoothFactor);

    // Apply smoothed rotations
    if (objectsRef.current.armGroup) {
      objectsRef.current.armGroup.rotation.y = state.currentPhi;
    }
    if (objectsRef.current.pendulumGroup) {
      objectsRef.current.pendulumGroup.rotation.x = state.currentTheta;
    }
  };

  // Axis indicators
  const addAxisIndicators = (scene) => {
    const axisLength = 0.08;
    const axisGroup = new THREE.Group();
    axisGroup.position.set(0.45, 0.01, -0.45);

    const createAxis = (dir, color) => {
      const points = [new THREE.Vector3(0, 0, 0), dir.clone().multiplyScalar(axisLength)];
      const geometry = new THREE.BufferGeometry().setFromPoints(points);
      const material = new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.7 });
      return new THREE.Line(geometry, material);
    };

    axisGroup.add(createAxis(new THREE.Vector3(1, 0, 0), 0xf87171));
    axisGroup.add(createAxis(new THREE.Vector3(0, 1, 0), 0x4ade80));
    axisGroup.add(createAxis(new THREE.Vector3(0, 0, 1), 0x60a5fa));

    scene.add(axisGroup);
  };

  // Update target positions from trajectory data
  const updateTargetPositions = useCallback((viz3D, frameIndex) => {
    if (!viz3D?.arm_trajectory || !viz3D?.pendulum_trajectory) return;

    const { arm_trajectory, pendulum_trajectory, arm_length, pendulum_length,
            velocities, energies, max_speed, max_energy, min_energy } = viz3D;

    const trajectoryLength = arm_trajectory.length;
    if (trajectoryLength === 0) return;

    // Clamp frame index to valid range
    const safeFrameIndex = Math.max(0, Math.min(frameIndex, trajectoryLength - 1));

    // Update physics state from trajectory data with bounds checking
    const floorFrameForPhysics = Math.floor(safeFrameIndex);
    const safePhysicsIndex = Math.min(floorFrameForPhysics, trajectoryLength - 1);

    if (velocities && velocities.length > safePhysicsIndex && velocities[safePhysicsIndex]) {
      const vel = velocities[safePhysicsIndex];
      physicsStateRef.current.currentSpeed = vel[3] || 0; // speed is index 3
      physicsStateRef.current.maxSpeed = max_speed || 1;
    }
    if (energies && energies.length > safePhysicsIndex && energies[safePhysicsIndex] !== undefined) {
      physicsStateRef.current.currentEnergy = energies[safePhysicsIndex];
      physicsStateRef.current.maxEnergy = max_energy || 1;
      const range = (max_energy || 1) - (min_energy || 0);
      physicsStateRef.current.normalizedEnergy = range > 0
        ? (energies[safePhysicsIndex] - (min_energy || 0)) / range
        : 0;
    }

    // Interpolate between frames for ultra-smooth animation
    const floorFrame = Math.max(0, Math.min(Math.floor(safeFrameIndex), trajectoryLength - 1));
    const ceilFrame = Math.min(floorFrame + 1, trajectoryLength - 1);
    const t = safeFrameIndex - floorFrame;

    const armPosFloor = arm_trajectory[floorFrame];
    const armPosCeil = arm_trajectory[ceilFrame];
    const pendPosFloor = pendulum_trajectory[floorFrame];
    const pendPosCeil = pendulum_trajectory[ceilFrame];

    if (!armPosFloor || !pendPosFloor) return;

    // Interpolate arm position
    const armX = lerp(armPosFloor[0], armPosCeil?.[0] ?? armPosFloor[0], t);
    const armY = lerp(armPosFloor[1], armPosCeil?.[1] ?? armPosFloor[1], t);

    // Interpolate pendulum position
    const pendX = lerp(pendPosFloor[0], pendPosCeil?.[0] ?? pendPosFloor[0], t);
    const pendY = lerp(pendPosFloor[1], pendPosCeil?.[1] ?? pendPosFloor[1], t);
    const pendZ = lerp(pendPosFloor[2], pendPosCeil?.[2] ?? pendPosFloor[2], t);

    // Calculate target angles
    const phi = Math.atan2(armY, armX);
    const dx = pendX - armX;
    const dy = pendY - armY;
    const horizontalDist = Math.sqrt(dx * dx + dy * dy);
    const theta = Math.atan2(horizontalDist, pendZ);

    // Determine swing direction
    const perpX = -Math.sin(phi);
    const perpY = Math.cos(phi);
    const dotProduct = dx * perpX + dy * perpY;

    // Set target values for smooth interpolation
    animationStateRef.current.targetPhi = phi;
    animationStateRef.current.targetTheta = dotProduct >= 0 ? theta : -theta;

    // Update geometry scales
    if (arm_length && objectsRef.current.arm) {
      const armScale = arm_length / 0.2;
      objectsRef.current.arm.scale.y = armScale;
      objectsRef.current.arm.position.x = arm_length / 2;
      if (objectsRef.current.joint) {
        objectsRef.current.joint.position.x = arm_length;
      }
      objectsRef.current.pendulumGroup.position.x = arm_length;
    }

    if (pendulum_length && objectsRef.current.pendulum) {
      const pendScale = pendulum_length / 0.3;
      objectsRef.current.pendulum.scale.y = pendScale;
      objectsRef.current.pendulum.position.y = pendulum_length / 2;
      objectsRef.current.mass.position.y = pendulum_length;
      objectsRef.current.massGlow.position.y = pendulum_length;
      objectsRef.current.statusRing.position.y = pendulum_length;
      objectsRef.current.outerStatusRing.position.y = pendulum_length;
    }

    // Update trajectory visualizations with error handling
    try {
      if (pendulum_trajectory.length > 1 && objectsRef.current.trajectoryLine) {
        const fullPoints = pendulum_trajectory
          .filter(pos => pos && pos.length >= 3)
          .map(pos => new THREE.Vector3(pos[0], pos[2], pos[1]));
        if (fullPoints.length > 0) {
          objectsRef.current.trajectoryLine.geometry.dispose();
          objectsRef.current.trajectoryLine.geometry = new THREE.BufferGeometry().setFromPoints(fullPoints);
        }
      }

      if (pendulum_trajectory.length > 1 && floorFrame > 0 && objectsRef.current.playedLine) {
        const endIndex = Math.min(floorFrame + 1, pendulum_trajectory.length);
        const playedPoints = pendulum_trajectory.slice(0, endIndex)
          .filter(pos => pos && pos.length >= 3)
          .map(pos => new THREE.Vector3(pos[0], pos[2], pos[1]));
        if (playedPoints.length > 0) {
          objectsRef.current.playedLine.geometry.dispose();
          objectsRef.current.playedLine.geometry = new THREE.BufferGeometry().setFromPoints(playedPoints);
        }
      }
    } catch (e) {
      // Silently handle geometry update errors during rapid data changes
      console.debug('Trajectory update skipped:', e.message);
    }

    // Update status ring colors
    const statusColor = isStable ? COLORS.stable : COLORS.unstable;
    if (objectsRef.current.statusRing) {
      objectsRef.current.statusRing.material.color.setHex(statusColor);
    }
    if (objectsRef.current.outerStatusRing) {
      objectsRef.current.outerStatusRing.material.color.setHex(statusColor);
    }
  }, [isStable, COLORS]);

  // Animation loop with smooth frame advancement
  useEffect(() => {
    if (!isPlaying || totalFrames === 0) return;

    let animationId;
    let isRunning = true;

    const animate = (timestamp) => {
      if (!isRunning) return;

      if (!lastFrameTimeRef.current) lastFrameTimeRef.current = timestamp;

      const deltaTime = Math.min(timestamp - lastFrameTimeRef.current, 100); // Cap delta to prevent jumps
      lastFrameTimeRef.current = timestamp;

      // Smooth frame advancement (real-time playback)
      const frameAdvance = (deltaTime / 1000) * 50 * animationSpeed; // 50 fps source data

      frameRef.current += frameAdvance;

      // Clamp and loop with current totalFrames value
      const currentTotalFrames = totalFrames;
      if (currentTotalFrames > 0) {
        if (frameRef.current >= currentTotalFrames) {
          frameRef.current = 0; // Loop
        }
        if (frameRef.current < 0) {
          frameRef.current = 0;
        }
      }

      setCurrentFrame(Math.max(0, frameRef.current));
      animationId = requestAnimationFrame(animate);
    };

    animationId = requestAnimationFrame(animate);

    return () => {
      isRunning = false;
      if (animationId) cancelAnimationFrame(animationId);
    };
  }, [isPlaying, totalFrames, animationSpeed]);

  // Update positions when frame changes
  useEffect(() => {
    if (visualization3D) {
      updateTargetPositions(visualization3D, currentFrame);
    }
  }, [currentFrame, visualization3D, updateTargetPositions]);

  // Track trajectory changes - use data signature to detect actual changes
  const prevDataSignatureRef = useRef(null);
  const dataVersionRef = useRef(0);

  useEffect(() => {
    if (!visualization3D?.pendulum_trajectory || visualization3D.pendulum_trajectory.length === 0) {
      return;
    }

    const trajectory = visualization3D.pendulum_trajectory;
    const newLength = trajectory.length;

    // Create a signature from first, middle, and last positions to detect data changes
    const first = trajectory[0];
    const mid = trajectory[Math.floor(newLength / 2)];
    const last = trajectory[newLength - 1];
    const newSignature = first && mid && last
      ? `${first[0].toFixed(4)}_${first[2].toFixed(4)}_${mid[0].toFixed(4)}_${last[0].toFixed(4)}_${last[2].toFixed(4)}`
      : null;

    const prevSignature = prevDataSignatureRef.current;
    const dataChanged = newSignature !== prevSignature;

    setTotalFrames(newLength);

    if (prevSignature === null) {
      // First load - auto-play from start
      frameRef.current = 0;
      setCurrentFrame(0);
      setIsPlaying(true);
      dataVersionRef.current++;
    } else if (dataChanged) {
      // Parameter changed - RESET animation to start and auto-play
      frameRef.current = 0;
      setCurrentFrame(0);
      lastFrameTimeRef.current = 0; // Reset time reference
      setIsPlaying(true); // Auto-play new simulation
      dataVersionRef.current++;

      // Reset physics state for new data
      physicsStateRef.current = {
        currentSpeed: 0,
        currentEnergy: 0,
        normalizedEnergy: 0,
        maxSpeed: visualization3D.max_speed || 1,
        maxEnergy: visualization3D.max_energy || 1,
      };

      // Reset animation interpolation state for immediate response
      animationStateRef.current = {
        currentPhi: 0,
        currentTheta: 0,
        targetPhi: 0,
        targetTheta: 0,
        velocity: { phi: 0, theta: 0 },
      };

      // Clear motion trail for fresh start
      if (trailRef.current) {
        trailRef.current.forEach(trail => {
          trail.active = false;
          trail.mesh.visible = false;
        });
      }
    }

    prevDataSignatureRef.current = newSignature;
  }, [visualization3D]);

  // Resize handler
  const handleResize = useCallback(() => {
    if (!containerRef.current || !rendererRef.current || !cameraRef.current) return;
    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;
    cameraRef.current.aspect = width / height;
    cameraRef.current.updateProjectionMatrix();
    rendererRef.current.setSize(width, height);
  }, []);

  // Update status ring colors whenever isStable changes
  useEffect(() => {
    const statusColor = isStable ? COLORS.stable : COLORS.unstable;
    if (objectsRef.current.statusRing) {
      objectsRef.current.statusRing.material.color.setHex(statusColor);
    }
    if (objectsRef.current.outerStatusRing) {
      objectsRef.current.outerStatusRing.material.color.setHex(statusColor);
    }
  }, [isStable, COLORS]);

  // Notify parent of frame changes for dynamic info panel updates
  useEffect(() => {
    if (onFrameChange && visualization3D) {
      onFrameChange(Math.floor(currentFrame), totalFrames);
    }
  }, [currentFrame, totalFrames, onFrameChange, visualization3D]);

  // Initialize scene
  useEffect(() => {
    initScene();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (rendererRef.current && containerRef.current) {
        containerRef.current.removeChild(rendererRef.current.domElement);
        rendererRef.current.dispose();
      }
      if (controlsRef.current) controlsRef.current.dispose();
    };
  }, [initScene, handleResize]);

  // Control handlers
  const togglePlayPause = () => {
    lastFrameTimeRef.current = 0;
    setIsPlaying(prev => !prev);
  };

  const resetAnimation = () => {
    frameRef.current = 0;
    setCurrentFrame(0);
    setIsPlaying(false);
    // Reset smooth interpolation state
    animationStateRef.current = {
      currentPhi: 0,
      currentTheta: 0,
      targetPhi: 0,
      targetTheta: 0,
    };
  };

  const handleScrubberChange = (e) => {
    const newFrame = parseFloat(e.target.value);
    frameRef.current = newFrame;
    setCurrentFrame(newFrame);
    setIsPlaying(false);
  };

  const handleSpeedChange = (e) => setAnimationSpeed(parseFloat(e.target.value));

  const formatTime = (frame) => {
    const time = (frame * 0.02).toFixed(2); // 50 fps = 0.02s per frame
    return `${time}s`;
  };

  return (
    <div className="furuta-3d-wrapper">
      <div className="furuta-3d-container" ref={containerRef}>
        <div className="furuta-3d-overlay">
          <span className={`status-badge ${isStable ? 'stable' : 'unstable'}`}>
            {isStable ? '● STABLE' : '○ UNSTABLE'}
          </span>
        </div>
        <div className="camera-hint">
          <span>Drag to rotate • Scroll to zoom</span>
        </div>
      </div>

      <div className="animation-controls">
        <div className="controls-row">
          <button
            className={`control-btn play-btn ${isPlaying ? 'playing' : ''}`}
            onClick={togglePlayPause}
            aria-label={isPlaying ? 'Pause' : 'Play'}
            style={{ minWidth: '40px', minHeight: '40px' }}
          >
            {isPlaying ? (
              <span style={{ fontSize: '18px', lineHeight: 1 }}>⏸</span>
            ) : (
              <span style={{ fontSize: '18px', lineHeight: 1 }}>▶</span>
            )}
          </button>

          <button
            className="control-btn reset-btn"
            onClick={resetAnimation}
            aria-label="Reset"
            style={{ minWidth: '40px', minHeight: '40px' }}
          >
            <span style={{ fontSize: '16px', lineHeight: 1 }}>↺</span>
          </button>

          <div className="time-display">
            <span className="current-time">{formatTime(currentFrame)}</span>
            <span className="time-separator">/</span>
            <span className="total-time">{formatTime(totalFrames)}</span>
          </div>

          <div className="speed-control">
            <label htmlFor="speed-slider">Speed:</label>
            <select
              id="speed-slider"
              value={animationSpeed}
              onChange={handleSpeedChange}
              className="speed-select"
            >
              <option value="0.25">0.25x</option>
              <option value="0.5">0.5x</option>
              <option value="1">1x</option>
              <option value="2">2x</option>
              <option value="4">4x</option>
            </select>
          </div>
        </div>

        <div className="timeline-row">
          <input
            type="range"
            min="0"
            max={Math.max(totalFrames - 1, 1)}
            step="0.1"
            value={currentFrame}
            onChange={handleScrubberChange}
            className="timeline-scrubber"
            aria-label="Animation timeline"
          />
        </div>
      </div>
    </div>
  );
}

export default FurutaPendulum3D;
