# Notes: GCP deployment with Terraform

This file is the build log of the deployment: the commands, files and checks, in the order the deployment was built. The plan and its reasons are in [evolution_roadmap_deployment.md](docs/claude/evolution_roadmap_deployment.md). The build log of the local app is [NOTES.md](NOTES.md).

<br>

## Contents

- [Goal](#goal)
- **Build log steps in development order:**
  1. [Serve the React build from FastAPI](#1-serve-the-react-build-from-fastapi)

<br>

## Goal

The app at tag `v0.3.0` (FastAPI, PostgreSQL and the React frontend) runs on GCP. One Cloud Run service serves the API and the React files, and Cloud SQL holds the database. Terraform creates every resource. The API contract does not change.

<br>

## 1. Serve the React build from FastAPI

- **Before:** two servers ran on the laptop. Vite served the React app on port 5173 and forwarded `/api` to FastAPI on port 8000. FastAPI served only the API.
- **Why the change:** Cloud Run runs one container, and the app needs no second server. When FastAPI also serves the built React files, the browser still sees one origin, as with the Vite proxy. So the API needs no CORS, and the session cookie keeps working unchanged.

Branch `feature/serve-frontend`. [main.py](backend/app/main.py) serves the files in `frontend/dist/` after every API route:

| Part                                     | Does                                                                                                                                         |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `FRONTEND_DIST`                          | The build folder, found from the location of `main.py`                                                                                       |
| `app.mount("/assets", StaticFiles(...))` | Serves the JS and CSS files that Vite names with a content hash                                                                              |
| `serve_frontend` on `/{path:path}`       | Returns a file from the root of `dist/` (such as `favicon.svg`), JSON `404` for an unknown `/api` path, and `index.html` for any other path |

Build the frontend in `frontend/`, then start the server in `backend/` (the database container must be running):

```bash
npm run build
```

```bash
uv run fastapi dev app/main.py
```

**Expected result:**

`serve_frontend` answers every path that no other route answers. FastAPI checks the routes in the order they are added, so `serve_frontend` is added last.

| Check                                                | Result                              | Shows                                                                                          |
| ---------------------------------------------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------- |
| Reload `http://localhost:8000/blog/1` in the browser | The post, not a `404`               | `/blog/1` is a React page, not a file. FastAPI returns `index.html`, and React shows the post. |
| `curl -i http://localhost:8000/api/unknown`          | `404` with `{"detail":"Not Found"}` | A wrong API path still gets a JSON error, not the React page.                                  |
| `curl -i http://localhost:8000/api/tags`             | `200` with the tags                 | `serve_frontend` does not hide the API routes.                                                 |
| `http://localhost:8000/docs` in the browser          | The Swagger UI                      | `serve_frontend` does not hide FastAPI's own pages either.                                     |
