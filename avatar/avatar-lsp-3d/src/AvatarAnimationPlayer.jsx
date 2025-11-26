// AvatarAnimationPlayer.jsx — carga JSON desde /animaciones y reproduce

import { useEffect, useState } from "react";
import Avatar3D from "./Avatar3D";

// Cargar TODAS las animaciones JSON de la carpeta ./animaciones
const modules = import.meta.glob("./animaciones/*.json", { eager: true });

const anims = {};
for (const path in modules) {
  const mod = modules[path];
  const data = mod.default ?? mod; // por si Vite envía {default: ...}
  const name = path.split("/").pop().replace(".json", "");
  anims[name] = data;
}

export default function AvatarAnimationPlayer({ sign }) {
  const [frame, setFrame] = useState(null);

  useEffect(() => {
    if (!sign || !anims[sign]) {
      setFrame(null);
      return;
    }

    const anim = anims[sign];
    const fps = anim.fps || 30;
    const frames = anim.frames || [];

    if (!frames.length) {
      setFrame(null);
      return;
    }

    let i = 0;
    const speedMultiplier = 0.6; // 🔥 un poco más rápido que en crudo
    const intervalMs = Math.max(1000 / (fps * speedMultiplier), 16);

    const id = setInterval(() => {
      const pose = frames[i].pose;
      setFrame(pose);
      i = (i + 1) % frames.length;
    }, intervalMs);

    return () => clearInterval(id);
  }, [sign]);

  if (!frame) {
    return <div style={{ color: "white", marginTop: 8 }}>Sin animación</div>;
  }

  return <Avatar3D pose={frame} />;
}
