# Academic Artifact Research Database

## Project Summary

### One-sentence description of the project

A full-stack web application for browsing, searching, and visualizing academic artifacts on an interactive map, backed by a PostgreSQL database and MinIO object storage.

### Additional information about the project

The Academic Artifact Research Database provides researchers and students with a centralized platform to explore historical and academic artifacts. Users can search the catalog by material type and date range, view artifacts plotted on an interactive Leaflet map by their geographic origin, and drill into individual objects to see high-resolution images, metadata, and bibliographic citations. The application is fully containerized with Docker Compose, making it easy to spin up for local development or deploy to a cloud environment.

## Installation

### Prerequisites

Before getting started, make sure you have the following installed:

- **Git** — [https://git-scm.com](https://git-scm.com)
- **Docker** & **Docker Compose** — [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)
- **Node.js** (v18 or later) — only needed for local frontend development outside Docker
- **Python 3.10+** — only needed for local backend development outside Docker

### Add-ons

| Add-on | Purpose |
|---|---|
| **FastAPI** | High-performance Python web framework for the REST API |
| **SQLAlchemy** | ORM for database models and queries |
| **Pydantic** | Data validation and serialization for API request/response schemas |
| **Uvicorn** | ASGI server to run the FastAPI application |
| **psycopg2-binary** | PostgreSQL database adapter for Python |
| **React 19** | Frontend UI library |
| **React Router v7** | Client-side routing |
| **Leaflet / React-Leaflet** | Interactive map visualization |
| **Axios** | HTTP client for API calls |
| **Tailwind CSS v4** | Utility-first CSS framework for styling |
| **Vite** | Frontend build tool and dev server |
| **MinIO** | S3-compatible object storage for artifact images |
| **PostgreSQL 15** | Relational database |

### Installation Steps

1. **Clone the repository**

```bash
git clone git@github.com:Keagasourus/Cpts421Project.git
cd Cpts421Project
```

2. **Start all services with Docker Compose**

```bash
cd deployment
docker compose up --build
```

This single command will:
- Start a **PostgreSQL 15** database and automatically run the schema migration and seed data
- Build and start the **FastAPI backend** on [http://localhost:8000](http://localhost:8000)
- Build and start the **React frontend** on [http://localhost:3000](http://localhost:3000)
- Start a **MinIO** object-storage server on [http://localhost:9000](http://localhost:9000) (console at [http://localhost:9001](http://localhost:9001))
- Create the `uploads` bucket in MinIO and populate it with sample artifact images

3. **Open the application**

Navigate to [http://localhost:3000](http://localhost:3000) in your browser.

#### Local Development (without Docker)

If you prefer to run services individually:

**Backend:**
```bash
cd code/backend
python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

**Frontend:**
```bash
cd code/frontend
npm install
npm run dev
```

> **Note:** When running locally you'll need a PostgreSQL instance running with the schema from `code/backend/src/schema.sql` applied, and the `DATABASE_URL` environment variable set (e.g., `postgresql://user:password@localhost:5432/dev_db`).

## Functionality

1. **Landing Page** — Visit the home page at `/` for an overview of the project and navigation links.
2. **Search & Filter** — Navigate to `/search` to browse the artifact catalog. Use the filter sidebar to narrow results by material type, date range, and tags.
3. **Map Visualization** — Go to `/map` to view all geolocated artifacts plotted on an interactive Leaflet map. Click a marker to see artifact details.
4. **Object Detail** — Click on any artifact to visit its detail page (`/objects/:id`), where you can view high-resolution images, metadata (material, date range, dimensions), and bibliographic citations.

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check / welcome message |
| `GET` | `/objects/search` | Search artifacts with optional filters (`material`, `year`, `date_start`, `date_end`) |
| `GET` | `/objects/map` | Get all artifacts with map coordinates |
| `GET` | `/objects/{id}` | Get full details for a single artifact |
| `GET` | `/tags` | List all available tags |

## Known Problems

- The search bar only partially works — keyword search is not yet fully implemented; only material and date-range filters are functional.
- The README template and LICENSE file are still placeholders and need to be finalized.
- No automated test suite is currently running in CI (tests exist but are not integrated into the GitHub Actions workflow).

## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D

## Additional Documentation

- [Sprint 1 Report](Sprints/Sprint_1/Sprint_Report/Sprint1_Report.md)
- [Database Schema Documentation](data/README.md)
- [Backend API Documentation](code/backend/API_Documentation.md)
- [Deployment Architecture](deployment/cloud_architecture.md)
- [Docker Compose Configuration](deployment/docker-compose.yml)

## License

MIT License — see [LICENSE](LICENSE) for details.