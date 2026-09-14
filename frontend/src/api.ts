export type QuestionShift =
  | "unchanged"
  | "clarified"
  | "shifted_focus"
  | "different_question";

interface Pass1Response {
  session_id: string;
  reading: string;
}

interface Pass2Response {
  reading: string;
  takeaway_question: string;
}

const request = async <T>(path: string, body: Record<string, unknown>): Promise<T> => {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = (await response.json()) as T & { error?: string };
  if (!response.ok) {
    throw new Error(payload.error || `Request failed (${response.status})`);
  }
  return payload;
};

export const runPass1 = (input: {
  card: string;
  orientation: "upright" | "reversed";
  transcript: string;
}) => request<Pass1Response>("/api/pass1", input);

export const runPass2 = (input: {
  session_id: string;
  question: string;
  question_shift: QuestionShift;
  question_shift_note?: string;
}) => request<Pass2Response>("/api/pass2", input);
