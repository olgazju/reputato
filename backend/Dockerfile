# Start with Node base image that has debian bookworm (for stability)
FROM node:current-bookworm

# Install Playwright (browsers + system deps)
RUN npx -y playwright@^1.51.1 install --with-deps

# Install Python manually
RUN apt-get update && \
    apt-get install -y python3 python3-venv python3-pip build-essential && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/*

# Set working directory
WORKDIR /app

# Create and activate virtualenv
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set Node.js environment variables
#ENV NODE_OPTIONS="--max-old-space-size=4096"
ENV NODE_ENV=production

# Install Bright Data MCP
RUN npm install -g @brightdata/mcp

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy rest of app
COPY . .

# Expose port
EXPOSE 8000

# Run app
CMD ["uvicorn", "app.lmain:app", "--host", "0.0.0.0", "--port", "8000"]
