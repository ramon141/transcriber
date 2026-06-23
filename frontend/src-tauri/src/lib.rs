use std::net::TcpStream;
use std::process::Command;
use std::sync::Mutex;
use tauri::Manager;

struct BackendProcess(Mutex<Option<std::process::Child>>);

fn backend_ativo() -> bool {
    TcpStream::connect("127.0.0.1:8001").is_ok()
}

fn iniciar_backend(raiz: &str) -> Option<std::process::Child> {
    if backend_ativo() {
        return None;
    }

    let uvicorn = format!("{}/venv/bin/uvicorn", raiz);

    Command::new(&uvicorn)
        .args(["backend.main:app", "--host", "127.0.0.1", "--port", "8001"])
        .current_dir(raiz)
        .spawn()
        .ok()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let raiz = std::env::var("TRANSCRIBER_ROOT")
        .unwrap_or_else(|_| "/Users/ramon/Documents/MyProjects/split_audio".to_string());

    let processo = iniciar_backend(&raiz);

    tauri::Builder::default()
        .manage(BackendProcess(Mutex::new(processo)))
        .build(tauri::generate_context!())
        .expect("Erro ao construir app Tauri")
        .run(|app, event| {
            if let tauri::RunEvent::Exit = event {
                if let Ok(mut guard) = app.state::<BackendProcess>().0.lock() {
                    if let Some(ref mut child) = *guard {
                        let _ = child.kill();
                    }
                }
            }
        });
}
