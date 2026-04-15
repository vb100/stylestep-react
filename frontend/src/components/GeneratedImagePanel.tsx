import type { GeneratedOutfitMeta } from "../lib/types";

interface GeneratedImagePanelProps {
  generatedImageUrl: string | null;
  imageErrorMessage: string;
  generatedOutfit: GeneratedOutfitMeta | null;
  isLoading: boolean;
}

export function GeneratedImagePanel({
  generatedImageUrl,
  imageErrorMessage,
  generatedOutfit,
  isLoading,
}: GeneratedImagePanelProps) {
  return (
    <section className="panel">
      <div className="section-heading section-heading--compact">
        <div>
          <span className="eyebrow">Vizualus įkvėpimas</span>
          <h2 className="section-title">Sugeneruotas derinio vaizdas</h2>
        </div>
      </div>

      {generatedOutfit ? (
        <div className="generated-meta">
          <span className="badge">{generatedOutfit.option_label}</span>
          <span className="badge badge--accent">{generatedOutfit.variant_label}</span>
          <p className="muted-text">
            Šis vaizdas sukurtas pagal <strong>{generatedOutfit.option_label.toLowerCase()}</strong>:
            {" "}
            <strong>{generatedOutfit.title}</strong>
          </p>
        </div>
      ) : null}

      {generatedImageUrl ? (
        <img className="generated-image" src={generatedImageUrl} alt="Sugeneruotas derinio vaizdas" />
      ) : isLoading ? (
        <div className="generated-image-loading">
          <div className="preview-card__placeholder generated-image-loading__placeholder">
            <div className="generated-image-loading__pulse" aria-hidden="true" />
            <div>
              <strong>Vizualas dar kuriamas...</strong>
              <p className="muted-text">Tekstiniai pasiūlymai jau paruošti, o galutinis derinio vaizdas bus įkeltas netrukus.</p>
            </div>
          </div>
        </div>
      ) : imageErrorMessage ? (
        <div className="soft-alert soft-alert--muted">
          Vizualo šį kartą nepavyko paruošti, tačiau žemiau pateikti tekstiniai stiliaus pasiūlymai vis tiek paruošti.
        </div>
      ) : (
        <div className="soft-alert soft-alert--muted">Vizualus derinio įkvėpimas šiai užklausai dar neparuoštas.</div>
      )}
    </section>
  );
}
