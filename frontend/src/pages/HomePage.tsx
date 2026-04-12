import { useEffect, useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { ApiError, createStylingRequest, fetchBootstrap } from "../lib/api";
import type { BootstrapPayload } from "../lib/types";
import { StylingForm } from "../components/StylingForm";

export function HomePage() {
  const navigate = useNavigate();
  const [bootstrap, setBootstrap] = useState<BootstrapPayload | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    fetchBootstrap()
      .then((payload) => {
        if (isMounted) {
          setBootstrap(payload);
          setErrorMessage("");
        }
      })
      .catch(() => {
        if (isMounted) {
          setErrorMessage("Nepavyko įkelti pradinių pasirinkimų. Atnaujink puslapį ir bandyk dar kartą.");
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(file ? URL.createObjectURL(file) : null);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setErrorMessage("");

    const form = event.currentTarget;
    const formData = new FormData(form);

    try {
      const payload = await createStylingRequest(formData);
      navigate(`/requests/${payload.id}`);
    } catch (error) {
      if (error instanceof ApiError && error.details && typeof error.details === "object") {
        const fieldErrors = (error.details as { fields?: Record<string, string[]> }).fields;
        if (fieldErrors) {
          setErrorMessage("Patikrink, ar pasirinkti visi laukai ir ar įkelta tinkamo formato nuotrauka.");
        } else {
          setErrorMessage("Nepavyko pateikti užklausos. Pabandyk dar kartą po akimirkos.");
        }
      } else if (error instanceof Error) {
        setErrorMessage("Nepavyko pateikti užklausos. Pabandyk dar kartą po akimirkos.");
      } else {
        setErrorMessage("Nepavyko pateikti užklausos. Pabandyk dar kartą po akimirkos.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return <section className="panel">Ruošiame pasirinkimus...</section>;
  }

  if (!bootstrap) {
    return <section className="panel soft-alert">{errorMessage || "Nepavyko įkelti pradinių pasirinkimų."}</section>;
  }

  return (
    <StylingForm
      seasons={bootstrap.reference_data.seasons}
      occasions={bootstrap.reference_data.occasions}
      styles={bootstrap.reference_data.styles}
      onSubmit={handleSubmit}
      onFileChange={handleFileChange}
      isSubmitting={isSubmitting}
      errorMessage={errorMessage}
      previewUrl={previewUrl}
    />
  );
}
