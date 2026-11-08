# Cooksy 🥬

Cooksy is a food and grocery idea by Amirhossein Aslani. This repository currently hosts a minimal **Hello World / Coming Soon** website.

- Public URL: https://cooksy.webigram.ir
- Server: `wbg-001`
- Application directory: `/opt/apps/cooksy`
- App container / internal DNS: `cooksy-web`
- Internal port: `80`
- Docker network: existing external `app-net`
- Health endpoint: `/healthz`
- Edge routing: managed independently in `amdkna/nginx-edge-wbg-001`
- CI/CD: Jenkins at `https://ci.webigram.ir`; node `deploy-wbg001`

## Deployment

The `Jenkinsfile` validates and builds changes on `main` using the isolated `build-docker-01` Jenkins agent. Only the trusted `production` branch deploys to `wbg-001` through `deploy-wbg001`. Configure a Jenkins multibranch pipeline with GitHub credentials to read this private repository and discover both branches.

Deployment builds the small site image on the production Docker host (no registry credentials required), manages **only** the `cooksy` Compose project, waits for container health and verifies the route from `edge-nginx`. It tries to restore the previous Cooksy image on failure. It does **not** touch the shared edge configuration.

Once deployed, test from the server:

```bash
docker compose -f /opt/apps/cooksy/compose.yml ps
docker exec edge-nginx wget -qO- http://cooksy-web/healthz
curl -I https://cooksy.webigram.ir/
```

## DNS and TLS

Point `cooksy.webigram.ir` to the public IP of `wbg-001`. The edge virtual host references the existing `/etc/nginx/ssl/webigram.ir/` wildcard certificate files; confirm that the installed certificate covers `cooksy.webigram.ir` before publishing. The edge workflow safely validates and reloads Nginx without restarting its container.

No public application ports, database or `.env` secrets are required for this placeholder.
