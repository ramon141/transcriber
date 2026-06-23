"use client";

import { useCallback, useRef } from "react";

interface Props {
  min: number;
  max: number;
  inicio: number;
  fim: number;
  setInicio: (v: number) => void;
  setFim: (v: number) => void;
  step?: number;
}

export function DualRangeSlider({ min, max, inicio, fim, setInicio, setFim, step = 1 }: Props) {
  const trackRef = useRef<HTMLDivElement>(null);

  const toPercent = (v: number) => ((v - min) / (max - min)) * 100;

  const toValue = useCallback(
    (clientX: number): number => {
      if (!trackRef.current) return min;
      const rect = trackRef.current.getBoundingClientRect();
      const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
      const raw = min + ratio * (max - min);
      return Math.round(raw / step) * step;
    },
    [min, max, step]
  );

  const startDrag = useCallback(
    (handle: "inicio" | "fim") => (e: React.MouseEvent | React.TouchEvent) => {
      e.preventDefault();

      const getX = (ev: MouseEvent | TouchEvent): number =>
        "touches" in ev ? ev.touches[0].clientX : ev.clientX;

      const onMove = (ev: MouseEvent | TouchEvent) => {
        const v = toValue(getX(ev));
        if (handle === "inicio") setInicio(Math.min(v, fim - step));
        else setFim(Math.max(v, inicio + step));
      };

      const onEnd = () => {
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onEnd);
        document.removeEventListener("touchmove", onMove);
        document.removeEventListener("touchend", onEnd);
      };

      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onEnd);
      document.addEventListener("touchmove", onMove, { passive: false });
      document.addEventListener("touchend", onEnd);
    },
    [toValue, inicio, fim, step, setInicio, setFim]
  );

  const onTrackClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const v = toValue(e.clientX);
      const distInicio = Math.abs(v - inicio);
      const distFim = Math.abs(v - fim);
      if (distInicio <= distFim) setInicio(Math.min(v, fim - step));
      else setFim(Math.max(v, inicio + step));
    },
    [toValue, inicio, fim, step, setInicio, setFim]
  );

  const pInicio = toPercent(inicio);
  const pFim = toPercent(fim);

  return (
    <div className="px-2.5 py-4">
      <div
        ref={trackRef}
        onClick={onTrackClick}
        className="relative h-1.5 bg-gray-200 rounded-full cursor-pointer"
      >
        <div
          className="absolute h-full bg-primary rounded-full"
          style={{ left: `${pInicio}%`, width: `${pFim - pInicio}%` }}
        />

        <Handle
          percent={pInicio}
          onMouseDown={startDrag("inicio")}
          onTouchStart={startDrag("inicio")}
          color="border-green-400"
        />
        <Handle
          percent={pFim}
          onMouseDown={startDrag("fim")}
          onTouchStart={startDrag("fim")}
          color="border-red-400"
        />
      </div>
    </div>
  );
}

function Handle({ percent, onMouseDown, onTouchStart, color }: {
  percent: number;
  onMouseDown: (e: React.MouseEvent) => void;
  onTouchStart: (e: React.TouchEvent) => void;
  color: string;
}) {
  return (
    <div
      onMouseDown={onMouseDown}
      onTouchStart={onTouchStart}
      className={`absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-5 h-5 rounded-full bg-white border-2 ${color} shadow-md cursor-grab active:cursor-grabbing active:scale-110 transition-transform z-10`}
      style={{ left: `${percent}%` }}
    />
  );
}
