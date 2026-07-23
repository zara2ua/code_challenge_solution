# Code Challenge Solution

## Event Sync Service

A Python 3 Flask microservice and single-page dashboard designed to ingest, reconcile, and display meeting records from disparate source systems (Calendar API and CRM API).


## 🌟 Overview
Different business tools often track the same real-world meeting with inconsistent formats, missing fields, or conflicting details. This service ingests two non-standard JSON datasets, runs a deterministic and heuristic reconciliation pipeline to merge matching records, and serves a unified dataset via a REST API and a Vue.js frontend interface.


## ✨ Features
Data Ingestion & Normalization: Robustly handles ISO 8601 datetimes, non-standard dates (e.g., 03-15/2025), missing timestamps, and null values.

Intra-Source Deduplication: Filters out redundant records within individual datasets prior to matching.

Cross-Source Fuzzy Reconciliation: Matches Calendar and CRM records using a multi-factor scoring model based on:

Date/Time proximity

Client name and company string comparison

Attendee email domain matching (e.g., matching client domains to CRM client records)

String similarity scoring on meeting titles/subjects

Conflict & Missing Field Resolution:

Merges location data and notes across sources.

Inters and labels missing client details or internal meetings cleanly.

RESTful Endpoint: Exposes /api/data returning clean, structured JSON.

Vue 3 Dashboard: Served directly at /meetings to browse unified records, complete with status tags and system source provenance (Calendar vs CRM IDs).


## Project Structure

    my_flask_app/
    ├── app.py              # Main Flask server & route handlers
    ├── reconciler.py       # Reconciliation engine, normalization, and logic
    ├── requirements.txt    # Python dependencies
    ├── templates/
    │   └── index.html      # Frontend Vue.js single-page dashboard
    └── api/
        └── data/
            ├── calendar_events.json  # Source A (Calendar API records)
            └── crm_events.json  # Source B (CRM API records)


## 🛠️ Technology Stack

* Backend: Python 3, Flask, python-dateutil

* Frontend: Vue.js 3 (CDN), HTML5, CSS3

* Data Sources: JSON files (/api/data/calendar_events.json, /api/data/crm_events.json)


## 🚀 Getting Started

### Prerequisites

* Python 3.11+
* pip package manager

### Installation

1.- Clone or download the repository:

    git clone <repository-url>
    cd my_flask_app


2.- Create and activate a virtual environment:

    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate


3.- Install dependencies:

    pip install -r requirements.txt


4.- Run the application:

    python3 app.py

    The app will start at [http://127.0.0.1:5000](http://127.0.0.1:5000).

## API Reference & Routes

|Endpoint|Method|Description|
| --- | --- | --- |
|/meetings|GET|Renders the Vue 3 frontend UI dashboard.|
|/api/data|GET|Returns the reconciled list of unified meetings as JSON.|
|/data|GET|Alias for /api/data.|


## Sample API Output (/api/data)

    {
        "status": "success",
        "count": 1,
        "data": [
            {
            "unified_id": "UNI-CAL-A1-CRM-1001",
            "title": "Q1 Portfolio Review - Meridian Capital",
            "client": {
                "name": "David Park",
                "company": "Meridian Capital"
            },
            "organizer": "sarah.chen@firma.com",
            "attendees": [
                "sarah.chen@firma.com",
                "david.park@meridiancap.com"
            ],
            "date": "2025-03-10",
            "status": "confirmed",
            "location": {
                "calendar_location": "Conference Room B",
                "crm_location": "HQ - Conference Room B",
                "resolved_location": "HQ - Conference Room B"
            },
            "sources": {
                "calendar_id": "CAL-A1",
                "crm_id": "CRM-1001"
            }
            }
        ]
    }

