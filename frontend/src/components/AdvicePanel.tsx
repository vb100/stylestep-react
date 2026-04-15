import type { AdviceBlock, ToBuyItem, ViewerPlan } from "../lib/types";
import { PremiumBadge, PremiumLock } from "./PremiumElements";

interface AdvicePanelProps {
  advice: AdviceBlock;
  toBuy: ToBuyItem[];
  viewerPlan: ViewerPlan;
}

const PRIORITY_LABELS: Record<string, string> = {
  must: "Svarbiausia",
  nice_to_have: "Papildomai",
};

function formatPriority(priority: string): string {
  return PRIORITY_LABELS[priority] ?? "Papildomai";
}

export function AdvicePanel({ advice, toBuy, viewerPlan }: AdvicePanelProps) {
  const adviceSections = [
    {
      key: "style",
      title: "Stilius",
      items: advice.style,
      locked: false,
      message: "",
    },
    {
      key: "care",
      title: "Priežiūra",
      items: advice.care,
      locked: viewerPlan === "free",
      message: "Drabužių priežiūros patarimai pilnai matomi su Premium planu.",
    },
    {
      key: "impression",
      title: "Įspūdis",
      items: advice.impression,
      locked: viewerPlan === "free",
      message: "Pilnas įspūdžio aprašymas skirtas prenumeratoriams.",
    },
  ];

  return (
    <>
      <section className="panel">
        <div className="section-heading section-heading--compact">
          <div>
            <span className="eyebrow">Jei ko dar trūksta</span>
            <h2 className="section-title">Papildomi pirkiniai</h2>
          </div>
        </div>

        {toBuy.length > 0 ? (
          <ul className="buy-list">
            {toBuy.map((item) => (
              <li key={`${item.name}-${item.google_query}`}>
                <div className="buy-list__header">
                  <strong>{item.name}</strong>
                  <span className="badge badge--accent">{formatPriority(item.priority)}</span>
                </div>
                <p>{item.why_needed}</p>
                <a href={item.google_search_url} target="_blank" rel="noreferrer">
                  Ieškoti Google
                </a>
                <span className="muted-text">Paieškos frazė: {item.google_query}</span>
              </li>
            ))}
          </ul>
        ) : (
          <div className="soft-alert soft-alert--muted">Šiam deriniui papildomų pirkinių kol kas nereikia.</div>
        )}
      </section>

      <section className="panel">
        <div className="section-heading section-heading--compact">
          <div>
            <span className="eyebrow">Naudinga prisiminti</span>
            <h2 className="section-title">Stiliaus pastabos</h2>
          </div>
        </div>

        <div className="advice-grid">
          {adviceSections.map((section) => (
            <div key={section.key} className={`advice-card${section.locked ? " advice-card--locked" : ""}`}>
              <div className="advice-card__header">
                <h3>{section.title}</h3>
                {section.locked ? <PremiumBadge /> : null}
              </div>
              <PremiumLock
                locked={section.locked}
                message={section.message}
                cta="Atrakink su Premium"
              >
                <ul>
                  {section.items.map((entry) => (
                    <li key={`${section.key}-${entry}`}>{entry}</li>
                  ))}
                </ul>
              </PremiumLock>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
