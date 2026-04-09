# Sprint 1 Report (January 20, 2026 – February 18, 2026)

## YouTube link of Sprint 1 Video (Make this video unlisted)

TODO: Add YouTube link here

## What's New (User Facing)
 * Searchable artifact catalog — users can browse and search academic artifacts by keyword
 * Filter sidebar — filter artifacts by category, date range, and other metadata
 * Interactive map visualization — view artifact origin locations on an interactive map
 * Dedicated object detail page — click any artifact to see full details and associated images
 * Landing page — a welcoming entry point that introduces the project and guides users into the catalog

## Work Summary (Developer Facing)
This sprint focused on standing up the full-stack foundation for the academic artifact research application. We began by establishing the repository structure, Git workflows, and a `.gitignore`. Next, we designed and implemented a PostgreSQL database schema supporting objects, sources, images, tags, and fuzzy date queries, along with SQL test cases for validation. Docker and Docker Compose were configured to orchestrate the backend, frontend, database, and a MinIO object-storage container seeded with sample images. The backend was initially prototyped with Flask, then migrated to FastAPI with SQLAlchemy ORM, Pydantic schemas, and a repository pattern for clean data access. On the frontend, we built a React application (Vite) featuring a search page with filtering, an artifact grid, a Leaflet-based map visualizer, individual object detail pages, and a landing page — all wired to the backend API. A GitHub Actions CI workflow was added to verify required repository structure on each push. The main challenge was coordinating the Docker networking and CORS configuration so the frontend, backend, and MinIO services could communicate correctly in both local and containerized environments.

## Unfinished Work
The search bar only partaily works. Minor items such as polishing the README and final UI styling were deferred to Sprint 2 as they were non-blocking.

## Completed Issues/User Stories
Here are links to the issues that we completed in this sprint:

 * https://github.com/Keagasourus/Cpts421Project/pull/8 — Frontend implementation (search, filter, map, artifact grid)
 * https://github.com/Keagasourus/Cpts421Project/pull/9 — Data gathering and filtering pipeline

TODO: Add links to any additional GitHub Issues that were tracked for this sprint.

## Incomplete Issues/User Stories
Here are links to issues we worked on but did not complete in this sprint:

 * None — all planned work for Sprint 1 was completed.

## Code Files for Review
Please review the following code files, which were actively developed during this sprint, for quality:
 * [main.py](https://github.com/Keagasourus/Cpts421Project/blob/main/code/backend/src/main.py) — FastAPI application entry point with all API routes
 * [models.py](https://github.com/Keagasourus/Cpts421Project/blob/main/code/backend/src/models.py) — SQLAlchemy ORM models for the database schema
 * [schemas.py](https://github.com/Keagasourus/Cpts421Project/blob/main/code/backend/src/schemas.py) — Pydantic request/response schemas
 * [database.py](https://github.com/Keagasourus/Cpts421Project/blob/main/code/backend/src/database.py) — Database connection and session configuration
 * [schema.sql](https://github.com/Keagasourus/Cpts421Project/blob/main/code/backend/src/schema.sql) — PostgreSQL DDL schema
 * [SearchPage.jsx](https://github.com/Keagasourus/Cpts421Project/blob/main/code/frontend/src/pages/SearchPage.jsx) — Search page with filter integration
 * [ObjectPage.jsx](https://github.com/Keagasourus/Cpts421Project/blob/main/code/frontend/src/pages/ObjectPage.jsx) — Artifact detail page
 * [MapVisualizer.jsx](https://github.com/Keagasourus/Cpts421Project/blob/main/code/frontend/src/components/MapVisualizer.jsx) — Leaflet-based map component
 * [LandingPage.jsx](https://github.com/Keagasourus/Cpts421Project/blob/main/code/frontend/src/pages/LandingPage.jsx) — Landing page component

## Retrospective Summary
Here's what went well:
  * Successfully stood up the entire full-stack architecture (React + FastAPI + PostgreSQL + MinIO) from scratch
  * Docker Compose setup allows any developer to spin up the full environment with a single command
  * Migrating from Flask to FastAPI early on gave us a more robust and well-typed backend
  * CI pipeline with GitHub Actions was established early, enforcing repository structure standards

Here's what we'd like to improve:
   * Better use of GitHub Issues to track individual tasks
   * More frequent, smaller pull requests instead of large feature branches
   * Improved code review process


Here are changes we plan to implement in the next sprint:
   * Implement document export functionality
   * Improve the UI design and overall visual polish
   * Set up automated testing with proper unit and integration tests
   * Fix the search functionality
   * Add more data to the database