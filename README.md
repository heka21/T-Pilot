# CASA Theory

A self-hosted study app for the Australian CASA **RPL(A)** and **PPL(A)** pilot theory exams.
It runs on your own machine (for example a Mac mini on your home network) and works fully offline:
no accounts, no cloud, no CDN.

What it does:

- **Syllabus** browser built from the Part 61 MOS Schedule 3 units (BAKC, RBKA, RFRC, ...), with a
  study status per subtopic (not started / studying / confident).
- **Notes** for each subtopic, written in Markdown.
- **Search** across notes, syllabus subtopics, MOS knowledge elements, questions, flashcards and
  reference pages (search box in the sidebar, or press `/`).
- **Quiz** practice by unit or subtopic, and timed **mock exams** in the RPLA/PPLA format with a
  knowledge deficiency report at the end.
- **Flashcards** with spaced repetition.
- **Planner** that spreads the syllabus over the days you have before your exam dates.
- **Issues**: every page has a small "report a problem" box; reports are listed under *Issues*.

> **Disclaimer.** This is a study aid only. All notes, questions and flashcards are original study
> material written for this app. They are **not** CASA exam questions and not CASA material.
> Always check regulatory numbers against the current AIP, Part 91 MOS and VFRG.

## Running it with Docker (recommended)

You need Docker Engine with the Compose plugin. From this folder:

```sh
docker compose up -d --build
```

Then open:

- <http://localhost:8081> on the Mac mini itself, or
- `http://<mac-mini-ip>:8081` from your phone, tablet or laptop on the same network
  (find the IP in *System Settings > Network*, or with `ipconfig getifaddr en0`).

Useful commands:

```sh
docker compose logs -f        # watch the logs
docker compose restart        # restart (re-reads content)
docker compose down           # stop (your progress is kept)
docker compose up -d --build  # rebuild after pulling updates or editing content
```

## Deploying from inside the dev container

The dev container includes the `docker-outside-of-docker` feature, which gives it the `docker` CLI
connected to the Docker Engine on the Mac. After a container rebuild (VS Code: "Dev Containers:
Rebuild Container"), deploy from a terminal in the container with:

```bash
docker compose up -d --build
```

The image is built on the Mac and the app is reachable at <http://localhost:8081> on the Mac.
`deploy.sh` is an alternative that deploys over SSH if the socket is not available.

## Where your progress is stored

Your progress (study status, quiz and exam attempts, flashcard schedule, study plan, reported
issues) lives in a SQLite database inside the Docker named volume **`casa_data`**, mounted at
`/app/data` in the container. It survives restarts, rebuilds and `docker compose down`.
(`docker compose down -v` **deletes** it.)

### Back up

```sh
docker run --rm -v casa_data:/data -v $(pwd):/backup alpine tar czf /backup/casa_data.tgz /data
```

This writes `casa_data.tgz` into the current folder. Note: Compose may prefix the volume name with
the project folder name (e.g. `casa-theory_casa_data`); check with `docker volume ls` and use that
name if so.

### Restore

```sh
docker compose down
docker run --rm -v casa_data:/data -v $(pwd):/backup alpine sh -c "rm -rf /data/* && tar xzf /backup/casa_data.tgz -C /"
docker compose up -d
```

## Editing content

Notes, questions, flashcards and exam settings live in `content/` as Markdown, YAML and JSON.
See [content/README.md](content/README.md) for the file formats.

Content is loaded into the database every time the app starts. Editing content never touches your
progress. To apply changes:

- **Rebuild** (content is baked into the image): `docker compose up -d --build`, or
- **Live editing**: uncomment the `./content:/app/content:ro` line in `docker-compose.yml`, run
  `docker compose up -d` once, then after each edit just `docker compose restart`.

## Local development without Docker

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```sh
uv venv
uv pip install -e ".[dev]"
source .venv/bin/activate
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>. The database goes to `./data/casa-theory.db` by default; set
`DATA_DIR` or `DATABASE_URL` to change it, and `CONTENT_DIR` to point at a different content folder.

## Styling (Tailwind)

The interface is styled with [Tailwind CSS](https://tailwindcss.com) v4. The compiled stylesheet
`app/static/app.css` is committed, so the Python app and the Docker image need no Node at runtime and the
app stays fully offline. Node is only needed when you change the design:

```sh
npm install                 # once; installs the Tailwind CLI and typography plugin
npm run css                 # rebuild app/static/app.css from app/static/src/app.css
npm run css:watch           # rebuild on every template change while developing
```

Design tokens (colours for light and dark mode, radii, shadows) and the reusable component classes
(`card`, `btn-primary`, `badge`, `status-badge`, `option`, `flashcard`, ...) live in `app/static/src/app.css`.
Templates use those classes plus Tailwind utilities. Dark mode follows the device setting.

## Running tests

```sh
pytest -q
```

Tests use a temporary SQLite database, so they never touch your real progress.
