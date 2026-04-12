import { useEffect, useMemo, useState } from "react";

import type { RequestStatus, RequestStatusPayload } from "../lib/types";

type StepState = "done" | "current" | "upcoming" | "failed";
type StepIconName = "inbox" | "clock" | "scan" | "spark" | "image" | "check" | "warning";

interface ProgressStep {
  id: string;
  title: string;
  description: string;
  icon: StepIconName;
  state: StepState;
}

interface ProgressSnapshot {
  percent: number;
  title: string;
  subtitle: string;
  steps: ProgressStep[];
}

interface RequestProgressPanelProps {
  status: RequestStatusPayload;
}

const STATUS_LABELS: Record<RequestStatus, string> = {
  QUEUED: "Eilėje",
  RUNNING: "Vykdoma",
  DONE: "Baigta",
  FAILED: "Nepavyko",
};

const BASE_STEPS: Omit<ProgressStep, "state">[] = [
  {
    id: "received",
    title: "Užklausa priimta",
    description: "Jūsų nuotrauka ir pasirinkimai sėkmingai išsaugoti.",
    icon: "inbox",
  },
  {
    id: "queued",
    title: "Laukiama apdorojimo eilėje",
    description: "Sistema parenka laisvą procesą šiai užklausai vykdyti.",
    icon: "clock",
  },
  {
    id: "analysis",
    title: "Analizuojama nuotrauka",
    description: "AI atpažįsta drabužius, spalvas ir svarbiausias detales.",
    icon: "scan",
  },
  {
    id: "styling",
    title: "Kuriami derinių pasiūlymai",
    description: "Ruošiami trys variantai, pirkinių pasiūlymai ir stiliaus patarimai.",
    icon: "spark",
  },
  {
    id: "visual",
    title: "Generuojamas derinio vaizdas",
    description: "Kuriamas galutinis vizualas pagal pasirinktą derinio variantą.",
    icon: "image",
  },
];

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function secondsSince(createdAt: string, now: number): number {
  const createdTs = new Date(createdAt).getTime();
  if (Number.isNaN(createdTs)) {
    return 0;
  }
  return Math.max(0, Math.floor((now - createdTs) / 1000));
}

function getRunningPhase(elapsedSeconds: number): {
  currentStepId: string;
  completedStepIds: string[];
  percent: number;
  subtitle: string;
} {
  if (elapsedSeconds < 12) {
    return {
      currentStepId: "analysis",
      completedStepIds: ["received", "queued"],
      percent: clamp(42 + elapsedSeconds * 1.6, 42, 58),
      subtitle: "AI pradėjo nuotraukos analizę ir identifikuoja, kas matoma nuotraukoje.",
    };
  }

  if (elapsedSeconds < 28) {
    return {
      currentStepId: "styling",
      completedStepIds: ["received", "queued", "analysis"],
      percent: clamp(60 + (elapsedSeconds - 12) * 1.2, 60, 79),
      subtitle: "Dabar ruošiami konkretūs derinių pasiūlymai ir tekstiniai patarimai.",
    };
  }

  return {
    currentStepId: "visual",
    completedStepIds: ["received", "queued", "analysis", "styling"],
    percent: clamp(82 + (elapsedSeconds - 28) * 0.7, 82, 94),
    subtitle: "Likęs paskutinis etapas: generuojamas derinio vaizdas ir užbaigiamas atsakymas.",
  };
}

function buildSteps(currentStepId: string, completedStepIds: string[], failed = false): ProgressStep[] {
  return BASE_STEPS.map((step) => {
    let state: StepState = "upcoming";

    if (completedStepIds.includes(step.id)) {
      state = "done";
    } else if (step.id === currentStepId) {
      state = failed ? "failed" : "current";
    }

    return {
      ...step,
      state,
    };
  });
}

function buildProgressSnapshot(status: RequestStatusPayload, now: number): ProgressSnapshot {
  const queuedElapsedSeconds = secondsSince(status.created_at, now);
  const runningElapsedSeconds = secondsSince(status.updated_at, now);

  if (status.status === "DONE") {
    return {
      percent: 100,
      title: "Rezultatas paruoštas",
      subtitle: "Užklausa sėkmingai baigta. Rezultatų puslapis bus atvertas automatiškai.",
      steps: [
        ...buildSteps("visual", ["received", "queued", "analysis", "styling", "visual"]),
        {
          id: "done",
          title: "Rezultatas išsaugotas",
          description: "Galutinis atsakymas įrašytas ir paruoštas parodyti ekrane.",
          icon: "check",
          state: "done",
        },
      ],
    };
  }

  if (status.status === "FAILED") {
    return {
      percent: 100,
      title: "Apdorojimas sustojo",
      subtitle: "Sistema šį kartą neužbaigė užklausos. Siūlome pabandyti dar kartą su kita ar aiškesne nuotrauka.",
      steps: [
        ...buildSteps("styling", ["received"], true),
        {
          id: "failed",
          title: "Nepavyko užbaigti užklausos",
          description: "Pabandyk pateikti naują užklausą. Dažniausiai padeda aiškesnė nuotrauka arba trumpesnė pastaba.",
          icon: "warning",
          state: "failed",
        },
      ],
    };
  }

  if (status.status === "QUEUED") {
    return {
      percent: clamp(18 + queuedElapsedSeconds * 0.9, 18, 32),
      title: "Užklausa laukia vykdymo",
      subtitle: "Failas jau priimtas. Kai tik procesas bus laisvas, pradėsime AI analizę.",
      steps: buildSteps("queued", ["received"]),
    };
  }

  const runningPhase = getRunningPhase(runningElapsedSeconds);
  return {
    percent: runningPhase.percent,
    title: "Užklausa šiuo metu vykdoma",
    subtitle: runningPhase.subtitle,
    steps: buildSteps(runningPhase.currentStepId, runningPhase.completedStepIds),
  };
}

