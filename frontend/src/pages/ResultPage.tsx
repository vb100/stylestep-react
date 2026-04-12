import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { fetchRequestDetail } from "../lib/api";
import type { RequestDetailPayload } from "../lib/types";
import { AdvicePanel } from "../components/AdvicePanel";
import { DetectedItemsTable } from "../components/DetectedItemsTable";
import { GeneratedImagePanel } from "../components/GeneratedImagePanel";
import { OutfitCards } from "../components/OutfitCards";
import { RequestStatusCard } from "../components/RequestStatusCard";

export function ResultPage() {
  const navigate = useNavigate();
  const { requestId = "" } = useParams();
  const [detail, setDetail] = useState<RequestDetailPayload | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let isMounted = true;
    fetchRequestDetail(requestId)
      .then((payload) => {
        if (!isMounted) {
          return;
        }
        setDetail(payload);
        setErrorMessage("");

        if (payload.status === "QUEUED" || payload.status === "RUNNING") {
          navigate(`/requests/${requestId}`, { replace: true });
        }
      })
      .catch(() => {
        if (isMounted) {
          setErrorMessage("Nepavyko įkelti rezultatų. Atnaujink puslapį ir bandyk dar kartą.");
        }
      });

    return () => {
      isMounted = false;
    };
  }, [navigate, requestId]);

  if (errorMessage) {
    return <section className="panel soft-alert">{errorMessage}</section>;
  }

  if (!detail) {
    return <section className="panel">Paruošiame tavo rezultatų vaizdą...</section>;
  }

  return (
    <div className="content-stack">
      <section className="panel">
        <div className="section-heading">
          <div>
            <span className="eyebrow">Paruošta tau</span>
            <h1 className="result-hero-title">Stiliaus kryptis tavo garderobui</h1>
            <p className="muted-text">
              Viskas vienoje vietoje: atpažinti drabužiai, trys derinių kryptys ir aiškūs papildymo pasiūlymai.
            </p>
          </div>
          <Link className="secondary-link" to="/">
            Nauja užklausa
          </Link>
        </div>

        <div className="selection-pills">
          <span className="selection-pill">Sezonas: {detail.season.name}</span>
          <span className="selection-pill">Proga: {detail.occasion.name}</span>
          <span className="selection-pill">Stilius: {detail.style.name}</span>
        </div>
      </section>

      <RequestStatusCard status={detail} />

      {detail.status === "FAILED" || !detail.result ? (
        <section className="panel">
          <div className="soft-alert">
            Šį kartą nepavyko paruošti galutinio atsakymo. Pabandyk pateikti naują nuotrauką arba pakartok veiksmą vėliau.
          </div>
        </section>
      ) : (
        <>
          <GeneratedImagePanel
            generatedImageUrl={detail.generated_image_url}
            imageErrorMessage={detail.image_error_message}
            generatedOutfit={detail.result.generated_outfit}
          />
          <DetectedItemsTable items={detail.result.detected_items} />
          <OutfitCards outfits={detail.result.outfit_cards} detectedItems={detail.result.detected_items} />
          <AdvicePanel advice={detail.result.advice} toBuy={detail.result.to_buy_with_links} />
        </>
      )}
    </div>
  );
}
