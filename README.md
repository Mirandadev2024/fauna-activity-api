Fauna Activity API



A REST API built with FastAPI to explore wildlife camera-trap records and visualize animal activity patterns from Excel data.



The project reads camera-trap records, filters observations by species, summarizes detections by hour of the day, and generates histogram and circular activity plots.



Features



Query camera-trap records by species.



Summarize detections by hour of the day.



Generate hourly histograms.



Generate circular plots to visualize daily activity patterns.



Access the API through automatically generated interactive documentation.



Explore results through a simple HTML dashboard.



Technologies



Python



FastAPI



Uvicorn



Pandas



NumPy



Matplotlib



OpenPyXL



Project structure



fauna\_api/

├── main.py

├── requirements.txt

├── Procfile

├── .gitignore

├── README.md

└── registros\_fauna.xlsx



The file registros fauna.xlsx was omitted, as this file is intended to have your personal fauna records data. You will have to manually create this file and add three columns named espécie, data and hora (in this order). The columns especie is intended to be read as a string, as it contains the species name. The columns data and hora are intended to have the date and hour of the day, respectively, in the following formats: xx-xx-xxx (day, month and year) and xx-xx-xx (hour, minutes, seconds). The application is configured to match the actual column names and data formats.



Data privacy: if you wish to fork this project, do not publish precise camera locations, sensitive wildlife records, or restricted field data. Use an anonymized or demonstration dataset when necessary.



Requirements



Python 3.11 or another Python version compatible with the dependencies.



Git.



An Excel workbook formatted for the application.



Installation



Clone the repository:



git clone https://github.com/Mirandadev2024/fauna-activity-api.git

cd fauna-activity-api



Create a virtual environment.



On Windows:



py -m venv .venv

.venv\\Scripts\\activate



On Linux or macOS:



python3 -m venv .venv

source .venv/bin/activate



Install the dependencies:



python -m pip install -r requirements.txt



Place the required Excel workbook in the expected location (the home directory), unless the application is configured to retrieve the data from another source.



Run locally



Start the development server:



python -m uvicorn main:app --reload



Open the following addresses in your browser:



API documentation: http://127.0.0.1:8000/docs



Alternative documentation: http://127.0.0.1:8000/redoc



HTML dashboard: http://127.0.0.1:8000/dashboard



The dashboard URL is available only if that route is implemented in main.py.



API endpoints



The following endpoints describe the intended interface. Check main.py for the exact parameters and response formats.



Method



Endpoint



Purpose



GET



/activity



Retrieve activity summaries for a species



GET



/activity.png



Generate an activity plot



POST



/activity



Submit a structured activity query



GET



/dashboard



Open the HTML dashboard



GET



/docs



Explore and test the API



Example request



Retrieve the activity summary for Dasyprocta azarae:



GET /activity?especie=Dasyprocta%20azarae



Generate a circular plot:



GET /activity.png?especie=Species%20namee\&tipo=circular



Generate a histogram:



GET /activity.png?especie=Species%20name\&tipo=histograma



These examples assume the corresponding routes and parameter names are implemented as shown.



Deployment



The application can be deployed to a Python-compatible hosting platform such as Heroku.



The root directory should include a requirements.txt file and a Procfile containing:



web: uvicorn main:app --host 0.0.0.0 --port $PORT



After configuring the application and authenticating with the Heroku CLI, deploy the main branch with:



git push heroku main



The Excel workbook must also be accessible to the deployed application. Do not rely on the dyno's local filesystem for persistent storage.



Scientific interpretation



Camera-trap detections describe observed activity at sampled locations rather than directly measuring population abundance or the full activity of individual animals.



Interpretation should consider sampling effort, camera placement, repeated detections, temporal coverage, and the definition of independent events.



Circular plots are useful for representing the daily cycle, while histograms make hourly detection frequencies easier to compare.



Future improvements



Validate and standardize input data.



Add sampling-effort summaries.



Export figures and summary tables.



Add automated tests.



Improve data storage and deployment configuration.



Author



Francisco Ferreira de Miranda Santos



Biologist interested in ecology, biodiversity monitoring, and scientific data analysis.



GitHub: https://github.com/Mirandadev2024



This project is intended as a learning and research tool for exploring wildlife camera-trap data.

