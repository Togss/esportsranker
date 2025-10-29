import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./screens/login";
import Dashboard from "./screens/dashboard";
import Tournaments from "./screens/tournaments";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Default route: when we're at "/" just go to /dashboard */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />

        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/tournaments" element={<Tournaments />} />
      </Routes>
    </BrowserRouter>
  );
}