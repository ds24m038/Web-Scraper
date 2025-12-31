# Azure Web Scraper

A Python-based web scraping pipeline that discovers URLs via Bing Search, scrapes web pages using Playwright, and uploads results to Azure Blob Storage with rich metadata.

---

## Features

- 🔍 **URL Discovery** - Find relevant pages using Bing Web Search API
- 🌐 **Recursive Scraping** - Follow links across multiple tiers with configurable depth
- 📄 **PDF Export** - Save complete page renders as PDF files
- 📥 **Auto Download** - Detect and save linked files (PDFs, documents, etc.)
- 🌳 **Hierarchy Tracking** - Preserve parent-child relationships between pages
- ☁️ **Azure Upload** - Automatically upload results to Azure Blob Storage

---

## Pipeline Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────┐     ┌──────────────┐
│  Bing Search    │ ──▶ │  Web Scraping    │ ──▶ │  Local Output  │ ──▶ │  Azure Blob  │
│  (Optional)     │     │  (Playwright)    │     │  (PDFs + JSON) │     │  Storage     │
└─────────────────┘     └──────────────────┘     └────────────────┘     └──────────────┘
```

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Environment

Create a `.env` file:

```env
# Required for Azure upload
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...

# Optional: customize container name (default: 'webscraper')
AZURE_CONTAINER_NAME=my-container

# Required only if using Bing Search (useSearch=True)
BING_SEARCH_SUBSCRIPTION_KEY=your_key_here
```

### 3. Configure Scraping Parameters

Edit `main.py`:

```python
# URLs to scrape directly
topLevelURLs = ['https://example.com/']

# Or use Bing Search to discover URLs
useSearch = True
keywords = 'topic1,topic2,topic3'

# Scraping limits
tierLimit = 2           # Max link depth (0 = top URL only)
scrapingLimit = 50      # Max pages per top-level URL
totalScrapingLimit = 500 # Max pages across all URLs
domainLimit = True      # Stay within same domain

# Search settings
searchLimit = 30        # Results per search term
```

### 4. Run

```bash
python main.py
```

---

## Output Structure

```
output/
└── DDMMYYYY-HHMMSS/            # Timestamped session folder
    ├── metadata.json           # Hierarchical scraping data
    └── <domain>/               # Folder per domain
        ├── abc123def456.pdf    # Scraped pages (hash ID filenames)
        └── downloads/          # Downloaded files
            └── xyz789_report.pdf
```

### Metadata Schema

Each scraped item includes:

| Field | Description |
|-------|-------------|
| `ID` | Unique hash (SHA256 + Base64) |
| `TIMESTAMP` | Unix timestamp of scraping |
| `TYPE` | `page` or `download` |
| `URL` | Source URL |
| `TIER` | Link depth (0 = top-level) |
| `TITLE` | Page title or filename |
| `PARENT` | URL where this link was found |
| `CHILDREN` | Nested array of child pages |

---

## File Reference

### `main.py`

**Entry point** - Configure parameters and run the pipeline.

| Parameter | Type | Description |
|-----------|------|-------------|
| `topLevelURLs` | `list[str]` | Starting URLs for scraping |
| `keywords` | `str` | Comma-separated search terms |
| `useSearch` | `bool` | Use Bing to discover URLs |
| `tierLimit` | `int` | Max link depth to follow |
| `scrapingLimit` | `int` | Max pages per domain |
| `totalScrapingLimit` | `int` | Max pages total |
| `domainLimit` | `bool` | Restrict to same domain |
| `searchLimit` | `int` | Results per search term |

---

### `search.py`

**URL discovery** using Bing Web Search API.

| Function | Description |
|----------|-------------|
| `__init__()` | Loads `BING_SEARCH_SUBSCRIPTION_KEY` from `.env` |
| `searchTermExtractor()` | Splits keywords by comma (placeholder for LLM enhancement) |
| `search()` | Queries Bing API, returns list of URLs |
| `runSearch()` | Orchestrates search across all keywords |

---

### `scraper.py`

**Core scraping engine** using Playwright.

| Function | Description |
|----------|-------------|
| `__init__()` | Initializes limits, queues, output directory |
| `runScraper()` | Main entry - processes all top-level URLs |
| `scrapePages()` | Creates browser, manages concurrent tasks (max 10) |
| `scrapePage()` | Scrapes single page: extracts links, saves as PDF |
| `checkURL()` | Validates URLs against exclusion rules |
| `saveMetadata()` | Builds hierarchical metadata structure |
| `generateHash()` | Creates unique IDs using SHA256 + Base64 |

**Exclusions:** Social media domains are automatically skipped:
- LinkedIn, YouTube, Twitter/X, Facebook, Bluesky

---

### `blob.py`

**Azure Blob Storage upload** with metadata.

| Function | Description |
|----------|-------------|
| `uploadToBlob()` | Iterates files, attaches metadata, uploads to Azure |
| `getMetadata()` | Finds metadata entry by file ID (recursive search) |
| `cleanMetadataText()` | Converts Unicode to ASCII for Azure compliance |

**Configuration via environment:**

| Variable | Required | Default |
|----------|----------|---------|
| `AZURE_STORAGE_CONNECTION_STRING` | Yes | - |
| `AZURE_CONTAINER_NAME` | No | `webscraper` |

---

### `requirements.txt`

| Package | Purpose |
|---------|---------|
| `playwright` | Browser automation |
| `azure-storage-blob` | Azure Blob Storage client |
| `azure-core` | Azure SDK core |
| `azure-identity` | Azure authentication |
| `microsoft-bing-websearch` | Bing Search API client |
| `python-dotenv` | Load `.env` files |
| `tldextract` | Parse domains from URLs |

---

## Azure Blob Storage Structure

After upload, files are organized as:

```
<container>/                    # Configurable via AZURE_CONTAINER_NAME
└── DDMMYYYY-HHMMSS/           # Session timestamp
    └── <domain>/
        ├── abc123.pdf
        └── downloads/
            └── xyz789_file.pdf
```

Each blob includes metadata properties:
- `ID`, `TIMESTAMP`, `TYPE`, `URL`, `TIER`, `TITLE`, `PARENT`

---

## Example Use Case

**Scraping research papers from Oxford Energy Institute:**

```python
topLevelURLs = ['https://www.oxfordenergy.org/publication-topic/papers/']
tierLimit = 2         # Follow links to PDFs
scrapingLimit = 100   # Get up to 100 items
domainLimit = True    # Stay on oxfordenergy.org
useSearch = False     # Start from known URL
```

This will:
1. Scrape the publications listing page
2. Follow links to individual paper pages
3. Download linked PDF files
4. Upload everything to Azure with metadata

---

## License

See [LICENSE](LICENSE) for details.