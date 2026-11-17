---
paths:
  - 'frontend/src/components/**'
  - 'frontend/src/pages/**'
  - 'frontend/src/api/**'
---

# Rules: minimal error handling in the API layer and UI

- **API functions throw:** every function in `src/api/` checks `response.ok` and throws an `Error` with a readable message. Page components catch it, store the message in state and show it as plain text. No toast managers or error components.
- **One place reads error bodies:** `request()` and `readError()` live in `src/api/client.ts`; `posts.ts` and `options.ts` import them.
- **FastAPI's error body:** the message is in `detail`. A 422 sends a list, one item per invalid field; `readError()` joins it into one plain-text line. A 500 body is plain text, not JSON, so `readError()` does not parse it.
- **Expected "not found" is not an error:** `getPost()` returns `null` on a 404, so the page shows the not-found page. It also returns `null` on a 422: an id that is not a whole number (`/blog/abc` requests `/api/blog/NaN`) fails FastAPI's type check, and for the reader it is a missing post too.
- **No session code:** the frontend never calls the mock session endpoints. The cookie comes from the mock login in the Swagger UI at `http://localhost:8000/docs`, in the same browser (not `blog.http`, whose cookies stay in VS Code); a write without it shows the 401 `detail` (`Not signed in`) like any other error.
- **Separate error states:** a failed load replaces the page with the message; a failed save or delete keeps the form or the post on screen and shows the message below it.

<br>

## What the UI shows

| Answer                                | Message shown                                               |
| ------------------------------------- | ----------------------------------------------------------- |
| No answer (`fetch` throws), or a 502  | `Cannot reach the server. Check that the backend is running.` |
| 400, 401, 404 (save or delete)        | The `detail` string, for example `Unknown tag: CoffeeMyth`  |
| 422                                   | Every `msg`, joined: `title: String should have at least 1 character` |
| 500                                   | `Something went wrong on the server. Try again later.`      |

The Vite proxy answers 502 with an empty body when the backend is not running.

<br>

## Example: the shared helpers (`src/api/client.ts`)

```ts
const NETWORK_ERROR = 'Cannot reach the server. Check that the backend is running.';
const SERVER_ERROR = 'Something went wrong on the server. Try again later.';

/* One item of a 422 detail list. */
interface ValidationIssue {
  loc: (string | number)[];
  msg: string;
  type: string;
}

/* FastAPI's error body: one message, or one item per invalid field (422). */
interface ApiError {
  detail: string | ValidationIssue[];
}

// Sends the request; turns "no answer" into one clear message
export async function request(url: string, options?: RequestInit): Promise<Response> {
  let response: Response;

  try {
    response = await fetch(url, options);
  } catch {
    // fetch throws (a TypeError) only when no answer arrives: Vite stopped or the network is down
    throw new Error(NETWORK_ERROR);
  }

  if (response.status === 502) {
    throw new Error(NETWORK_ERROR);
  }

  return response;
}

// A 4xx or 5xx answer still resolves fetch, so the caller checks response.ok and throws this
export async function readError(response: Response): Promise<Error> {
  const isJson = response.headers.get('content-type')?.includes('application/json');

  if (!isJson) {
    return new Error(SERVER_ERROR);
  }

  const body: ApiError = await response.json();

  // loc ends with the field name, for example ['body', 'title']
  if (Array.isArray(body.detail)) {
    return new Error(
      body.detail.map((issue) => `${issue.loc.at(-1)}: ${issue.msg}`).join('; '),
    );
  }

  return new Error(body.detail);
}
```

<br>

## Example: `getPost()` and the not-found page

```ts
// src/api/posts.ts
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
```

<br>

## Example: an API function and its page

```ts
// src/api/posts.ts
export async function createPost(input: PostInput): Promise<PostDetail> {
  const response = await request(BASE_URL, jsonOptions('POST', input));

  if (!response.ok) {
    throw await readError(response);
  }

  return response.json();
}
```

```tsx
// src/pages/PostForm.tsx (shortened)
const [saveError, setSaveError] = useState<string | null>(null);

const handleSubmit = async (event: SubmitEvent<HTMLFormElement>) => {
  event.preventDefault();
  setSaveError(null);

  try {
    const savedPost = await createPost(input);
    navigate(`/blog/${savedPost.id}`);
  } catch (err) {
    setSaveError((err as Error).message);
  }
};

// Below the form fields: the typed values stay on screen
{saveError !== null && <p>{saveError}</p>}
```
