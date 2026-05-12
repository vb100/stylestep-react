import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { ApiError, createStylingRequest, fetchBootstrap } from "../lib/api";
import type { BootstrapPayload } from "../lib/types";
import { StylingForm } from "../components/StylingForm";

const ACCEPTED_IMAGE_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);
const ACCEPTED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"];

function isAcceptedImageFile(file: File) {
  const lowerName = file.name.toLowerCase();
  return ACCEPTED_IMAGE_TYPES.has(file.type) || ACCEPTED_IMAGE_EXTENSIONS.some((extension) => lowerName.endsWith(extension));
}

export function HomePage() {
  const navigate = useNavigate();
  const [bootstrap, setBootstrap] = useState<BootstrapPayload | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [uploadErrorMessage, setUploadErrorMessage] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
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

  const handleFileSelect = (file: File | null) => {
    if (!file) {
      return;
    }

    if (!isAcceptedImageFile(file)) {
      setUploadErrorMessage("Netinkamas failo formatas. Įkelk JPG, PNG arba WEBP.");
      return;
    }

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setUploadErrorMessage("");
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedFile) {
      setUploadErrorMessage("Įkelk JPG, PNG arba WEBP nuotrauką.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage("");
    setUploadErrorMessage("");

    const form = event.currentTarget;
    const formData = new FormData(form);
    formData.set("image_original", selectedFile);

    try {
      const payload = await createStylingRequest(formData);
      navigate(`/requests/${payload.id}`);
    } catch (error) {
      if (error instanceof ApiError && error.details && typeof error.details === "object") {
        const fieldErrors = (error.details as { fields?: Record<string, string[]> }).fields;
        if (fieldErrors) {
          const firstFieldError = Object.values(fieldErrors).flat()[0];
          setErrorMessage(firstFieldError || "Patikrink, ar pasirinkti visi laukai ir ar įkelta tinkamo formato nuotrauka.");
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
      onFileSelect={handleFileSelect}
      isSubmitting={isSubmitting}
      errorMessage={errorMessage}
      uploadErrorMessage={uploadErrorMessage}
      previewUrl={previewUrl}
    />
  );
}
