# Reputato

Not every job is golden. We sniff out the ones that are.

## What is Reputato?

Reputato is an OSINT (Open Source Intelligence) agent designed to help job seekers and professionals make informed decisions about potential employers. By aggregating and analyzing data from multiple sources including LinkedIn, Glassdoor, Crunchbase, and news articles, Reputato provides comprehensive insights into companies' reputation, work culture, financial health, and recent developments.

## Features

- **Multi-Source Data Collection**: Gathers information from LinkedIn, Glassdoor, Crunchbase, and news sources
- **Real-time Analysis**: Uses Bright Data's infrastructure to access and process current information
- **Comprehensive Insights**: Provides a holistic view of companies through various data points
- **User-Friendly Interface**: Easy-to-use web interface for accessing company information

## Prerequisites

- Python 3.12+ (managed via pyenv)
- Bright Data account with API access
- OpenAI API key

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

6. **Configure environment variables**:
   Create a `.env` file in the project root with the following variables:
   ```
   BRIGHTDATA_API_TOKEN=your_brightdata_token
   OPENAI_API_KEY=your_openai_key
   BRIGHTDATA_LINKEDIN_UNLOCKER_ZONE=your_linkedin_zone
   BRIGHTDATA_GLASSDOOR_UNLOCKER_ZONE=your_glassdoor_zone
   BRIGHTDATA_CRUNCHBASE_UNLOCKER_ZONE=your_crunchbase_zone
   BRIGHTDATA_NEWS_UNLOCKER_ZONE=your_news_zone
   BROWSER_AUTH_LINKEDIN=your_linkedin_auth
   BROWSER_AUTH_GLASSDOOR=your_glassdoor_auth
   BROWSER_AUTH_CRUNCHBASE=your_crunchbase_auth
   BROWSER_AUTH_NEWS=your_news_auth
   ```

## Running the Application

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
├── frontend/
│   ├── app.py
│   └── requirements.txt
├── .env
└── README.md
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the terms of the license included in the repository.
