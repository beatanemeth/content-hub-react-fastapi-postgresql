const NETWORK_ERROR =
  'Cannot reach the server. Check that the backend is running.';
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
export async function request(
  url: string,
  options?: RequestInit,
): Promise<Response> {
  let response: Response;

  try {
    response = await fetch(url, options);
  } catch {
    // fetch throws (a TypeError) only when no answer arrives: Vite stopped or the network is down
    throw new Error(NETWORK_ERROR);
  }

  // The Vite proxy answers 502 with an empty body when FastAPI is not running
  if (response.status === 502) {
    throw new Error(NETWORK_ERROR);
  }

  return response;
}

// A 4xx or 5xx answer still resolves fetch, so the caller checks response.ok and throws this
export async function readError(response: Response): Promise<Error> {
  // A 500 from FastAPI is plain text, not JSON
  const isJson = response.headers
    .get('content-type')
    ?.includes('application/json');

  if (!isJson) {
    return new Error(SERVER_ERROR);
  }

  const body: ApiError = await response.json();

  // loc ends with the field name, for example ['body', 'title']
  if (Array.isArray(body.detail)) {
    return new Error(
      body.detail
        .map((issue) => `${issue.loc.at(-1)}: ${issue.msg}`)
        .join('; '),
    );
  }

  return new Error(body.detail);
}
