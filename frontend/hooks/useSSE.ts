"use client";

import { useCallback, useRef, useState } from "react";
import type { SSEEvent } from "@/lib/types";

interface SSEState {
  progress: number;
  status: string;
  preview: string;
  running: boolean;
  error: string | null;
}

const INITIAL_STATE: SSEState = {
  progress: 0,
  status: "",
  preview: "",
  running: false,
  error: null,
};

export function useSSE(onComplete: (data: import("@/lib/types").ResultadoTranscricao) => void) {
  const [state, setState] = useState<SSEState>(INITIAL_STATE);
  const readerRef = useRef<ReadableStreamDefaultReader<Uint8Array> | null>(null);

  const start = useCallback(
    async (url: string) => {
      setState({ ...INITIAL_STATE, running: true });

      try {
        const res = await fetch(url);
        if (!res.ok || !res.body) {
          setState((s) => ({ ...s, running: false, error: "Falha ao conectar ao servidor." }));
          return;
        }

        const reader = res.body.getReader();
        readerRef.current = reader;
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const raw = line.slice(6).trim();
            if (!raw) continue;
            try {
              const event = JSON.parse(raw) as SSEEvent;
              _handleEvent(event, setState, onComplete);
            } catch {
              // linha malformada, ignorar
            }
          }
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Erro desconhecido";
        setState((s) => ({ ...s, running: false, error: msg }));
      } finally {
        setState((s) => ({ ...s, running: false }));
      }
    },
    [onComplete]
  );

  const stop = useCallback(() => {
    readerRef.current?.cancel();
    setState((s) => ({ ...s, running: false }));
  }, []);

  return { ...state, start, stop };
}

function _handleEvent(
  event: SSEEvent,
  setState: React.Dispatch<React.SetStateAction<SSEState>>,
  onComplete: (data: import("@/lib/types").ResultadoTranscricao) => void
): void {
  switch (event.type) {
    case "progress":
      setState((s) => ({ ...s, progress: event.value }));
      break;
    case "status":
      setState((s) => ({ ...s, status: event.message }));
      break;
    case "preview":
      setState((s) => ({ ...s, preview: event.text }));
      break;
    case "complete":
      setState((s) => ({ ...s, running: false, progress: 1 }));
      onComplete(event.data);
      break;
    case "error":
      setState((s) => ({ ...s, running: false, error: event.message }));
      break;
    default:
      break;
  }
}
