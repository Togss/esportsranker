import { useState } from "react";
import { useSessionStore } from "../store/session";

export default function Login() {
  const [deviceCode, setDeviceCode] = useState("");

  // subscribe using selectors (consistent with Dashboard)
  const isLoggedIn = useSessionStore((s) => s.isLoggedIn);
  const accessToken = useSessionStore((s) => s.accessToken);
  const storeId = useSessionStore((s) => s.storeId);
  const loginWithDeviceCode = useSessionStore((s) => s.loginWithDeviceCode);
  const logout = useSessionStore((s) => s.logout);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    loginWithDeviceCode(deviceCode);
  }

  return (
    <div style={{ padding: 40, maxWidth: 400 }}>
      <h1 style={{ fontSize: "24px", fontWeight: 600 }}>Login</h1>
      <p style={{ marginTop: "8px", color: "#555" }}>
        This simulates Device Code → JWT. Later we'll call the backend and
        store a real access token securely.
      </p>

      <div
        style={{
          marginTop: "8px",
          fontSize: "12px",
          color: "#999",
          fontFamily: "monospace",
        }}
      >
        storeId: {storeId}
      </div>

      {isLoggedIn ? (
        <div
          style={{
            marginTop: "20px",
            padding: "12px",
            border: "1px solid #2c2c2c",
            borderRadius: "6px",
            background: "#111",
            color: "#eee",
            fontSize: "14px",
          }}
        >
          <div style={{ marginBottom: "8px", fontWeight: 500 }}>
            Logged in ✔
          </div>
          <div
            style={{
              wordBreak: "break-all",
              fontSize: "12px",
              color: "#ccc",
            }}
          >
            Token: {accessToken}
          </div>
          <button
            onClick={logout}
            style={{
              marginTop: "12px",
              width: "100%",
              background: "#441111",
              color: "#fff",
              fontSize: "14px",
              fontWeight: 600,
              border: "1px solid #772222",
              borderRadius: "4px",
              padding: "8px 12px",
              cursor: "pointer",
            }}
          >
            Logout
          </button>
        </div>
      ) : (
        <form
          onSubmit={handleSubmit}
          style={{
            marginTop: "20px",
            display: "flex",
            flexDirection: "column",
            gap: "12px",
            fontSize: "14px",
          }}
        >
          <label style={{ fontWeight: 500 }}>
            Device Code
            <input
              value={deviceCode}
              onChange={(e) => setDeviceCode(e.target.value)}
              placeholder="ex: ABC123-XYZ"
              style={{
                marginTop: "6px",
                width: "100%",
                background: "#111",
                color: "#fff",
                border: "1px solid #333",
                borderRadius: "4px",
                padding: "8px 10px",
                fontSize: "14px",
              }}
            />
          </label>

          <button
            type="submit"
            style={{
              width: "100%",
              background: "#113311",
              color: "#fff",
              fontSize: "14px",
              fontWeight: 600,
              border: "1px solid #224422",
              borderRadius: "4px",
              padding: "8px 12px",
              cursor: "pointer",
            }}
          >
            Login
          </button>
        </form>
      )}
    </div>
  );
}