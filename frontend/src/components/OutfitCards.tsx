import type { DetectedItem, OutfitCard, ViewerPlan } from "../lib/types";
import { PremiumBadge, PremiumLock } from "./PremiumElements";

interface OutfitCardsProps {
  outfits: OutfitCard[];
  detectedItems: DetectedItem[];
  viewerPlan: ViewerPlan;
}

const ROLE_LABELS: Record<string, string> = {
  top: "Viršutinė dalis",
  bottom: "Apatinė dalis",
  outerwear: "Viršutinis sluoksnis",
  dress: "Suknelė",
  shoes: "Avalynė",
  accessory: "Aksesuaras",
  layer: "Sluoksnis",
};

function lookupItemLabel(detectedItems: DetectedItem[], itemId: string): string {
  return detectedItems.find((item) => item.id === itemId)?.label ?? "Pasirinktas drabužis";
}

function formatRole(role: string): string {
  return ROLE_LABELS[role] ?? role;
}

export function OutfitCards({ outfits, detectedItems, viewerPlan }: OutfitCardsProps) {
  return (
    <section className="panel">
      <div className="section-heading section-heading--compact">
        <div>
          <span className="eyebrow">Trys kryptys</span>
          <h2 className="section-title">Derinių pasiūlymai</h2>
        </div>
      </div>

      <div className="outfit-grid">
        {outfits.map((outfit, index) => {
          const isLocked = viewerPlan === "free" && index > 0;

          return (
          <article
            key={outfit.key}
            className={`outfit-card${outfit.is_generated_source ? " outfit-card--selected" : ""}${isLocked ? " outfit-card--locked" : ""}`}
          >
            <div className="outfit-card__header">
              <span className="badge">{outfit.option_label}</span>
              <span className="badge badge--accent">{outfit.variant_label}</span>
              {outfit.is_generated_source ? <span className="badge badge--selected">Pagal šį variantą sukurtas vaizdas</span> : null}
              {isLocked ? <PremiumBadge /> : null}
            </div>
            <PremiumLock
              locked={isLocked}
              message="Likę derinių pasiūlymai pilnai matomi prenumeratoriams."
              cta="Atrakink su Premium"
            >
              <h3>{outfit.title}</h3>
              <p>
                <strong>Kodėl tinka:</strong> {outfit.why_it_works}
              </p>
              <p>
                <strong>Siluetas:</strong> {outfit.fit_notes}
              </p>
              <p>
                <strong>Spalvų nuotaika:</strong> {outfit.color_notes}
              </p>

              <div className="outfit-card__items">
                {outfit.items.map((item) => (
                  <span key={`${outfit.key}-${item.detected_item_id}-${item.role}`} className="outfit-chip">
                    <strong>{lookupItemLabel(detectedItems, item.detected_item_id)}</strong>
                    <span>{formatRole(item.role)}</span>
                  </span>
                ))}
              </div>
            </PremiumLock>
          </article>
          );
        })}
      </div>
    </section>
  );
}
