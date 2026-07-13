# 📊 TrendIntel: Developer Trend Intelligence Platform

![TrendIntel Dashboard](https://img.shields.io/badge/Status-Live-success)
![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)

**TrendIntel** is an autonomous, full-stack Developer Trend Intelligence Platform designed to track, aggregate, and analyze real-time developer activity. By continuously gathering data from the tech industry's three largest developer ecosystems—**GitHub, Hacker News, and DEV.to**—the platform extracts and transforms raw telemetry into actionable metrics.

---

## 🚀 Features

* **Autonomous ETL Pipeline:** A background `APScheduler` worker continuously polls REST APIs to extract the latest data every hour without blocking the main web server.
* **Custom Trend-Ranking Algorithm:** Applies mathematical weights to engagement metrics (stars, comments, upvotes) and utilizes logarithmic recency decay to ensure outdated trends age out naturally.
* **Optimized Storage Engine:** Powered by SQLite and SQLModel (ORM), featuring custom indexes and foreign keys for rapid historical queries and relational integrity.
* **Contextual AI Chat:** Allows users to interact with and query historical trend data directly.
* **Single-Host Full-Stack Routing:** A responsive HTML/CSS/JS dashboard served seamlessly on the same port as the backend API using FastAPI's static/template routing.

---

## 🏗️ Architecture

```text
 [GitHub / HN / DEV.to APIs]
            │
            ▼  (Hourly Interval)
 ┌──────────────────────────────────────┐
 │  1. BACKEND ETL PIPELINE             │
 │  • APScheduler Background Thread     │
 │  • Trend-Ranking & Decay Algorithm   │
 └──────────┬───────────────────────────┘
            │
            ▼
 ┌──────────────────────────────────────┐
 │  2. DATA STORAGE LAYER               │
 │  • SQLite Database                   │
 │  • SQLModel ORM Mapping              │
 │  • Custom Indexes & Foreign Keys     │
 └──────────┬───────────────────────────┘
            │
            ▼  (FastAPI Single-Host Routing)
 ┌──────────────────────────────────────┐
 │  3. USER INTERACTION LAYER           │
 │  • Responsive Frontend Dashboard     │
 │  • Live Data Visualizations          │
 │  • Contextual AI Chat Integration    │
 └──────────────────────────────────────┘
