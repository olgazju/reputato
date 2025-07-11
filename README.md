# Reputato

Not every company is golden. We sniff out the ones that are.

## What is Reputato?

Reputato is an OSINT (Open Source Intelligence) agent designed to help job seekers and professionals make informed decisions about potential employers. By aggregating and analyzing data from multiple sources including LinkedIn, Glassdoor, Crunchbase, and news articles, Reputato provides comprehensive insights into companies' reputation, work culture, financial health, and recent developments.

Original post on [dev.to](https://dev.to/olgabraginskaya/reputato-not-every-company-is-golden-we-sniff-out-the-ones-that-are-3daa)

https://github.com/user-attachments/assets/273d23ec-ad58-4c24-b33a-be4ff3699571


Screenshots of summaries:


<img width="728" alt="image" src="https://github.com/user-attachments/assets/fdf4351b-1013-43cb-bb7f-c02bc4479fa2" />


<img width="764" alt="image" src="https://github.com/user-attachments/assets/5f7a9112-7f7a-40e2-9fd4-fbf6a0ca2382" />


## Features

- **Multi-Source Data Collection**: Gathers information from LinkedIn, Glassdoor, Crunchbase, and news sources
- **Real-time Analysis**: Uses Bright Data's MCP server to retrieve and process scraping data from various sources
- **Comprehensive Insights**: Provides a holistic view of companies through various data points
- **User-Friendly Interface**: Easy-to-use web interface for accessing company information

## Technology Stack

The backend is built as a FastAPI service that leverages PydanticAI for intelligent agent orchestration. PydanticAI provides a robust framework for building production-grade AI applications with structured data validation and type safety. The system uses OpenAI's models for natural language processing and data analysis. You can configure the model in the environment variables, but by default, it uses GPT-4 for optimal performance.

> **Note**: While Docker and Docker Compose configurations are available, there was a known issue with browser tools in Docker containers. This has been resolved by implementing the solution from [Bright Data MCP issue #11](https://github.com/luminati-io/brightdata-mcp/issues/11#issuecomment-2889967823): launching the MCP server once at app start-up and keeping it alive across requests, while closing (or timing-out) the browser only after the final multi-step tool call.

## Prerequisites

- Python 3.12+ (managed via pyenv)
- Bright Data account with API access
- OpenAI API key

## Configuration

### Backend Configuration (.env)

Create a `.env` file in the backend directory with the following variables:

```env
# API Keys
BRIGHTDATA_API_TOKEN=your_brightdata_token
OPENAI_API_KEY=your_openai_key
REPUTATO_API_KEY=your_own_generated_api_key

# URLs
FRONTEND_URL=http://localhost:8501

# Bright Data Zones
BRIGHTDATA_LINKEDIN_UNLOCKER_ZONE=your_linkedin_zone
BRIGHTDATA_GLASSDOOR_UNLOCKER_ZONE=your_glassdoor_zone
BRIGHTDATA_CRUNCHBASE_UNLOCKER_ZONE=your_crunchbase_zone
BRIGHTDATA_NEWS_UNLOCKER_ZONE=your_news_zone

# Browser Authentication
BROWSER_AUTH_LINKEDIN=your_linkedin_auth
BROWSER_AUTH_GLASSDOOR=your_glassdoor_auth
BROWSER_AUTH_CRUNCHBASE=your_crunchbase_auth
BROWSER_AUTH_NEWS=your_news_auth

# Optional: Logging Configuration
LOGFIRE_TOKEN=your_logfire_token  # Add this to enable logging through Logfire
```

### Frontend Configuration (Streamlit)

Create a `.streamlit/secrets.toml` file in the frontend directory with the following configuration:

```toml
[backend]
url = "http://localhost:8000"
apikey = "your_own_generated_api_key"
```

## Local Development Setup

1. **Install pyenv** (if not already installed):
   ```bash
   # macOS
   brew install pyenv

   # Linux
   curl https://pyenv.run | bash
   ```

2. **Set up Python environment**:
   ```bash
   brew update && brew upgrade pyenv
   pyenv install 3.12.2
   pyenv virtualenv 3.12.2 reputato
   pyenv local reputato
   ```

3. **Set up pre-commit hooks**:
   ```bash
   # Install pre-commit
   pip install pre-commit

   # Install the git hook scripts
   pre-commit install

   # Run pre-commit on all files
   pre-commit run --all-files
   ```

4. **Set up Bright Data MCP Server**:
   - Follow the instructions at [Bright Data MCP Server Documentation](https://docs.brightdata.com/api-reference/MCP-Server)
   - Create necessary zones for LinkedIn, Glassdoor, Crunchbase, and News

5. **Install dependencies**:
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt

   # Frontend
   cd ../frontend
   pip install -r requirements.txt
   ```

## Running the Application

You can run the application either using Docker or locally:

### Using Docker

1. **Build and run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

### Local Development

1. **Start the backend server**:
   ```bash
   cd backend
   python run.py
   ```

2. **Start the frontend**:
   ```bash
   cd frontend
   streamlit run app.py
   ```

3. Access the application at `http://localhost:8501`

## Project Structure

```
reputato/
├── backend/
│   ├── app/
│   ├── requirements.txt
│   └── run.py
│   └── .env
├── frontend/
│   ├── app.py
│   └── requirements.txt
│   └── .streamlit/secrets.toml
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the terms of the license included in the repository.
