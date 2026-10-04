import { useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent, DragEvent, FormEvent } from "react";

import type { ReferenceOption } from "../lib/types";
import demoPreviewVideo from "../../assets/stylestep-demo-preview.webm";

interface StylingFormProps {
  seasons: ReferenceOption[];
  occasions: ReferenceOption[];
  styles: ReferenceOption[];
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onFileSelect: (file: File | null) => void;
  isSubmitting: boolean;
  errorMessage: string;
  uploadErrorMessage: string;
  previewUrl: string | null;
}

type UiIcon = "season" | "occasion" | "style" | "note" | "arrow" | "arrowUp";

function UiGlyph({ icon }: { icon: UiIcon }) {
  const commonProps = {
    fill: "none",
    stroke: "currentColor",
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    strokeWidth: 1.8,
  };

  switch (icon) {
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
    case "arrow":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path {...commonProps} d="M6 12h12" />
          <path {...commonProps} d="M13 7l5 5-5 5" />
        </svg>
      );
    case "arrowUp":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path {...commonProps} d="M12 18V6" />
          <path {...commonProps} d="M7 11l5-5 5 5" />
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

export function StylingForm({
  seasons,
  occasions,
  styles,
  onSubmit,
  onFileSelect,
  isSubmitting,
  errorMessage,
  uploadErrorMessage,
  previewUrl,
}: StylingFormProps) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const imageInputRef = useRef<HTMLInputElement | null>(null);
  const demoVideoRef = useRef<HTMLVideoElement | null>(null);
  const demoReplayTimeoutRef = useRef<number | null>(null);
  const [isDropActive, setIsDropActive] = useState(false);
  const [additionalInfo, setAdditionalInfo] = useState("");
  const hasReferenceData = useMemo(
    () => seasons.length > 0 && occasions.length > 0 && styles.length > 0,
    [occasions.length, seasons.length, styles.length],
  );
  const trimmedAdditionalInfo = additionalInfo.trim();
  const hasAdditionalInfo = trimmedAdditionalInfo.length > 0;
  const hasMinimumAdditionalInfoLength = trimmedAdditionalInfo.length >= 10;
  const remainingCharacters = Math.max(0, 10 - trimmedAdditionalInfo.length);
  const shouldShowAdditionalInfoHelper = hasAdditionalInfo && !hasMinimumAdditionalInfoLength;

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) {
      return;
    }

    textarea.style.height = "0px";
    const nextHeight = hasAdditionalInfo
      ? Math.min(Math.max(textarea.scrollHeight, 150), 220)
      : 76;
    textarea.style.height = `${nextHeight}px`;
    textarea.style.overflowY = hasAdditionalInfo && textarea.scrollHeight > 220 ? "auto" : "hidden";
  }, [additionalInfo, hasAdditionalInfo]);

  useEffect(() => {
    return () => {
      if (demoReplayTimeoutRef.current !== null) {
        window.clearTimeout(demoReplayTimeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (previewUrl && demoReplayTimeoutRef.current !== null) {
      window.clearTimeout(demoReplayTimeoutRef.current);
      demoReplayTimeoutRef.current = null;
    }
  }, [previewUrl]);

  const handleAdditionalInfoChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    event.currentTarget.setCustomValidity("");
    setAdditionalInfo(event.currentTarget.value);
  };

  const handleAdditionalInfoInvalid = (event: FormEvent<HTMLTextAreaElement>) => {
    const value = event.currentTarget.value.trim();
    if (!value) {
      event.currentTarget.setCustomValidity("Kas dar aktualu Tavo stiliui?");
      return;
    }

    if (value.length < 10) {
      event.currentTarget.setCustomValidity("Papildoma pastaba turi būti bent 10 simbolių.");
      return;
    }

    event.currentTarget.setCustomValidity("");
  };

  const handleDemoPreviewEnded = () => {
    if (demoReplayTimeoutRef.current !== null) {
      window.clearTimeout(demoReplayTimeoutRef.current);
    }

    demoReplayTimeoutRef.current = window.setTimeout(() => {
      const video = demoVideoRef.current;
      if (!video) {
        demoReplayTimeoutRef.current = null;
        return;
      }

      video.currentTime = 0;
      void video.play().catch(() => {});
      demoReplayTimeoutRef.current = null;
    }, 3000);
  };

  const handleMediaAreaClick = () => {
    const input = imageInputRef.current;
    if (!input) {
      return;
    }

    input.value = "";
    input.click();
  };

  const handleHiddenInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    onFileSelect(event.target.files?.[0] ?? null);
  };

  const handleDropZoneDragOver = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
    setIsDropActive(true);
  };

  const handleDropZoneDragLeave = (event: DragEvent<HTMLDivElement>) => {
    if (event.currentTarget.contains(event.relatedTarget as Node | null)) {
      return;
    }

    setIsDropActive(false);
  };

  const handleDropZoneDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDropActive(false);
    onFileSelect(event.dataTransfer.files?.[0] ?? null);
  };

  const uploadHintText = previewUrl ? "Paspausk, jei nori pakeisti nuotrauką" : "Įkelti drabužių nuotrauką";

  return (
    <section className="panel panel--form">
      <div className="hero-grid">
        <div className="hero-copy">
          <h1>Atrask naujus savo drabužių derinius</h1>
          <p className="hero-copy__lead">
            Įkelk nuotrauką, pasirink progą ir gauk 3 stiliaus pasiūlymus.
          </p>
        </div>

        <div
          className={`preview-card preview-card--hero${previewUrl ? "" : " preview-card--empty"}${isDropActive ? " preview-card--drop-active" : ""}`}
          onDragLeave={handleDropZoneDragLeave}
          onDragOver={handleDropZoneDragOver}
          onDrop={handleDropZoneDrop}
        >
          <input
            ref={imageInputRef}
            className="visually-hidden"
            accept=".jpg,.jpeg,.png,.webp"
            name="image_original"
            onChange={handleHiddenInputChange}
            type="file"
          />

          <button
            className="preview-card__media-button"
            type="button"
            onClick={handleMediaAreaClick}
            aria-label={previewUrl ? "Pakeisti drabužių nuotrauką" : "Įkelti drabužių nuotrauką"}
          >
            {previewUrl ? (
              <img className="preview-card__image" src={previewUrl} alt="Įkelta drabužių nuotrauka" />
            ) : (
              <video
                ref={demoVideoRef}
                className="preview-card__image preview-card__video"
                autoPlay
                muted
                onEnded={handleDemoPreviewEnded}
                playsInline
                preload="metadata"
                aria-label="Trumpa demonstracija, kaip naudotis StyleStep"
              >
                <source src={demoPreviewVideo} type="video/webm" />
              </video>
            )}
          </button>

          <div className="preview-card__upload-meta">
            <span className="preview-card__upload-hint">
              <span className="preview-card__upload-icon" aria-hidden="true">
                <UiGlyph icon="arrowUp" />
              </span>
              {uploadHintText}
            </span>
            {uploadErrorMessage ? <span className="preview-card__upload-error">{uploadErrorMessage}</span> : null}
          </div>
        </div>
      </div>

      <form className="form-grid" onSubmit={onSubmit}>
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

        <div className={`field-card field-card--note${hasAdditionalInfo ? " field-card--note-expanded" : ""}`}>
          <label className="field-label" htmlFor="additional_info">
            <span className="field-icon" aria-hidden="true">
              <UiGlyph icon="note" />
            </span>
            Papildoma pastaba
          </label>
          <div className={`note-composer${hasAdditionalInfo ? " note-composer--expanded" : ""}`}>
            <textarea
              ref={textareaRef}
              id="additional_info"
              className={`note-composer__textarea${hasAdditionalInfo ? " note-composer__textarea--expanded" : ""}`}
              name="additional_info"
              placeholder="Kas dar aktualu Tavo stiliui?"
              required
              minLength={10}
              rows={1}
              value={additionalInfo}
              onChange={handleAdditionalInfoChange}
              onInvalid={handleAdditionalInfoInvalid}
              aria-describedby={shouldShowAdditionalInfoHelper ? "additional_info_note" : undefined}
            />

            <div className="note-composer__actions">
              <button
                className="primary-button primary-button--inline note-composer__submit"
                disabled={isSubmitting || !hasReferenceData || !hasMinimumAdditionalInfoLength}
                type="submit"
              >
                <span className="primary-button__icon" aria-hidden="true">
                  <UiGlyph icon="arrow" />
                </span>
                {isSubmitting ? "Ruošiame tavo stiliaus kryptį..." : "Gauti stiliaus pasiūlymus"}
              </button>
            </div>
          </div>
          {shouldShowAdditionalInfoHelper ? (
            <span className="field-note" id="additional_info_note">
              Įrašyk dar bent {remainingCharacters} simbolių.
            </span>
          ) : null}
        </div>

        {errorMessage ? <div className="soft-alert">{errorMessage}</div> : null}
      </form>
    </section>
  );
}
