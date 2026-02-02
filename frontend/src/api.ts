// api.ts - API 请求封装
export interface ApiResponse {
  ok: boolean;
  action: 'record' | 'query' | 'confirm' | 'reject';
  tool_called: string | null;
  today_fragments: Fragment[];
  input_text: string;
  error?: string;
}

export interface Fragment {
  id: string;
  type: string;
  content: string;
  occurred_date: string;
  source: string;
  author?: string;
  tags: string[];
  created_at: string;
}

export interface SubmitRequest {
  text: string;
  author: string;
  date?: string; // 可选参数，格式 YYYY-MM-DD
}

export async function submitInput(request: SubmitRequest): Promise<ApiResponse> {
  const response = await fetch('/api/input', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

export interface DeleteResponse {
  ok: boolean;
  deleted_id?: string;
  today_fragments: Fragment[];
  error?: string;
}

export async function deleteFragment(fragmentId: string): Promise<DeleteResponse> {
  const response = await fetch(`/api/fragments/${fragmentId}`, {
    method: 'DELETE',
  });

  if (!response.ok && response.status !== 404) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}
