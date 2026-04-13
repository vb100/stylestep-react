import { Link, Outlet } from "react-router-dom";
import brandLogo from "../../logo/logo.png";

type AccentIcon = "hanger" | "spark" | "bag";

function AccentGlyph({ icon }: { icon: AccentIcon }) {
  const commonProps = {
    fill: "none",
    stroke: "currentColor",
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    strokeWidth: 1.7,
  };

  switch (icon) {
    case "hanger":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path {...commonProps} d="M12 6.4a1.8 1.8 0 1 0-1.6-2.7" />
          <path {...commonProps} d="M10.4 3.7l1.7 2.3" />
          <path {...commonProps} d="M12.1 6l-5.4 4.2a1.2 1.2 0 0 0 .8 2.2h9a1.2 1.2 0 0 0 .8-2.2z" />
        </svg>
      );
    case "spark":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path {...commonProps} d="M12 4l1.1 3.5L16.6 8 13 9.1 12 12.7 11 9.1 7.4 8l3.5-1.1z" />
          <path {...commonProps} d="M18 13.7l.6 1.8 1.8.6-1.8.6-.6 1.8-.6-1.8-1.8-.6 1.8-.6z" />
        </svg>
      );
    case "bag":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path {...commonProps} d="M7.2 9.2h9.6l-.8 8a1 1 0 0 1-1 .9H9a1 1 0 0 1-1-.9z" />
          <path {...commonProps} d="M9.4 10V8.7a2.6 2.6 0 0 1 5.2 0V10" />
        </svg>
      );
    default:
      return null;
  }
}

export function Layout() {
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
            <div className="header-palette" aria-hidden="true">
              <span className="header-palette__pill header-palette__pill--sage">
                <AccentGlyph icon="hanger" />
              </span>
              <span className="header-palette__pill header-palette__pill--rose">
                <AccentGlyph icon="spark" />
              </span>
              <span className="header-palette__pill header-palette__pill--sand">
                <AccentGlyph icon="bag" />
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="page-shell">
        <Outlet />
      </main>
    </div>
  );
}
