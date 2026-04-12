import { useMemo } from "react";
import type { ChangeEvent, FormEvent } from "react";

import type { ReferenceOption } from "../lib/types";
import { TypewriterText } from "./TypewriterText";

interface StylingFormProps {
  seasons: ReferenceOption[];
  occasions: ReferenceOption[];
  styles: ReferenceOption[];
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onFileChange: (event: ChangeEvent<HTMLInputElement>) => void;
  isSubmitting: boolean;
  errorMessage: string;
  previewUrl: string | null;
}

type UiIcon = "image" | "season" | "occasion" | "style" | "note" | "spark" | "bag" | "hanger" | "arrow";

function UiGlyph({ icon }: { icon: UiIcon }) {
  const commonProps = {
    fill: "none",
    stroke: "currentColor",
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    strokeWidth: 1.8,
  };

  switch (icon) {
    case "image":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <rect {...commonProps} x="4" y="5" width="16" height="14" rx="3" />
          <circle {...commonProps} cx="9" cy="10" r="1.4" />
          <path {...commonProps} d="M6.5 17l4.1-4.2 2.6 2.7 2.5-2.3L18.5 17" />
        </svg>
      );
    case "season":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <circle {...commonProps} cx="12" cy="12" r="4" />
          <path {...commonProps} d="M12 2.8v2.5M12 18.7v2.5M21.2 12h-2.5M5.3 12H2.8M18.6 5.4l-1.8 1.8M7.2 16.8l-1.8 1.8M18.6 18.6l-1.8-1.8M7.2 7.2 5.4 5.4" />
        </svg>
      );
    case "occasion":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <rect {...commonProps} x="5" y="6.5" width="14" height="12" rx="3" />
          <path {...commonProps} d="M8.5 6.5v-1a1.2 1.2 0 0 1 1.2-1.2h4.6a1.2 1.2 0 0 1 1.2 1.2v1" />
          <path {...commonProps} d="M5 11.2h14" />
        </svg>
      );
    case "style":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path {...commonProps} d="M12 4l1.1 3.5L16.6 8 13 9.1 12 12.7 11 9.1 7.4 8l3.5-1.1z" />
          <path {...commonProps} d="M18.4 13.4l.6 1.8 1.8.6-1.8.6-.6 1.8-.6-1.8-1.8-.6 1.8-.6z" />
        </svg>
      );
    case "note":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path {...commonProps} d="M7 5h10a2 2 0 0 1 2 2v10H9l-4 2V7a2 2 0 0 1 2-2z" />
          <path {...commonProps} d="M9 10h6M9 13h4" />
        </svg>
      );
    case "spark":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path {...commonProps} d="M12 4l1.1 3.5L16.6 8 13 9.1 12 12.7 11 9.1 7.4 8l3.5-1.1z" />
          <path {...commonProps} d="M6 15.7l.5 1.5 1.5.5-1.5.5-.5 1.5-.5-1.5-1.5-.5 1.5-.5z" />
        </svg>
      );
    case "bag":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path {...commonProps} d="M7.2 9.2h9.6l-.8 8a1 1 0 0 1-1 .9H9a1 1 0 0 1-1-.9z" />
          <path {...commonProps} d="M9.4 10V8.7a2.6 2.6 0 0 1 5.2 0V10" />
        </svg>
      );
    case "hanger":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path {...commonProps} d="M12 6.4a1.8 1.8 0 1 0-1.6-2.7" />
          <path {...commonProps} d="M10.4 3.7l1.7 2.3" />
          <path {...commonProps} d="M12.1 6l-5.4 4.2a1.2 1.2 0 0 0 .8 2.2h9a1.2 1.2 0 0 0 .8-2.2z" />
        </svg>
      );
    case "arrow":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path {...commonProps} d="M6 12h12" />
          <path {...commonProps} d="M13 7l5 5-5 5" />
        </svg>
      );
    default:
      return null;
  }
}

function OptionList({ options }: { options: ReferenceOption[] }) {
  return (
    <>
      {options.map((option) => (
        <option key={option.id} value={option.id}>
          {option.name}
        </option>
      ))}
    </>
  );
}

const HIGHLIGHTS = [
  {
    icon: "hanger" as const,
    title: "Švelni drabužių analizė",
    text: "Sistema pirmiausia remiasi tuo, ką iš tikrųjų matai nuotraukoje.",
  },
  {
    icon: "spark" as const,
    title: "Trys aiškūs variantai",
    text: "Gauni ramesnį, ryškesnį ir kūrybiškesnį derinio kelią.",
  },
  {
    icon: "bag" as const,
    title: "Pirkinių kryptis",
    text: "Jei ko nors trūksta, matysi konkrečias paieškos nuorodas ir prioritetus.",
  },
];

