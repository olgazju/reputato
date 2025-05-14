FROM node:current-bookworm

# Install Playwright (browsers + system deps)
RUN npx -y playwright@^1.51.1 install --with-deps

# Install Python manually
RUN apt-get update && \
    apt-get install -y python3 python3-venv python3-pip build-essential && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/*

WORKDIR /app

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV NODE_ENV=production

RUN npm install -g @brightdata/mcp

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