function StatusIcon({ name }: { name: StepIconName }) {
  const commonProps = {
    fill: "none",
    stroke: "currentColor",
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    strokeWidth: 1.8,
  };

  switch (name) {
    case "inbox":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path {...commonProps} d="M4 13.5V6.8A1.8 1.8 0 0 1 5.8 5h12.4A1.8 1.8 0 0 1 20 6.8v6.7" />
          <path {...commonProps} d="M4 13.5h3.8l1.6 2.5h5.2l1.6-2.5H20V18a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1z" />
        </svg>
      );
    case "clock":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <circle {...commonProps} cx="12" cy="12" r="8" />
          <path {...commonProps} d="M12 8v4.1l2.7 1.7" />
        </svg>
      );
    case "scan":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path {...commonProps} d="M7 4H5a1 1 0 0 0-1 1v2" />
          <path {...commonProps} d="M17 4h2a1 1 0 0 1 1 1v2" />
          <path {...commonProps} d="M7 20H5a1 1 0 0 1-1-1v-2" />
          <path {...commonProps} d="M17 20h2a1 1 0 0 0 1-1v-2" />
          <path {...commonProps} d="M6 12h12" />
          <path {...commonProps} d="M10 9h4" />
          <path {...commonProps} d="M9 15h6" />
        </svg>
      );
    case "spark":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path {...commonProps} d="M12 4l1.2 3.8L17 9l-3.8 1.2L12 14l-1.2-3.8L7 9l3.8-1.2z" />
          <path {...commonProps} d="M18 14l.7 2.3L21 17l-2.3.7L18 20l-.7-2.3L15 17l2.3-.7z" />
          <path {...commonProps} d="M6 14l.6 1.7L8.3 16l-1.7.6L6 18.3l-.6-1.7L3.7 16l1.7-.6z" />
        </svg>
      );
    case "image":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <rect {...commonProps} x="4" y="5" width="16" height="14" rx="2" />
          <circle {...commonProps} cx="9" cy="10" r="1.6" />
          <path {...commonProps} d="M6.5 17l4.2-4.4 2.8 2.9 2.3-2.3L19 17" />
        </svg>
      );
    case "check":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <circle {...commonProps} cx="12" cy="12" r="8" />
          <path {...commonProps} d="M8.5 12.2l2.3 2.4 4.7-5.2" />
        </svg>
      );
    case "warning":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path {...commonProps} d="M12 5l7 12H5z" />
          <path {...commonProps} d="M12 10v3.8" />
          <path {...commonProps} d="M12 17h.01" />
        </svg>
      );
    default:
      return null;
  }
}

export function translateStatus(status: RequestStatus): string {
  return STATUS_LABELS[status];
}

export function RequestProgressPanel({ status }: RequestProgressPanelProps) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (status.status === "DONE" || status.status === "FAILED") {
      return undefined;
    }

    const timerId = window.setInterval(() => {
      setNow(Date.now());
    }, 1000);

    return () => {
      window.clearInterval(timerId);
    };
  }, [status.status]);

  const snapshot = useMemo(() => buildProgressSnapshot(status, now), [now, status]);
  const elapsedSeconds = secondsSince(status.created_at, now);

  return (
    <section className="panel progress-panel">
      <div className="section-heading section-heading--compact">
        <div>
          <span className="eyebrow">Vykdymo eiga</span>
          <h2 className="section-title">{snapshot.title}</h2>
        </div>
        <span className={`status-pill status-pill--${status.status.toLowerCase()}`}>{translateStatus(status.status)}</span>
      </div>

      <p className="muted-text progress-panel__subtitle">{snapshot.subtitle}</p>

      <div
        aria-hidden="true"
        className={`progress-bar${status.status === "FAILED" ? " progress-bar--failed" : ""}`}
      >
        <div className="progress-bar__fill" style={{ width: `${snapshot.percent}%` }} />
      </div>

      <div className="progress-panel__meta">
        <span>{snapshot.percent}%</span>
        <span>Praėjo maždaug {elapsedSeconds} s</span>
        <span>Atnaujinama kas 3 s</span>
      </div>

      <div className="progress-steps">
        {snapshot.steps.map((step) => (
          <div key={step.id} className={`progress-step progress-step--${step.state}`}>
            <span className={`progress-step__icon progress-step__icon--${step.state}`}>
              <StatusIcon name={step.icon} />
            </span>
            <div className="progress-step__content">
              <strong>{step.title}</strong>
              <p>{step.description}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
