import type { AdviceBlock, ToBuyItem } from "../lib/types";

interface AdvicePanelProps {
  advice: AdviceBlock;
  toBuy: ToBuyItem[];
}

const PRIORITY_LABELS: Record<string, string> = {
  must: "Svarbiausia",
  nice_to_have: "Papildomai",
};

function formatPriority(priority: string): string {
  return PRIORITY_LABELS[priority] ?? "Papildomai";
}

export function AdvicePanel({ advice, toBuy }: AdvicePanelProps) {
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
          <div className="advice-card">
            <h3>Stilius</h3>
            <ul>
              {advice.style.map((entry) => (
                <li key={`style-${entry}`}>{entry}</li>
              ))}
            </ul>
          </div>
          <div className="advice-card">
            <h3>Priežiūra</h3>
            <ul>
              {advice.care.map((entry) => (
                <li key={`care-${entry}`}>{entry}</li>
              ))}
            </ul>
          </div>
          <div className="advice-card">
            <h3>Įspūdis</h3>
            <ul>
              {advice.impression.map((entry) => (
                <li key={`impression-${entry}`}>{entry}</li>
              ))}
            </ul>
          </div>
        </div>
      </section>
    </>
  );
}
