import { useSessionStore } from "../store/session";

export default function Dashboard() {
  // subscribe to individual fields so component re-renders when they change
  const isLoggedIn = useSessionStore((s) => s.isLoggedIn);
  const accessToken = useSessionStore((s) => s.accessToken);
  const storeId = useSessionStore((s) => s.storeId);

  return (
    <div style={{ padding: 40 }}>
      <h1 style={{ fontSize: "24px", fontWeight: 600 }}>Dashboard</h1>
      <p style={{ marginTop: "8px", color: "#555" }}>
        Overview screen — sync status, pending items, quick actions.
      </p>

      <div
        style={{
          marginTop: "12px",
          fontSize: "12px",
          color: "#999",
          fontFamily: "monospace",
        }}
      >
        storeId: {storeId}
      </div>

      <div
        style={{
          marginTop: "24px",
          padding: "16px",
          borderRadius: "8px",
          border: "1px solid #222",
          background: "#0f172a",
          color: "#fff",
          maxWidth: 480,
        }}
      >
        <div style={{ fontSize: "14px", fontWeight: 600, marginBottom: "8px" }}>
          Session Status
        </div>

        {isLoggedIn ? (
          <>
            <div style={{ fontSize: "14px", color: "#a7f3d0" }}>
              Logged in ✔
            </div>
            <div
              style={{
                marginTop: "8px",
                fontSize: "12px",
                color: "#94a3b8",
                wordBreak: "break-all",
              }}
            >
              Token: {accessToken}
            </div>
          </>
        ) : (
          <div style={{ fontSize: "14px", color: "#fca5a5" }}>
            Not logged in
          </div>
        )}
      </div>
    </div>
  );
}