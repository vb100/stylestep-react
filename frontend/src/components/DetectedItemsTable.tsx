import type { DetectedItem } from "../lib/types";

interface DetectedItemsTableProps {
  items: DetectedItem[];
}

const CATEGORY_LABELS: Record<string, string> = {
  top: "Viršutinė dalis",
  bottom: "Apatinė dalis",
  outerwear: "Viršutinis sluoksnis",
  dress: "Suknelė",
  shoes: "Avalynė",
  accessory: "Aksesuaras",
  other: "Kita",
};

function formatCategory(category: string): string {
  return CATEGORY_LABELS[category] ?? "Kita";
}

function formatConfidence(confidence: number): string {
  return `${Math.round(confidence * 100)}%`;
}

export function DetectedItemsTable({ items }: DetectedItemsTableProps) {
  return (
    <section className="panel">
      <div className="section-heading section-heading--compact">
        <div>
          <span className="eyebrow">Atpažinta nuotraukoje</span>
          <h2 className="section-title">Drabužiai ir detalės</h2>
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Drabužis</th>
              <th>Kategorija</th>
              <th>Spalvos</th>
              <th>Tikslumas</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td>
                  <strong>{item.label}</strong>
                </td>
                <td>
                  <span className="category-pill">{formatCategory(item.category)}</span>
                </td>
                <td>
                  <div className="color-list">
                    {item.colors.map((color) => (
                      <span key={`${item.id}-${color}`} className="color-chip">
                        {color}
                      </span>
                    ))}
                  </div>
                </td>
                <td>
                  <span className="confidence-pill">{formatConfidence(item.confidence)}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
