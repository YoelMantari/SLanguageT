// App.jsx — menú de señas + AvatarAnimationPlayer

import { useState } from "react";
import AvatarAnimationPlayer from "./AvatarAnimationPlayer";

const SIGNS = [
  "hola",
  "gracias",
  "comer",
  "ayuda",
  "adios",
  "baño",
  "beber",
  "casa",
  "dolor",
  "donde",
  "espera",
  "ir",
  "porfavor",
  "querer",
  "tu",
  "venir",
  "yo",
];

export default function App() {
  const [selected, setSelected] = useState(null);

  return (
    <div style={{ padding: 20, fontFamily: "system-ui, sans-serif" }}>
      <h1 style={{ color: "white", marginBottom: 16 }}>
        Entrenador LSP con Avatar 3D
      </h1>

      <div style={{ marginBottom: 16, display: "flex", flexWrap: "wrap", gap: 8 }}>
        {SIGNS.map((s) => (
          <button
            key={s}
            onClick={() => setSelected(s)}
            style={{
              padding: "8px 18px",
              borderRadius: 6,
              border: "none",
              background: selected === s ? "#1d4ed8" : "#1f2937",
              color: "white",
              cursor: "pointer",
              fontWeight: 600,
              letterSpacing: 0.5,
            }}
          >
            {s.toUpperCase()}
          </button>
        ))}
      </div>

      <AvatarAnimationPlayer sign={selected} />
    </div>
  );
}
