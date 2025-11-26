// Avatar3D.jsx — Avatar PRO para 153 keypoints (9 pose + 2 manos)

import { useEffect, useRef } from "react";
import * as THREE from "three";

export default function Avatar3D({ pose }) {
  const mountRef = useRef(null);
  const rigRef = useRef(null);
  const poseRef = useRef(pose);

  // Cuando cambia el frame desde el reproductor
  useEffect(() => {
    poseRef.current = pose;
  }, [pose]);

  // Inicializar Three.js solo una vez
  useEffect(() => {
    const container = mountRef.current;
    const width = container.clientWidth || 800;
    const height = 420;

    // === ESCENA ===
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x020617);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 20);
    camera.position.set(0, 1.2, 4);
    camera.lookAt(0, 1, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    // Luces
    scene.add(new THREE.AmbientLight(0xffffff, 0.9));
    const dir = new THREE.DirectionalLight(0xffffff, 1.3);
    dir.position.set(2, 4, 3);
    scene.add(dir);

    // ROOT
    const root = new THREE.Group();
    scene.add(root);

    // ------------- JOINTS (esferas) -------------
    const jointGeo = new THREE.SphereGeometry(0.06, 12, 12);
    const jointMat = new THREE.MeshStandardMaterial({ color: 0xffffff });

    const joints = {};
    const jointNames = [
      "nose",
      "lShoulder",
      "rShoulder",
      "lElbow",
      "rElbow",
      "lWrist",
      "rWrist",
      "lHip",
      "rHip",
    ];

    jointNames.forEach((name) => {
      joints[name] = new THREE.Mesh(jointGeo, jointMat);
      root.add(joints[name]);
    });

    // ------------- MANOS (21 puntos por mano) -------------
    const handPointGeo = new THREE.SphereGeometry(0.04, 12, 12);
    const leftHandMat = new THREE.MeshStandardMaterial({ color: 0xffd400 });
    const rightHandMat = new THREE.MeshStandardMaterial({ color: 0x00e5ff });

    joints.leftHand = [];
    joints.rightHand = [];

    for (let i = 0; i < 21; i++) {
      const lp = new THREE.Mesh(handPointGeo, leftHandMat);
      const rp = new THREE.Mesh(handPointGeo, rightHandMat);
      root.add(lp, rp);
      joints.leftHand.push(lp);
      joints.rightHand.push(rp);
    }

    // ------------- HUESOS (cilindros) -------------
    const boneGeo = new THREE.CylinderGeometry(0.035, 0.035, 1, 10);
    const boneMat = new THREE.MeshStandardMaterial({ color: 0xb0c4de });

    function makeBone() {
      const m = new THREE.Mesh(boneGeo, boneMat);
      root.add(m);
      return m;
    }

    const bones = {
      torso: makeBone(), // hombros ↔ caderas
      lUpperArm: makeBone(), // hombro izq ↔ codo izq
      lLowerArm: makeBone(), // codo izq ↔ muñeca izq
      rUpperArm: makeBone(), // hombro der ↔ codo der
      rLowerArm: makeBone(), // codo der ↔ muñeca der
    };

    // Guardamos todo en el rig
    rigRef.current = {
      joints,
      bones,
      prev: null, // para suavizado
    };

    // ------------- LOOP DE ANIMACIÓN -------------
    const animate = () => {
      requestAnimationFrame(animate);

      if (poseRef.current && rigRef.current) {
        updateFrame153(poseRef.current, rigRef.current);
      }

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      renderer.dispose();
      container.innerHTML = "";
    };
  }, []);

  return (
    <div
      ref={mountRef}
      style={{
        width: "100%",
        height: "420px",
        border: "1px solid #1e293b",
        borderRadius: "6px",
      }}
    />
  );
}

// ============================================
//      REPRODUCTOR PARA 153 VALORES
// ============================================

const SCALE = 1.8;
const OFFSET_Y = 1.0;

function mpToWorld(mp, center) {
  return new THREE.Vector3(
    (mp.x - center.x) * SCALE,
    (center.y - mp.y) * SCALE + OFFSET_Y,
    0.25
  );
}

