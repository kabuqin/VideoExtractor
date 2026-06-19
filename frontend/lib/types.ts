export type TaskStatus =
  | "pending"
  | "checking_platform"
  | "resolving_url"
  | "downloading_video"
  | "video_downloaded"
  | "extracting_audio"
  | "loading_whisper_model"
  | "transcribing_audio"
  | "segmenting_text"
  | "restoring_punctuation"
  | "rewriting_text"
  | "generating_copy"
  | "completed"
  | "failed"
  | "cancelled";

export type Task = {
  id: string;
  source_url: string;
  normalized_url: string | null;
  source_platform: string | null;
  target_platform: string;
  style: string;
  language: string;
  whisper_model: string;
  whisper_device: string;
  status: TaskStatus;
  progress: number;
  current_step: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
};

export type CreateTaskPayload = {
  url: string;
  target_platform: string;
  style: string;
  language: string;
  whisper_model: string;
  whisper_device: string;
};

export type Video = {
  id: string;
  task_id: string;
  platform: string | null;
  video_id: string | null;
  source_url: string | null;
  title: string | null;
  author: string | null;
  duration: number | null;
  thumbnail_url: string | null;
  video_path: string | null;
  audio_path: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export type Transcript = {
  id: string;
  task_id: string;
  raw_text: string | null;
  segmented_text: string | null;
  punctuated_text: string | null;
  rewritten_text: string | null;
  edited_text: string | null;
  created_at: string;
  updated_at: string;
};

export type Copy = {
  id: string;
  task_id: string;
  title: string | null;
  summary: string | null;
  body: string | null;
  hashtags: string[];
  platform: string;
  style: string;
  prompt_version: string;
  created_at: string;
};

export type TranscriptUpdatePayload = {
  edited_text: string;
};

export type CopyUpdatePayload = {
  title?: string;
  summary?: string;
  body?: string;
  hashtags?: string[];
};

export type RewritePayload = {
  target_platform?: string;
  style?: string;
  use_edited_transcript?: boolean;
};
