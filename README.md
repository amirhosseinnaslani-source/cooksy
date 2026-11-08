# Cooksy | کوکسی

**غذاتو انتخاب کن، موادش با ما!** An ingredient-kit ordering site: customers choose a recipe and servings, then request delivery of the ingredients instead of prepared food.

## Customer journeys

- Home customers: name, telephone, delivery address, recipes and servings.
- Business customers: company name, company contact, telephone, delivery address and recipes with larger servings.
- Each recipe shows required ingredients (quantities returned by the API are per serving), estimated preparation time and **illustrative** per-serving prices.
- A cart calculates estimated quantities/prices, and checkout saves a request in SQLite.
- No payment integration, automated fulfillment, administrative UI or confirmation notifications yet. The order is a request, not a confirmed sale.

## Deployment

- Public host: https://cooksy.webigram.ir
- Server: wbg-001
- Directory: /opt/apps/cooksy
- Container/DNS: cooksy-web
- Container port: 8080
- Edge config: nginx-edge-wbg-001/conf.d/cooksy.webigram.ir.conf (must forward to cooksy-web:8080)
- Docker network: app-net
- Persistent DB: named Compose volume cooksy_orders mounted at /data
- Jenkins: main validates; production branch deploys on deploy-wbg001
- API: GET /api/recipes, POST /api/orders, GET /healthz

For local development:

```bash
COOKSY_DATA_DIR=/tmp/cooksy-test-data python3 app.py
```

Then visit http://localhost:8080 (Python 3.12+ recommended). Orders are stored in SQLite under the configured data directory. The public API intentionally does not expose orders; only an authorized server operator can inspect the SQLite database.

**Security and production readiness:** This is an early MVP. Add authentication and authorization for future order-management endpoints, request throttling, anti-abuse controls, fulfillment workflow, true supplier prices, delivery coverage rules, privacy notice and retention policy before public marketing. The sample prices shown in the UI are placeholders.

The Jenkins deployment only changes the Cooksy Compose project, retaining the named Docker volume for orders; it never restarts shared edge-nginx.
