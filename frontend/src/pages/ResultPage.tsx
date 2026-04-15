import { useEffect, useState } from "react";
import { Link, useNavigate, useOutletContext, useParams } from "react-router-dom";

import { fetchRequestDetail } from "../lib/api";
import type { RequestDetailPayload } from "../lib/types";
import { AdvicePanel } from "../components/AdvicePanel";
import { DetectedItemsTable } from "../components/DetectedItemsTable";
import { GeneratedImagePanel } from "../components/GeneratedImagePanel";
import type { LayoutOutletContext } from "../components/Layout";
import { OutfitCards } from "../components/OutfitCards";
import { RequestStatusCard } from "../components/RequestStatusCard";

export function ResultPage() {
  const navigate = useNavigate();
  const { requestId = "" } = useParams();
  const { viewerPlan } = useOutletContext<LayoutOutletContext>();
  const [detail, setDetail] = useState<RequestDetailPayload | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let isMounted = true;
    let intervalId: number | null = null;

    const loadDetail = async () => {
      try {
        const payload = await fetchRequestDetail(requestId);
        if (!isMounted) {
          return;
        }
        setDetail(payload);
        setErrorMessage("");

        if ((payload.status === "QUEUED" || payload.status === "RUNNING") && !payload.result_ready) {
          navigate(`/requests/${requestId}`, { replace: true });
          return;
        }

        const shouldKeepPolling =
          payload.status === "RUNNING" && (payload.image_pending || (!payload.image_ready && !payload.image_error_message));

        if (!shouldKeepPolling && intervalId !== null) {
          window.clearInterval(intervalId);
          intervalId = null;
        }
      } catch {
        if (isMounted) {
          setErrorMessage("Nepavyko įkelti rezultatų. Atnaujink puslapį ir bandyk dar kartą.");
        }
      }
    };

    void loadDetail();
    intervalId = window.setInterval(() => {
      void loadDetail();
    }, 4000);

    return () => {
      isMounted = false;
      if (intervalId !== null) {
        window.clearInterval(intervalId);
      }
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
            isLoading={detail.image_pending}
          />
          <DetectedItemsTable items={detail.result.detected_items} />
          <OutfitCards
            outfits={detail.result.outfit_cards}
            detectedItems={detail.result.detected_items}
            viewerPlan={viewerPlan}
          />
          <AdvicePanel advice={detail.result.advice} toBuy={detail.result.to_buy_with_links} viewerPlan={viewerPlan} />
        </>
      )}
    </div>
  );
}
