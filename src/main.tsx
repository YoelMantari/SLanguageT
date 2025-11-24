import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";

const rootElement = document.getElementById("root");

if (!rootElement) {
  console.error("Root element not found!");
  document.body.innerHTML =
    '<div style="padding: 20px; color: red;">Error: Root element not found!</div>';
} else {
  console.log("Root element found, mounting React app...");
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>
  );
}
