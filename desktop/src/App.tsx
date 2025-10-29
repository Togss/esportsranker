import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./screens/login";
import Dashboard from "./screens/dashboard";
import Tournaments from "./screens/tournaments";
import { NavBar } from "./components/NavBar";

export default function App() {
  return (
    <HashRouter>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          height: "100vh",
          background: "#1a1a1a",
          color: "#fff",
          fontFamily: "system-ui, sans-serif",
        }}
      >
        <NavBar />

        <div
          style={{
            flex: 1,
            overflow: "auto",
            background: "#0f172a",
            color: "#fff",
          }}
        >
          <Routes>
            {/* default route when app first opens */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />

            {/* actual pages */}
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/tournaments" element={<Tournaments />} />
            <Route path="/login" element={<Login />} />

            {/* fallback for unknown paths */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </div>
      </div>
    </HashRouter>
  );
}