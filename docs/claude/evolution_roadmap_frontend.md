# Frontend evolution roadmap (React, Vite and Tailwind CSS)

This document outlines the progressive phases for building the frontend of our study project.

<br>

## Phase 1: static UI and local mock data

- **Goal:** Build the visual layout, components, and forms using hardcoded mock data or local component state (`useState`).
- **Focus:** Tailwind CSS styling, semantic HTML, accessibility (WCAG AA contrast), and component structure (`interface` for props, `UPPER_SNAKE_CASE` for class lists).
- **No network calls yet:** Components render arrays of hardcoded objects directly.
- **Before the first file:** read [ui_specifications.md](./ui_specifications.md) and [ui_visual_identity.md](../../.claude/rules/ui_visual_identity.md) first. The UI rules are path-scoped to `frontend/src/components/`, `pages/` and CSS files, so they are not in context during Vite, Tailwind or Prettier set-up. The Tailwind classes in the code examples below only illustrate the logic; the styling comes from these two files.

<br>

## Phase 2: API layer isolation and GET integration

- **Goal:** Extract data fetching out of components and into dedicated API service files (`src/api/posts.ts`).
- **Pattern:** Replace mock arrays with `useEffect`, `async/await`, and `try/catch`.
- **Vite proxy:** `vite.config.ts` keeps the default port (5173) and proxies `/api` to `http://localhost:8000`. API functions use relative paths such as `/api/blog`; the backend needs no CORS.
- **Validation:** Ensure API functions check `response.ok` and throw clean errors.

<br>

## Phase 3: error handling and loading states

- **Goal:** Implement robust, minimal user feedback for asynchronous actions.
- **Pattern:** Page components catch errors from API functions, store the message in local state (`setError(err.message)`), and render it as a simple plain-text error banner.
- **Validation:** Use native HTML5 attributes (`required`, etc.) for basic form checks.

<br>

## Phase 4: full CRUD mutations (create, update, delete)

- **Goal:** Wire up interactive forms and action buttons to backend `POST`, `PUT`, and `DELETE` endpoints.
- **Pattern:** Optimistic UI updates or simple state re-fetching after successful mutations.

<br>

## What this looks like in practice (Phase 1 vs Phase 2)

### Phase 1: the component with mock data (no backend needed)

When a new feature is started, build it like this first:

```tsx
// src/components/PostList.tsx (Phase 1: local mock data)
import { useState } from 'react';

const MOCK_POSTS = [
	{ id: 1, title: 'Mock Post One', summary: 'Testing layout...' },
	{ id: 2, title: 'Mock Post Two', summary: 'Tailwind styles look good.' }
];

export default function PostList() {
	const [posts] = useState(MOCK_POSTS);

	return (
		<div className="flex flex-col gap-4 p-6">
			<h1 className="text-2xl font-bold">Blog Posts</h1>
			{posts.map(post => (
				<div key={post.id} className="p-4 border rounded-xl">
					<h2 className="font-semibold">{post.title}</h2>
					<p className="text-gray-600">{post.summary}</p>
				</div>
			))}
		</div>
	);
}
```

### Phase 2: swapping to real data (wiring the API)

Once your backend is running, transition the component to Phase 2, and wrap it with `src/api/posts.ts` helper and `useEffect`:

```tsx
// src/components/PostList.tsx (Phase 2: real API integration)
import { useState, useEffect } from 'react';
import { getPosts } from '../api/posts';

export default function PostList() {
	const [posts, setPosts] = useState([]);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		async function load() {
			try {
				const data = await getPosts();
				setPosts(data);
			} catch (err: any) {
				setError(err.message);
			}
		}
		load();
	}, []);

	return (
		<div className="flex flex-col gap-4 p-6">
			<h1 className="text-2xl font-bold">Blog Posts</h1>
			{error && <p className="text-red-600 text-sm">{error}</p>}
			{posts.map((post: any) => (
				<div key={post.id} className="p-4 border rounded-xl">
					<h2 className="font-semibold">{post.title}</h2>
					<p className="text-gray-600">{post.summary}</p>
				</div>
			))}
		</div>
	);
}
```
