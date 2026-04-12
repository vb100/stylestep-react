import type {
  BootstrapPayload,
  CreateRequestResponse,
  RequestDetailPayload,
  RequestStatusPayload,
} from "./types";

class ApiError extends Error {
  details?: unknown;

  constructor(message: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.details = details;
  }
}

async function parseJsonOrThrow(response: Response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = typeof payload.error === "string" ? payload.error : "Užklausos nepavyko apdoroti.";
    throw new ApiError(message, payload.details);
  }
  return payload;
}

export async function fetchBootstrap(): Promise<BootstrapPayload> {
  const response = await fetch("/api/bootstrap/", {
    credentials: "include",
  });
  return parseJsonOrThrow(response);
}

export async function createStylingRequest(formData: FormData): Promise<CreateRequestResponse> {
  const response = await fetch("/api/requests/", {
    method: "POST",
    body: formData,
    credentials: "include",
  });
  return parseJsonOrThrow(response);
}

export async function fetchRequestStatus(requestId: string): Promise<RequestStatusPayload> {
  const response = await fetch(`/api/requests/${requestId}/status/`, {
    credentials: "include",
  });
  return parseJsonOrThrow(response);
}

export async function fetchRequestDetail(requestId: string): Promise<RequestDetailPayload> {
  const response = await fetch(`/api/requests/${requestId}/`, {
    credentials: "include",
  });
  return parseJsonOrThrow(response);
}

export { ApiError };
