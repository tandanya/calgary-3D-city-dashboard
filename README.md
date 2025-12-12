# Calgary 3D City Dashboard

A web-based visualization of Calgary buildings using the Property Assessments Values data set. Buildings can be clicked, inspected, and using natural language queries, highlighted using a desired filter. 

![Dashboard Preview](docs/city-demo.gif)
## Features
- **3D Visualization**: Buildings rendered in Three.js based on City of Calgary's *Current Year Property Assessments* dataset. 
- **AI-Powered Queries**: Natural language queries to visually filter buildings using Hugging Face LLM
- **Interactive Data**: Click buildings to view detailed information (Type, Assessed value, Zoning, etc.)
- **Color-Coded Properties**: For viewing comfort, there's visual distinction between Commercial, Residential and Industrial buildings.

## Known Issues
- The data set used is a *property value* dataset, so it does not provide *building* details but rather the details about the property itself like value and zoning. Because of this, the height is assigned based on value, and evenly distributed from highest to lowest value in the current building cache. 
- The scale used to draw buildings could use some fine tuning. Currently, because we do not pull data from a small specific area but rather try to gather a variety of different buildings (in order to demonstrate functionality), the buildings are not orderly drawn and often overlap. 
	- This can be fixed by creating a more specific dataset (eg. merging diff datasets) and fine tuning the scale of buildings to it. 

## Tech Stack
- **Frontend**: React, Three.js (@react-three/fiber), Vite
- **Backend**: Python, Flask
- **AI**: Hugging Face Inference API (Mistral-7B)
- **Data**: City of Calgary's *Current Year Property Assessments* dataset.
## Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- Hugging Face API key (free at [huggingface.co](https://huggingface.co))

  

## Setup Instructions

  

### 1. Clone and Setup Backend


```bash
cd backend
# Create virtual environment
python -m venv venv
source venv/bin/activate  
# On Windows the path is venv\Scripts\activate
# Install dependencies
pip install -r requirements.txt
# Create .env file
echo "HUGGINGFACE_API_KEY=your_api_key_here" > .env
```


### 2. Get Hugging Face API Key

1. Go to [huggingface.co](https://huggingface.co)
2. Sign up for a free account
3. Navigate to Settings -> Access Tokens
4. Create a new token with "read" permissions
5. Copy the token to your .env file


### 3. Setup Frontend

bash

```bash
cd frontend

# Install dependencies
npm install

# Create environment file (optional, for production)
echo "VITE_API_URL=http://localhost:5000/api" > .env
```

### 4. Run the Application

**Terminal 1 - Backend:**

bash

```bash
cd backend
source venv/bin/activate
python app.py
```

**Terminal 2 - Frontend:**

bash

```bash
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

## Usage

### Viewing Buildings

- **Rotate**: Left-click and drag
- **Zoom**: Scroll wheel
- **Pan**: Right-click and drag
- **Select**: Click on any building to view details

### Querying with Natural Language

Type queries in the search box:

- "Show buildings over 100 feet"
- "Highlight commercial buildings"
- "Find buildings worth less than $500,000"
- "Show buildings in RC-G zoning"
- "Display residential properties"

## Project Structure

text

```text
├── backend/
│   ├── app.py              # flask and api application 
│   ├── data_fetcher.py     # dataset fetcher
│   ├── llm_handler.py      # llm intergration
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx    # main dashboard container
│   │   │   ├── CityScene.jsx    # three.js 3d scene
│   │   │   ├── QueryInput.jsx   # NL query window
│   │   │   └── BuildingPopup.jsx # building details popup
│   │   ├── App.jsx
│   │   └── index.css
│   └── package.json
├── docs/
│   └── uml-diagram.png
└── README.md
```

## To run
```bash

# backend terminal
cd backend
source venv/bin/activate
# windows: source venv/Scripts/activate
python app.py

# in a frontend terminal
cd frontend
npm run dev
```
Open http://localhost:5173 in your browser.
