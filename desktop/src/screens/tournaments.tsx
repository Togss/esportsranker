import { useEffect, useState } from "react";
import { loadTournamentNames } from "../lib/storage";

export default function Tournaments() {
  const [names, setNames] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function run() {
      const data = await loadTournamentNames();
      setNames(data);
      setLoading(false);
    }
    run();
  }, []);

  return (
    <div style={{ padding: 40 }}>
      <h1 style={{ fontSize: "24px", fontWeight: 600 }}>Tournaments</h1>
      <p style={{ marginTop: "8px", color: "#555" }}>
        Offline tournaments from local SQLite:
      </p>

      {loading ? (
        <div style={{ marginTop: "16px", fontStyle: "italic" }}>Loading…</div>
      ) : names.length === 0 ? (
        <div style={{ marginTop: "16px", color: "#999" }}>
          No tournaments found.
        </div>
      ) : (
        <ul style={{ marginTop: "16px", lineHeight: "1.6em" }}>
          {names.map((n, idx) => (
            <li
              key={idx}
              style={{
                fontSize: "14px",
                background: "#111",
                color: "#eee",
                padding: "6px 10px",
                borderRadius: "6px",
                marginBottom: "6px",
                border: "1px solid #333",
              }}
            >
              {n}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}