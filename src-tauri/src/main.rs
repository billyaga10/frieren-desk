#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use std::process::Command;
use tauri::{Manager, Window};

#[derive(Serialize, Deserialize, Clone)]
struct ChatItem {
    role: String,
    text: String,
}

#[tauri::command]
fn set_ignore_cursor_events(window: Window, ignore: bool) {
    let _ = window.set_ignore_cursor_events(ignore);
}

#[tauri::command]
fn ask_codex(user_message: String) -> Result<String, String> {
    let base_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR")).parent().unwrap().to_path_buf();
    let persona_path = base_dir.join("persona.txt");
    let memory_path = base_dir.join("memory.json");

    let persona = fs::read_to_string(&persona_path).unwrap_or_else(|_| {
        "Kamu adalah Frieren. Jawab tenang, hangat, dan singkat dalam 2-3 kalimat.".to_string()
    });

    let mut history: Vec<ChatItem> = fs::read_to_string(&memory_path)
        .ok()
        .and_then(|s| serde_json::from_str(&s).ok())
        .unwrap_or_default();

    let mut prompt = format!("=== SYSTEM PERSONA ===\n{}\n\n=== RIWAYAT CHAT ===\n", persona);
    for item in history.iter().rev().take(8).rev() {
        prompt.push_str(&format!("{}: {}\n", item.role, item.text));
    }
    prompt.push_str(&format!(
        "\nUser: {}\nBerikan balasan langsung sebagai Frieren (2-3 kalimat saja):",
        user_message
    ));

    let output = Command::new("/Users/user/.local/bin/codex")
        .args([
            "exec",
            "--skip-git-repo-check",
            "--ephemeral",
            "--sandbox",
            "read-only",
            "--color",
            "never",
            "-c",
            "mcp_servers={}",
            &prompt,
        ])
        .current_dir(&base_dir)
        .output()
        .map_err(|e| format!("Gagal memanggil Codex CLI: {}", e))?;

    let reply = String::from_utf8_lossy(&output.stdout).trim().to_string();
    let final_reply = if reply.is_empty() {
        "Maaf ya, mantranya sedang sedikit terhambat. Coba sapa aku lagi sebentar lagi.".to_string()
    } else {
        reply
    };

    history.push(ChatItem {
        role: "user".into(),
        text: user_message,
    });
    history.push(ChatItem {
        role: "assistant".into(),
        text: final_reply.clone(),
    });
    if history.len() > 8 {
        let drain_count = history.len() - 8;
        history.drain(0..drain_count);
    }
    let _ = fs::write(
        &memory_path,
        serde_json::to_string_pretty(&history).unwrap_or_else(|_| "[]".into()),
    );

    Ok(final_reply)
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let win = app.get_window("main").unwrap();
            // Position at bottom-right corner above Dock
            if let Ok(Some(monitor)) = win.primary_monitor() {
                let size = monitor.size();
                let scale = monitor.scale_factor();
                let x = (size.width as f64 / scale) as i32 - 358;
                let y = (size.height as f64 / scale) as i32 - 530;
                let _ = win.set_position(tauri::Position::Logical(tauri::LogicalPosition {
                    x: x as f64,
                    y: y as f64,
                }));
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![ask_codex, set_ignore_cursor_events])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
