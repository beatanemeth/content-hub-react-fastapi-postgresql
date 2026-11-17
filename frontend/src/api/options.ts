import { readError, request } from './client.ts';
import type { Label } from './posts.ts';

// The form's checkboxes come from these lists, so a new category in the database appears without a code change
export async function getCategories(): Promise<Label[]> {
  const response = await request('/api/categories');

  if (!response.ok) {
    throw await readError(response);
  }

  return response.json();
}

export async function getTags(): Promise<Label[]> {
  const response = await request('/api/tags');

  if (!response.ok) {
    throw await readError(response);
  }

  return response.json();
}
