import type { RequestStatus, RequestStatusPayload } from "../lib/types";
import { translateStatus } from "./RequestProgressPanel";

interface RequestStatusCardProps {
  status: RequestStatusPayload;
}

const STATUS_COPY: Record<RequestStatus, { title: string; description: string }> = {
  QUEUED: {
    title: "Užklausa sėkmingai priimta",
    description: "Nuotrauka jau išsaugota. Kai tik atsiras laisvas procesas, pradėsime analizę.",
  },
  RUNNING: {
    title: "Kuriamas tavo stiliaus planas",
    description: "Šiuo metu analizuojame drabužius ir dėliojame aiškius derinių pasiūlymus.",
  },
  DONE: {
    title: "Tavo pasiūlymai jau paruošti",
    description: "Žemiau rasi pagrindinius drabužius, tris derinius ir papildomas įsigijimo rekomendacijas.",
  },
  FAILED: {
    title: "Šį kartą užklausos užbaigti nepavyko",
    description: "Pabandyk pateikti naują nuotrauką arba pakartok veiksmą šiek tiek vėliau.",
  },
};

export function RequestStatusCard({ status }: RequestStatusCardProps) {
  const copy = STATUS_COPY[status.status];

  return (
    <section className="panel status-summary">
      <div className="section-heading section-heading--compact">
        <div>
          <span className="eyebrow">Būsena</span>
          <h2 className="section-title">{copy.title}</h2>
        </div>
        <span className={`status-pill status-pill--${status.status.toLowerCase()}`}>{translateStatus(status.status)}</span>
      </div>

      <p className="status-summary__lead">{copy.description}</p>
    </section>
  );
}
