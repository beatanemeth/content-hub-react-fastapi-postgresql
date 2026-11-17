import { readError, request } from './client.ts';

// A relative path: the Vite proxy forwards /api requests to the backend
const BASE_URL = '/api/blog';

/* The staff member who wrote the post. */
export interface Author {
  id: number;
  full_name: string;
}

/* A category or a tag: both have the same two fields. */
export interface Label {
  id: number;
  label: string;
}

/* One post as GET /api/blog returns it: what the list shows. */
export interface PostSummary {
  id: number;
  title: string;
  summary: string;
  /* The API sends dates as text, for example '2026-06-01'. */
  published_on: string;
  author: Author;
}

/* One post as GET /api/blog/:id, POST and PUT return it. */
export interface PostDetail extends PostSummary {
  body: string;
  /* ISO 8601 in UTC, for example '2025-06-13T15:27:28Z'. */
  updated_at: string;
  categories: Label[];
  tags: Label[];
  /* Calculated by the API from body; never sent back. */
  minutes_to_read: number;
}

/* The body of POST and PUT: labels, not ids; the API sets the author from the session. */
export interface PostInput {
  title: string;
  summary: string;
  body: string;
  published_on: string;
  categories: string[];
  tags: string[];
}

// Both POST and PUT send the post fields as JSON
function jsonOptions(method: string, input: PostInput): RequestInit {
  return {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  };
}

export async function getPosts(): Promise<PostSummary[]> {
  const response = await request(BASE_URL);

  if (!response.ok) {
    throw await readError(response);
  }

  return response.json();
}

// null for an unknown id (404) or an id that is not a whole number (422), so the page shows its not-found state
export async function getPost(id: number): Promise<PostDetail | null> {
  const response = await request(`${BASE_URL}/${id}`);

  if (response.status === 404 || response.status === 422) {
    return null;
  }

  if (!response.ok) {
    throw await readError(response);
  }

  return response.json();
}

// The API answers 201 Created with the new post, which carries its new id
export async function createPost(input: PostInput): Promise<PostDetail> {
  const response = await request(BASE_URL, jsonOptions('POST', input));

  if (!response.ok) {
    throw await readError(response);
  }

  return response.json();
}

export async function updatePost(
  id: number,
  input: PostInput,
): Promise<PostDetail> {
  const response = await request(
    `${BASE_URL}/${id}`,
    jsonOptions('PUT', input),
  );

  if (!response.ok) {
    throw await readError(response);
  }

  return response.json();
}

// The API answers 204 No Content, so there is nothing to return
export async function deletePost(id: number): Promise<void> {
  const response = await request(`${BASE_URL}/${id}`, { method: 'DELETE' });

  if (!response.ok) {
    throw await readError(response);
  }
}
