import { Link } from "react-router-dom";

export function NavBar() {
  return (
    <nav
      style={{
        display: "flex",
        gap: "12px",
        alignItems: "center",
        padding: "12px 16px",
        background: "#0a0a0a",
        borderBottom: "1px solid #333",
        color: "#fff",
        fontSize: "14px",
        fontWeight: 500,
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <Link
        to="/dashboard"
        style={{ color: "#fff", textDecoration: "none" }}
      >
        Dashboard
      </Link>

      <Link
        to="/tournaments"
        style={{ color: "#fff", textDecoration: "none" }}
      >
        Tournaments
      </Link>

      <Link
        to="/login"
        style={{
          color: "#fff",
          textDecoration: "none",
          marginLeft: "auto",
          fontWeight: 600,
        }}
      >
        Login
      </Link>
    </nav>
  );
}