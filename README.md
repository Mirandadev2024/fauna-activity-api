# Fauna Activity API

A REST API built with FastAPI to explore wildlife camera-trap records and visualize animal activity patterns from Excel data.

The project reads camera-trap records, filters observations by species, summarizes detections by hour of the day, and generates histogram and circular activity plots.

## Features

- Query camera-trap records by species.
- Summarize detections by hour of the day.
- Generate hourly histograms.
- Generate circular plots to visualize daily activity patterns.
- Access the API through automatically generated interactive documentation.
- Explore results through a simple HTML dashboard.

## Technologies

- Python
- FastAPI
- Uvicorn
- Pandas
- NumPy
- Matplotlib
- OpenPyXL
- Pytest

## Project structure

```text
fauna-activity-api/
├── main.py
├── test_main.py
├── requirements.txt
├── Procfile
├── .gitignore
├── README.md
└── registros_fauna.xlsx
```

The file `registros_fauna.xlsx` is intentionally omitted from the repository because it is expected to contain the user's own wildlife records.

You must create this Excel workbook and add three columns named `especie`, `data`, and `hora`, in this order. The species column should contain strings with scientific names. The date and time columns should follow the formats expected by the application (day-month-year and hour:minute:second, respectively). Column names and data formats must match those configured in `main.py`.

**Data privacy:** If you fork this project, do not publish precise camera locations, sensitive wildlife records, or restricted field data. Use an anonymized or demonstration dataset when necessary.

## Requirements

- Python 3.11 or another Python version compatible with the dependencies.
- Git.
- An Excel workbook formatted for the application.

## Installation

Clone the repository:

```bash
git clone https://github.com/Mirandadev2024/fauna-activity-api.git
cd fauna-activity-api
```

Create a virtual environment.

**Windows:**

```bash
py -m venv .venv
.venv\Scripts\activate
```

**Linux or macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

Place the required Excel workbook in the expected location (the project root directory), unless the application is configured to retrieve the data from another source.

## Running locally

Start the development server:

```bash
python -m uvicorn main:app --reload
```

Open the following addresses in your browser:

- API documentation: http://127.0.0.1:8000/docs
- Alternative documentation: http://127.0.0.1:8000/redoc
- HTML dashboard: http://127.0.0.1:8000/dashboard

The dashboard URL is available only if that route is implemented in `main.py`.

## Automated tests

The project uses **Pytest** to run automated tests and verify application functionality.

The test file is located in the project root:

```text
fauna-activity-api/
├── main.py
└── test_main.py
```

### Running tests locally

Install Pytest:

```bash
python -m pip install pytest
```

Run the tests:

```bash
python -m pytest -v
```

The `-v` option enables verbose output, displaying each test and its execution result.

### Continuous Integration (GitHub Actions)

The project uses **GitHub Actions** to automatically execute tests in a clean environment.

The workflow is configured in the GitHub repository under:

```text
.github/workflows/
```

It is triggered by:

- Push events to the `main` branch.
- Pull requests targeting the `main` branch.

The workflow performs the following steps:

1. Checks out the repository.
2. Sets up Python 3.11.
3. Installs project dependencies from `requirements.txt`.
4. Installs Pytest.
5. Runs the automated test suite using:

```bash
python -m pytest -v
```

This process helps detect regressions whenever changes are submitted to the main branch.

The current automated test suite includes a test for `carregar_dados()`, which verifies the data-loading functionality.

## API endpoints

The following endpoints describe the intended interface. Check `main.py` for the exact parameters and response formats.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/activity` | Retrieve activity summaries for a species |
| GET | `/activity.png` | Generate an activity plot |
| POST | `/activity` | Submit a structured activity query |
| GET | `/dashboard` | Open the HTML dashboard |
| GET | `/docs` | Explore and test the API |

### Example requests

Retrieve the activity summary for *Dasyprocta azarae*:

```http
GET /activity?especie=Dasyprocta%20azarae
```

Generate a circular plot:

```http
GET /activity.png?especie=Species%20name&tipo=circular
```

Generate a histogram:

```http
GET /activity.png?especie=Species%20name&tipo=histograma
```

These examples assume the corresponding routes and parameter names are implemented as shown.

## Deployment

The application can be deployed to a Python-compatible hosting platform such as Heroku.

The root directory should include a `requirements.txt` file and a `Procfile` containing:

```text
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

After configuring the application and authenticating with the Heroku CLI, deploy the main branch with:

```bash
git push heroku main
```

The Excel workbook must also be accessible to the deployed application. Do not rely on the dyno's local filesystem for persistent storage.

## Scientific interpretation

Camera-trap detections describe observed activity at sampled locations rather than directly measuring population abundance or the full activity of individual animals.

Interpretation should consider sampling effort, camera placement, repeated detections, temporal coverage, and the definition of independent events.

Circular plots are useful for representing the daily cycle, while histograms make hourly detection frequencies easier to compare.

## Future improvements

- Validate and standardize input data.
- Add sampling-effort summaries.
- Export figures and summary tables.
- Expand automated test coverage.
- Improve data storage and deployment configuration.

## Author

**Francisco Ferreira de Miranda Santos**

Biologist interested in ecology, biodiversity monitoring, and scientific data analysis.

GitHub: https://github.com/Mirandadev2024

---

This project is intended as a learning and research tool for exploring wildlife camera-trap data.