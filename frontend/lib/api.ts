import type {
  Copy,
  CopyUpdatePayload,
  CreateTaskPayload,
  RewritePayload,
  Task,
  Transcript,
  TranscriptUpdatePayload,
  Video,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

export async function createTask(payload: CreateTaskPayload): Promise<{ task_id: string }> {
  const response = await fetch(`${API_BASE}/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json();
}

export async function listTasks(): Promise<Task[]> {
  const response = await fetch(`${API_BASE}/tasks`, { cache: "no-store" });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json();
}

export async function getTask(taskId: string): Promise<Task> {
  const response = await fetch(`${API_BASE}/tasks/${taskId}`, { cache: "no-store" });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json();
}

export async function startTask(taskId: string): Promise<Task> {
  const response = await fetch(`${API_BASE}/tasks/${taskId}/start`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json();
}

export async function getVideo(taskId: string): Promise<Video | null> {
  const response = await fetch(`${API_BASE}/videos/${taskId}`, { cache: "no-store" });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json();
}

// Transcript API
export async function getTranscript(taskId: string): Promise<Transcript | null> {
  const response = await fetch(`${API_BASE}/transcripts/${taskId}`, { cache: "no-store" });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json();
}

export async function updateTranscript(
  taskId: string,
  payload: TranscriptUpdatePayload,
): Promise<Transcript> {
  const response = await fetch(`${API_BASE}/transcripts/${taskId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json();
}

// Copy API
export async function getCopy(taskId: string): Promise<Copy | null> {
  const response = await fetch(`${API_BASE}/copies/${taskId}`, { cache: "no-store" });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json();
}

export async function updateCopy(taskId: string, payload: CopyUpdatePayload): Promise<Copy> {
  const response = await fetch(`${API_BASE}/copies/${taskId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json();
}

export async function rewriteCopy(taskId: string, payload?: RewritePayload): Promise<Copy> {
  const response = await fetch(`${API_BASE}/copies/${taskId}/rewrite`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload ?? {}),
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json();
}
