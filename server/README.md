# ExamSprint full-stack server

This folder is the optional cloud version of the local app. It contains the
Python backend, the preloaded probability pack, and the generated web assets.

## Render free deployment

1. Create a Render account with GitHub.
2. New → Blueprint → connect this repository.
3. Render reads `render.yaml` from the repository root.
4. Set `EXAMSPRINT_ACCESS_TOKEN` to a private password you choose. The app uses
   HTTP Basic auth: any username + this password.
5. Deploy. The first build installs Python packages and may take 2–4 minutes.

Free Render notes:

- The instance sleeps after a period of inactivity; first request is slow.
- The filesystem is ephemeral. Uploaded files, API keys, and progress can be
  lost on restart/redeploy. For durable personal use, add a paid persistent disk
  or move `data/` to a database.
- Set an access token. Without it, anyone with the URL can use the app and
  change settings.

## Local test of the container

```bash
docker build -t examsprint .
docker run --rm -p 10000:10000 \
  -e EXAMSPRINT_ACCESS_TOKEN=change-me \
  examsprint
```

Open `http://127.0.0.1:10000`, username anything, password `change-me`.
