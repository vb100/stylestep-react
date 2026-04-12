import { useEffect, useMemo, useState } from "react";

interface TypewriterTextProps {
  text: string;
  durationMs?: number;
  loopIntervalMs?: number;
  className?: string;
}

export function TypewriterText({
  text,
  durationMs = 2000,
  loopIntervalMs,
  className = "",
}: TypewriterTextProps) {
  const [visibleLength, setVisibleLength] = useState(0);

  useEffect(() => {
    if (!text) {
      setVisibleLength(0);
      return undefined;
    }

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (prefersReducedMotion) {
      setVisibleLength(text.length);
      return undefined;
    }

    const stepMs = Math.max(Math.floor(durationMs / text.length), 16);
    const cycleMs = Math.max(loopIntervalMs ?? durationMs, durationMs);
    let intervalId: number | null = null;
    let timeoutId: number | null = null;

    const startCycle = () => {
      let current = 0;
      setVisibleLength(0);

      intervalId = window.setInterval(() => {
        current += 1;
        if (current >= text.length) {
          setVisibleLength(text.length);
          if (intervalId !== null) {
            window.clearInterval(intervalId);
            intervalId = null;
          }
          return;
        }

        setVisibleLength(current);
      }, stepMs);

      if (loopIntervalMs) {
        timeoutId = window.setTimeout(() => {
          if (intervalId !== null) {
            window.clearInterval(intervalId);
            intervalId = null;
          }
          startCycle();
        }, cycleMs);
      }
    };

    startCycle();

    return () => {
      if (intervalId !== null) {
        window.clearInterval(intervalId);
      }
      if (timeoutId !== null) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [durationMs, loopIntervalMs, text]);

  const renderedText = useMemo(() => text.slice(0, visibleLength), [text, visibleLength]);
  const isComplete = visibleLength >= text.length;

  return (
    <span className={`typewriter-text${className ? ` ${className}` : ""}`}>
      {renderedText}
      {!isComplete ? <span aria-hidden="true" className="typewriter-text__cursor" /> : null}
    </span>
  );
}