function updateBone(mesh, a, b) {
  const mid = a.clone().add(b).multiplyScalar(0.5);
  const dir = b.clone().sub(a);
  const length = dir.length() || 0.0001;

  mesh.position.copy(mid);
  mesh.scale.set(1, length, 1);

  dir.normalize();
  const q = new THREE.Quaternion().setFromUnitVectors(
    new THREE.Vector3(0, 1, 0),
    dir
  );
  mesh.setRotationFromQuaternion(q);
}

function updateFrame153(arr, rig) {
  if (!arr || arr.length !== 153) return;

  const { joints, bones } = rig;

  const read = (i) => ({ x: arr[i], y: arr[i + 1], z: arr[i + 2] });

  let o = 0;

  // ---- POSE (9 puntos) ----
  const nose = read(o); o += 3;
  const lS = read(o);   o += 3;
  const rS = read(o);   o += 3;
  const lE = read(o);   o += 3;
  const rE = read(o);   o += 3;
  const lW = read(o);   o += 3;
  const rW = read(o);   o += 3;
  const lH = read(o);   o += 3;
  const rH = read(o);   o += 3;

  const center = {
    x: (lS.x + rS.x) / 2,
    y: (lS.y + rS.y) / 2,
  };

  // Pasar a coordenadas de mundo
  const world = {
    nose: mpToWorld(nose, center),
    lShoulder: mpToWorld(lS, center),
    rShoulder: mpToWorld(rS, center),
    lElbow: mpToWorld(lE, center),
    rElbow: mpToWorld(rE, center),
    lWrist: mpToWorld(lW, center),
    rWrist: mpToWorld(rW, center),
    lHip: mpToWorld(lH, center),
    rHip: mpToWorld(rH, center),
    leftHand: [],
    rightHand: [],
  };

  for (let i = 0; i < 21; i++) {
    const lh = read(o); o += 3;
    world.leftHand.push(mpToWorld(lh, center));
  }

  for (let i = 0; i < 21; i++) {
    const rh = read(o); o += 3;
    world.rightHand.push(mpToWorld(rh, center));
  }

  // --------- SUAVIZADO ---------
  if (!rig.prev) {
    rig.prev = {
      ...world,
      leftHand: world.leftHand.map((v) => v.clone()),
      rightHand: world.rightHand.map((v) => v.clone()),
    };
  } else {
    const alpha = 0.35; // factor de suavizado

    const keys = [
      "nose",
      "lShoulder",
      "rShoulder",
      "lElbow",
      "rElbow",
      "lWrist",
      "rWrist",
      "lHip",
      "rHip",
    ];

    keys.forEach((k) => {
      rig.prev[k].lerp(world[k], alpha);
    });

    for (let i = 0; i < 21; i++) {
      rig.prev.leftHand[i].lerp(world.leftHand[i], alpha);
      rig.prev.rightHand[i].lerp(world.rightHand[i], alpha);
    }
  }

  const p = rig.prev;

  // --------- PONER ESFERAS ---------
  joints.nose.position.copy(p.nose);
  joints.lShoulder.position.copy(p.lShoulder);
  joints.rShoulder.position.copy(p.rShoulder);
  joints.lElbow.position.copy(p.lElbow);
  joints.rElbow.position.copy(p.rElbow);
  joints.lWrist.position.copy(p.lWrist);
  joints.rWrist.position.copy(p.rWrist);
  joints.lHip.position.copy(p.lHip);
  joints.rHip.position.copy(p.rHip);

  for (let i = 0; i < 21; i++) {
    joints.leftHand[i].position.copy(p.leftHand[i]);
    joints.rightHand[i].position.copy(p.rightHand[i]);
  }

  // --------- HUESOS (cilindros) ---------
  const midShoulders = p.lShoulder.clone().add(p.rShoulder).multiplyScalar(0.5);
  const midHips = p.lHip.clone().add(p.rHip).multiplyScalar(0.5);

  updateBone(bones.torso, midShoulders, midHips);
  updateBone(bones.lUpperArm, p.lShoulder, p.lElbow);
  updateBone(bones.lLowerArm, p.lElbow, p.lWrist);
  updateBone(bones.rUpperArm, p.rShoulder, p.rElbow);
  updateBone(bones.rLowerArm, p.rElbow, p.rWrist);
}
