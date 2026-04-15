import { useState } from "react";
import { Link, Outlet } from "react-router-dom";
import type { ViewerPlan } from "../lib/types";
import { CrownIcon } from "./PremiumElements";
import brandLogo from "../../logo/logo.png";

export interface LayoutOutletContext {
  viewerPlan: ViewerPlan;
  setViewerPlan: (plan: ViewerPlan) => void;
}

export function Layout() {
  const [viewerPlan, setViewerPlan] = useState<ViewerPlan>("free");

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="site-header__inner">
          <div className="brand-column">
            <Link className="brand-link" to="/">
              <span className="brand-link__mark" aria-hidden="true">
                <img className="brand-link__logo" src={brandLogo} alt="" />
              </span>
              <span className="brand-link__text">
                <span className="brand-link__title">StyleStep</span>
                <span className="brand-link__subtitle">Tavo asmeninis stilistas</span>
                <span className="brand-link__meta">Druskininkų „Atgimimo&quot; mokykla | MMB</span>
              </span>
            </Link>
          </div>

          <div className="header-actions">
            <span className="header-plan-label">Peržiūros planas</span>
            <div className="plan-switcher" role="group" aria-label="Peržiūros plano pasirinkimas">
              <button
                type="button"
                className={`plan-switcher__button${viewerPlan === "free" ? " plan-switcher__button--active" : ""}`}
                onClick={() => setViewerPlan("free")}
                aria-pressed={viewerPlan === "free"}
              >
                Nemokamas
              </button>
              <button
                type="button"
                className={`plan-switcher__button plan-switcher__button--premium${viewerPlan === "premium" ? " plan-switcher__button--active" : ""}`}
                onClick={() => setViewerPlan("premium")}
                aria-pressed={viewerPlan === "premium"}
              >
                <CrownIcon className="plan-switcher__icon" />
                Prenumerata
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="page-shell">
        <Outlet context={{ viewerPlan, setViewerPlan }} />
      </main>
    </div>
  );
}
