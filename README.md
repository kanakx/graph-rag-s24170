# teg-s24170-s35256

### Work & Naming Conventions

We keep everything tied to GitHub Issues so we can work asynchronously.

#### Workflow proposition

- Create an Issue for every user story
- Use the following branch naming convention `<type>/<issue-number>-branch-name`, like `feature/389-basic-rag`
- Use `dev` branch

The above allows GitHub to update the kanban board automatically. 

### How to run the app in dev

#### Infrastructure

```bash
docker compose --profile dev --env-file .env.dev up -d
```

- Neo4j Browser: [http://localhost:7474/browser/](http://localhost:7474/browser/)

#### Dependencies

```bash
uv sync
```
