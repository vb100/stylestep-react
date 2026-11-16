import { useState } from "react";
import type { FormEvent } from "react";

import productPreview from "../assets/landing/product-preview.png";

const SUCCESS_MESSAGE =
  "Ačiū, kad domitės! Kai tik pasirodys nauja StyleStep versija su daug patogaus funkcionalumo, sužinosi pirmas!";

function ArrowIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

function MailIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4 6.5h16v11H4z" />
      <path d="m5 8 7 5 7-5" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="m5 12.5 4.3 4.3L19 7" />
    </svg>
  );
}

function SparkIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 1.5c.8 6.3 4.2 9.7 10.5 10.5-6.3.8-9.7 4.2-10.5 10.5C11.2 16.2 7.8 12.8 1.5 12 7.8 11.2 11.2 7.8 12 1.5Z" />
    </svg>
  );
}

export function LandingPage() {
  const [email, setEmail] = useState("");
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    // Presentation-only until the approved waitlist persistence endpoint exists.
    setIsSubmitted(true);
  };

  return (
    <div className="waitlist-page">
      <header className="waitlist-header">
        <a className="waitlist-brand" href="#pradžia" aria-label="StyleStep pradžia">
          stylestep<span aria-hidden="true" />
        </a>
        <span className="waitlist-header__status">
          <span aria-hidden="true" />
          Nauja versija ruošiama
        </span>
      </header>

      <main id="pradžia" className="waitlist-main">
        <section className="waitlist-hero" aria-labelledby="waitlist-title">
          <div className="waitlist-orbit waitlist-orbit--left" aria-hidden="true">
            <span className="waitlist-orbit__label waitlist-orbit__label--daily">Kasdien</span>
            <span className="waitlist-orbit__label waitlist-orbit__label--wardrobe">Tavo spinta</span>
            <span className="waitlist-orbit__spark">
              <SparkIcon />
            </span>
          </div>

          <div className="waitlist-hero__content">
            <span className="waitlist-kicker">
              <SparkIcon />
              Greitai naujas StyleStep
            </span>

            <h1 id="waitlist-title">
              Tavo stilius.
              <br />
              <span>Tavo naujas žingsnis.</span>
            </h1>

            <p className="waitlist-hero__lead">
              Kuriame išmanesnę StyleStep versiją, kuri padės atrasti savo spintą iš naujo ir kasdien lengviau
              pasirinkti, ką vilkėti.
            </p>

            <div className={`waitlist-card${isSubmitted ? " waitlist-card--success" : ""}`}>
              {isSubmitted ? (
                <div className="waitlist-success" role="status" aria-live="polite">
                  <span className="waitlist-success__icon">
                    <CheckIcon />
                  </span>
                  <div>
                    <strong>Ačiū!</strong>
                    <p>{SUCCESS_MESSAGE}</p>
                  </div>
                </div>
              ) : (
                <>
                  <div className="waitlist-card__heading">
                    <span>Sužinok pirmas</span>
                    <span className="waitlist-card__number">01</span>
                  </div>

                  <form className="waitlist-form" onSubmit={handleSubmit}>
                    <label className="visually-hidden" htmlFor="waitlist-email">
                      Elektroninis paštas
                    </label>
                    <div className="waitlist-form__field">
                      <span className="waitlist-form__mail" aria-hidden="true">
                        <MailIcon />
                      </span>
                      <input
                        id="waitlist-email"
                        name="email"
                        type="email"
                        inputMode="email"
                        autoComplete="email"
                        placeholder="tavo@el.pastas.lt"
                        value={email}
                        onChange={(event) => setEmail(event.target.value)}
                        required
                      />
                      <button type="submit">
                        <span>Pranešk man</span>
                        <span className="waitlist-form__arrow">
                          <ArrowIcon />
                        </span>
                      </button>
                    </div>
                  </form>

                  <p className="waitlist-card__note">Jokio triukšmo. Parašysime tik tada, kai nauja versija bus paruošta.</p>
                </>
              )}
            </div>
          </div>

          <div className="waitlist-preview" aria-hidden="true">
            <div className="waitlist-preview__glow" />
            <div className="waitlist-preview__screen">
              <img src={productPreview} alt="" />
            </div>
            <span className="waitlist-preview__sticker">Kiekvienai dienai!</span>
          </div>
        </section>

        <section className="waitlist-features" aria-label="Būsimos StyleStep galimybės">
          <article>
            <span>01</span>
            <div>
              <strong>Spinta vienoje vietoje</strong>
              <p>Tavo drabužiai ir jų istorija.</p>
            </div>
          </article>
          <article>
            <span>02</span>
            <div>
              <strong>Deriniai kiekvienai dienai</strong>
              <p>Pagal progą, nuotaiką ir orą.</p>
            </div>
          </article>
          <article>
            <span>03</span>
            <div>
              <strong>Tendencijos tavo stiliui</strong>
              <p>Mažiau triukšmo, daugiau aiškumo.</p>
            </div>
          </article>
        </section>
      </main>

      <footer className="waitlist-footer">
        <span>StyleStep</span>
        <span>Ženk į savo stilių.</span>
      </footer>
    </div>
  );
}
