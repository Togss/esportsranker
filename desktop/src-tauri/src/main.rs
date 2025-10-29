#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use rusqlite::{Connection, Result as SqlResult};
use std::fs;
use std::path::PathBuf;
use std::sync::Mutex;

/// figure out where to place the sqlite db file
/// we'll create `<project-root>/sqlite/esports_ranker.db`
/// and make sure the `sqlite/` directory exists.
fn resolve_db_path() -> SqlResult<PathBuf> {
    // current_dir() when running `pnpm tauri dev` is usually `desktop/`
    // but when the compiled binary runs, it can sometimes be `desktop/src-tauri/target/...`
    // so we'll walk up until we find the project root that has a `sqlite` folder or can create it.

    // start from the current working directory
    let mut dir = std::env::current_dir()
        .map_err(|e| rusqlite::Error::ToSqlConversionFailure(Box::new(e)))?;

    // We'll walk up at most 3 levels to be safe: current, parent, grandparent
    // and stop when we can create/use `<that>/sqlite`
    for _ in 0..3 {
        let candidate_sqlite_dir = dir.join("sqlite");

        // try to create the sqlite dir if it doesn't exist
        if !candidate_sqlite_dir.exists() {
            if let Err(_) = fs::create_dir_all(&candidate_sqlite_dir) {
                // couldn't create here, so try going up a level
                dir = match dir.parent() {
                    Some(parent) => parent.to_path_buf(),
                    None => break,
                };
                continue;
            }
        }

        // We were able to ensure this sqlite/ dir exists here.
        let db_path = candidate_sqlite_dir.join("esports_ranker.db");
        return Ok(db_path);
    }

    // if we exit the loop without returning, give up with a meaningful error
    Err(rusqlite::Error::SqliteFailure(
        rusqlite::ffi::Error {
            code: rusqlite::ErrorCode::CannotOpen,
            extended_code: 14,
        },
        Some("could not resolve sqlite directory".into()),
    ))
}

/// Initialize (or open) the local SQLite database:
/// - Enable WAL mode
/// - Create the `tournaments` table
fn init_database() -> SqlResult<Connection> {
    let db_path = resolve_db_path()?;
    let conn = Connection::open(&db_path)?;

    // WAL mode for durability and fewer write locks
    conn.pragma_update(None, "journal_mode", &"WAL")?;
    conn.pragma_update(None, "synchronous", &"NORMAL")?;

    // basic schema; we'll extend this later (stages, series, outbox, etc.)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            region TEXT,
            tier TEXT,
            start_date TEXT,
            end_date TEXT,
            status TEXT DEFAULT 'Draft'
        );",
        [],
    )?;

    Ok(conn)
}

/// Return a list of tournament names from the local DB.
/// This is called from React via invoke("get_tournaments")
#[tauri::command]
fn get_tournaments(state: tauri::State<'_, Mutex<Connection>>) -> Result<Vec<String>, String> {
    let conn = state
        .lock()
        .map_err(|_| "Failed to lock DB connection".to_string())?;

    let mut stmt = conn
        .prepare("SELECT name FROM tournaments ORDER BY id DESC")
        .map_err(|e| e.to_string())?;

    let rows = stmt
        .query_map([], |row| row.get::<_, String>(0))
        .map_err(|e| e.to_string())?;

    let mut names = Vec::new();
    for row_result in rows {
        match row_result {
            Ok(name) => names.push(name),
            Err(e) => return Err(e.to_string()),
        }
    }

    Ok(names)
}

fn main() {
    tauri::Builder::default()
        // DB connection is created once and shared via Tauri state
        .manage(Mutex::new(
            init_database().expect("failed to initialize local SQLite database"),
        ))
        // expose commands to frontend
        .invoke_handler(tauri::generate_handler![get_tournaments])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}