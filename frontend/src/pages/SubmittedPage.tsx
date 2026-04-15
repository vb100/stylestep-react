import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { fetchRequestStatus } from "../lib/api";
import type { RequestStatusPayload } from "../lib/types";
import { RequestProgressPanel } from "../components/RequestProgressPanel";
import { RequestStatusCard } from "../components/RequestStatusCard";

export function SubmittedPage() {
  const navigate = useNavigate();
  const { requestId = "" } = useParams();
  const [statusPayload, setStatusPayload] = useState<RequestStatusPayload | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let isMounted = true;

    const poll = async () => {
      try {
        const payload = await fetchRequestStatus(requestId);
        if (!isMounted) {
          return;
        }
        setStatusPayload(payload);
        setErrorMessage("");
        if (payload.result_ready || payload.status === "DONE") {
          navigate(`/requests/${requestId}/result`, { replace: true });
        }
      } catch (error) {
        if (isMounted) {
          setErrorMessage("Ryšys trumpam nutrūko. Bandome atnaujinti būseną dar kartą.");
        }
      }
    };

    void poll();
    const intervalId = window.setInterval(() => {
      void poll();
    }, 3000);

    return () => {
      isMounted = false;
      window.clearInterval(intervalId);
    };
  }, [navigate, requestId]);

  return (
    <div className="content-stack">
      <section className="panel">
        <h1>Užklausa pateikta</h1>
        <p className="muted-text">
          Sistema automatiškai tikrina eigą. Kai tik tekstiniai pasiūlymai bus paruošti, šis puslapis automatiškai
          atidarys rezultatą, o vizualas prireikus bus dar užbaigiamas tame pačiame lange.
        </p>
        <div className="action-row">
          <Link className="secondary-link" to="/">
            Kurti naują užklausą
          </Link>
          {statusPayload?.status === "FAILED" ? (
            <Link className="secondary-link" to={`/requests/${requestId}/result`}>
              Peržiūrėti atsakymą
            </Link>
          ) : null}
        </div>
      </section>

      {statusPayload ? (
        <>
          <RequestProgressPanel status={statusPayload} />
          <RequestStatusCard status={statusPayload} />
        </>
      ) : (
        <section className="panel">Įkeliama vykdymo būsena...</section>
      )}
      {errorMessage ? <section className="panel soft-alert soft-alert--muted">{errorMessage}</section> : null}
    </div>
  );
}
