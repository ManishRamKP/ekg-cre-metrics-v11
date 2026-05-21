# finflow-ekg-cre-metrics-v11

A lightweight Flask microservice for managing the **enterprise knowledge graph (EKG)** that powers the Credit Recommendation Engine. It handles creating and updating OUTBOUND edges in a RedisGraph instance with CRE metrics derived from GST invoice data.

---

## Overview

This service exposes a single API endpoint that accepts GST transaction data and upserts edges in a RedisGraph graph. Each edge represents a borrower–trader relationship and carries invoice-level metrics used downstream by the credit scoring engine.

---

## Prerequisites

- Python 3.8+
- A running RedisGraph instance
- Docker (for containerised deployment)

---

## Configuration

All sensitive configuration is supplied via environment variables — nothing is hardcoded.

| Variable | Description |
|---|---|
| `REDIS_HOST` | Hostname or IP of your RedisGraph instance |
| `REDIS_PASSWORD` | Redis authentication password |

Set them before running:

```bash
export REDIS_HOST=your-redis-host
export REDIS_PASSWORD=your-redis-password
```

---

## Running Locally

```bash
# 1. Clone the repo
git clone https://github.com/your-org/finflow-ekg-cre-metrics-v11.git
cd finflow-ekg-cre-metrics-v11

# 2. Create virtual environment
python -m venv venv && source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
export REDIS_HOST=your-redis-host
export REDIS_PASSWORD=your-redis-password

# 5. Run
python ekg_cre_redis.py
```

Service runs on `http://localhost:5000`.

---

## Docker Deployment

```bash
# Build
docker build -t ekg-cre-metrics .

# Tag for GCP Artifact Registry
docker tag ekg-cre-metrics YOUR_GCP_REGION-docker.pkg.dev/YOUR_GCP_PROJECT_ID/YOUR_REPO/ekg-cre-metrics

# Push
docker push YOUR_GCP_REGION-docker.pkg.dev/YOUR_GCP_PROJECT_ID/YOUR_REPO/ekg-cre-metrics
```

`deployment_build.bat` automates the above on Windows after you update the registry path.

---

## API Reference

### `POST /edges`

Creates or updates OUTBOUND edges in the RedisGraph graph for each borrower–trader GSTIN pair.

**Request body** — array of transaction objects:

```json
[
  {
    "ptgstin": "27XXXXXXXXXXXXX",
    "ctin": "29XXXXXXXXXXXXX",
    "1_3_months": 5,
    "2_3_months": 3,
    "3_3_months": 2,
    "4_3_months": 1,
    "numberofinvoices": 11,
    "avginvoiceamount": 250000,
    "opvin": "36",
    "invoice_to_cashflow_ema": 0.82,
    "recentdate": "2024-01-10T00:00:00.000",
    "source": "GST",
    "ptgstinscore": 8.5,
    "ctinscore": 9.0,
    "totalinvoiceamount": 2750000
  }
]
```

**Response**

```json
{
  "message": "Edge processing complete",
  "details": [
    {
      "action": "updated",
      "edge_id": 42,
      "source_gstin": "27XXXXXXXXXXXXX",
      "dest_gstin": "29XXXXXXXXXXXXX"
    }
  ]
}
```

`action` will be `"created"` for new edges or `"updated"` for existing ones.

---

## Graph Schema

- **Node label:** `enterprise`
- **Node property:** `gstin`
- **Edge type:** `OUTBOUND`
- **Graph name:** `nodes_finflowgraph`

---

## Security Notes

- Never hardcode Redis credentials — always use environment variables.
- In production, inject secrets via a secrets manager (GCP Secret Manager, AWS Secrets Manager) rather than plain environment variables.
