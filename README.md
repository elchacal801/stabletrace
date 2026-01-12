# StableTrace

**Stablecoin Telemetry & Risk Observatory**

StableTrace is a full-stack telemetry and risk monitoring dashboard for the global stablecoin market. It aggregates real-time supply data, price feeds, and sanctions lists to provide a comprehensive view of the stablecoin ecosystem.

![StableTrace Dashboard](docs/dashboard_preview.png)

## Features

- **Market Dashboard**: Real-time total supply tracking, historical trends, and top asset breakdowns (sourced from DefiLlama).
- **Risk Overlay**: Unified search and filtering for sanctioned crypto entities (OFAC, OpenSanctions, CryptoScamDB).
- **Data Pipeline**: Robust ingestion engine validating and normalizing data from multiple sources into a warehouse.

## Tech Stack

- **Backend**: Python (FastAPI), DuckDB (Warehouse)
- **Frontend**: Next.js 14, TailwindCSS, Recharts
- **Ingestion**: Custom Python connectors

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Git

### Backend Setup

1. Clone the repository:

    ```bash
    git clone https://github.com/elchacal801/stabletrace.git
    cd stabletrace
    ```

2. Create and activate a virtual environment:

    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Unix
    source venv/bin/activate
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Initialize the database and run ingestion:

    ```bash
    # Runs the ingestion pipeline for all sources
    python ingest/run_ingest.py --all
    ```

    *Note: This will create a local DuckDB file `stabletrace.db`.*

5. Start the API server:

    ```bash
    uvicorn api.main:app --reload
    ```

    The API will be available at `http://127.0.0.1:8000`.

### Frontend Setup

1. Navigate to the app directory:

    ```bash
    cd app
    ```

2. Install dependencies:

    ```bash
    npm install
    ```

3. Run the development server:

    ```bash
    npm run dev
    ```

4. Open `http://localhost:3000` in your browser.

## Project Structure

- `/api`: FastAPI application and database logic.
- `/ingest`: Data collectors for DefiLlama, OFAC, etc.
- `/warehouse`: SQL schema definitions.
- `/app`: Next.js frontend application.

## License

MIT
