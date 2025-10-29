import { invoke } from "@tauri-apps/api/core";

// Ask Rust (Tauri command) for tournaments from SQLite
export async function loadTournamentNames(): Promise<string[]> {
  try {
    const names = await invoke<string[]>("get_tournaments");
    return names;
  } catch (err) {
    console.error("Failed to load tournaments:", err);
    return [];
  }
}