export function StylingForm({
  seasons,
  occasions,
  styles,
  onSubmit,
  onFileChange,
  isSubmitting,
  errorMessage,
  previewUrl,
}: StylingFormProps) {
  const hasReferenceData = useMemo(
    () => seasons.length > 0 && occasions.length > 0 && styles.length > 0,
    [occasions.length, seasons.length, styles.length],
  );

  return (
    <section className="panel panel--form">
      <div className="hero-grid">
        <div className="hero-copy">
          <span className="eyebrow">Subtilus stiliaus planas</span>
          <h1>Vienas vaizdas, trys deriniai ir aiški kryptis tavo garderobui.</h1>
          <p className="hero-copy__lead">
            <TypewriterText
              durationMs={2000}
              loopIntervalMs={10000}
              text="Įkelk nuotrauką su drabužiais, pasirink progą ir nuotaiką, o StyleStep paruoš lengvai suprantamus pasiūlymus lietuvių kalba."
            />
          </p>

          <div className="hero-highlights">
            {HIGHLIGHTS.map((item) => (
              <article key={item.title} className="feature-card">
                <span className="feature-card__icon" aria-hidden="true">
                  <UiGlyph icon={item.icon} />
                </span>
                <strong className="feature-card__title">{item.title}</strong>
                <span className="feature-card__text">{item.text}</span>
              </article>
            ))}
          </div>
        </div>

        <div className={`preview-card preview-card--hero${previewUrl ? "" : " preview-card--empty"}`}>
          <span className="preview-card__label">Tavo pasirinktas įkvėpimas</span>
          {previewUrl ? (
            <img className="preview-card__image" src={previewUrl} alt="Įkelta drabužių nuotrauka" />
          ) : (
            <div className="preview-card__placeholder">
              <span className="feature-card__icon" aria-hidden="true">
                <UiGlyph icon="image" />
              </span>
              <p>Įkėlus nuotrauką, jos miniatiūra iš karto bus parodyta čia.</p>
            </div>
          )}
        </div>
      </div>

      <form className="form-grid" onSubmit={onSubmit}>
        <div className="field-grid">
          <label className="field-card field-card--upload">
            <span className="field-label">
              <span className="field-icon" aria-hidden="true">
                <UiGlyph icon="image" />
              </span>
              Įkelk drabužių nuotrauką
            </span>
            <input accept=".jpg,.jpeg,.png,.webp" name="image_original" onChange={onFileChange} required type="file" />
            <span className="field-note">Tinka JPG, PNG arba WEBP formatai. Rekomenduojama aiški, šviesi nuotrauka.</span>
          </label>
        </div>

        <div className="form-grid__inline">
          <label className="field-card">
            <span className="field-label">
              <span className="field-icon" aria-hidden="true">
                <UiGlyph icon="season" />
              </span>
              Sezonas
            </span>
            <select name="season" defaultValue="" required>
              <option value="" disabled>
                Pasirink sezoną
              </option>
              <OptionList options={seasons} />
            </select>
          </label>

          <label className="field-card">
            <span className="field-label">
              <span className="field-icon" aria-hidden="true">
                <UiGlyph icon="occasion" />
              </span>
              Proga
            </span>
            <select name="occasion" defaultValue="" required>
              <option value="" disabled>
                Pasirink progą
              </option>
              <OptionList options={occasions} />
            </select>
          </label>

          <label className="field-card">
            <span className="field-label">
              <span className="field-icon" aria-hidden="true">
                <UiGlyph icon="style" />
              </span>
              Stiliaus kryptis
            </span>
            <select name="style" defaultValue="" required>
              <option value="" disabled>
                Pasirink stilių
              </option>
              <OptionList options={styles} />
            </select>
          </label>
        </div>

        <label className="field-card">
          <span className="field-label">
            <span className="field-icon" aria-hidden="true">
              <UiGlyph icon="note" />
            </span>
            Papildoma pastaba
          </span>
          <textarea
            name="additional_info"
            placeholder="Pvz.: norisi daugiau šviesių tonų, patogaus silueto ir lengvai priderinamų detalių."
            rows={5}
          />
          <span className="field-note">Šis laukas neprivalomas, bet padeda pasiūlymus pritaikyti tiksliau.</span>
        </label>

        {errorMessage ? <div className="soft-alert">{errorMessage}</div> : null}

        <div className="submit-row">
          <button className="primary-button" disabled={isSubmitting || !hasReferenceData} type="submit">
            <span className="primary-button__icon" aria-hidden="true">
              <UiGlyph icon="arrow" />
            </span>
            {isSubmitting ? "Ruošiame tavo stiliaus kryptį..." : "Gauti stiliaus pasiūlymus"}
          </button>
        </div>
      </form>
    </section>
  );
}
