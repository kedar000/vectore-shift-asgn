# 🔌 Integrations Project – Local Setup

This project allows integration with third-party platforms like **HubSpot**, **Notion**, and **Airtable** using OAuth2.
Assignment is to Integrate HubSpot

---

## Step 1: Start Redis
Make sure Redis is installed and running.

```bash
redis-server
```

## Step 1: Start Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## Step 1: Start frontend
```bash
cd frontend
npm install
npm run start
```

## Step 1: Docs
http://localhost:8000/docs