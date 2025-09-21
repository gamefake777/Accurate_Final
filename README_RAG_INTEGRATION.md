# RAG Integration with Frontend

This document describes the integration of the RAG (Retrieval-Augmented Generation) system with the frontend interface.

## Overview

The integration connects the `rag.py` backend functionality with the web frontend, allowing users to query the database using natural language through a modern web interface.

## Architecture

```
Frontend (HTML/CSS/JS) 
    ↓ HTTP Requests
Flask Backend (app.py)
    ↓ Function Calls
RAG System (rag.py)
    ↓ Database Queries
Supabase Database
```

## Key Features

### 1. Natural Language Queries
- Users can ask questions in plain English
- The system interprets queries using ChromaDB embeddings
- Supports various query types: counts, distributions, unique values, time filters

### 2. Real-time Database Access
- Direct connection to Supabase database
- Dynamic table loading and data fetching
- Real-time query processing

### 3. Interactive Dashboard
- Table browser with clickable table buttons
- Voice recognition support
- Responsive design with modern UI

## API Endpoints

### `/api/rag-query` (POST)
Processes natural language queries using RAG system.

**Request:**
```json
{
  "query": "How many completed orders are there?"
}
```

**Response:**
```json
{
  "type": "count",
  "value": 150,
  "message": "There are 150 records"
}
```

### `/api/table/<table_name>` (GET)
Fetches data from a specific table.

**Response:**
```json
{
  "table": "order_request",
  "data": [...],
  "columns": ["order_id", "status", ...],
  "count": 1000
}
```

### `/api/tables` (GET)
Returns list of available tables.

**Response:**
```json
{
  "tables": ["order_request", "subject", "company", ...]
}
```

## Setup Instructions

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   Create a `.env` file with:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   OPENROUTER_API_KEY=your_openrouter_key
   GEMINI_API_KEY=your_gemini_key
   ```

3. **Start the Application:**
   ```bash
   python app.py
   ```

4. **Access the Interface:**
   Open http://localhost:5000 in your browser

## Query Types Supported

### Count Queries
- "How many records are there?"
- "Count completed orders"
- "Number of education verifications"

### Distribution Queries
- "Show distribution of order_status"
- "What's the distribution of package types?"

### Unique Value Queries
- "Show unique values in order_status"
- "What are the different companies?"

### Time-based Queries
- "Records since yesterday"
- "Orders from last week"

### Sample Data Queries
- "Show me sample data"
- "Display some records from order_request"

## Frontend Components

### Voice Recognition
- Wake word: "Hey Accurate"
- Natural language query processing
- Text-to-speech responses

### Dashboard
- Table selection interface
- Real-time data loading
- Interactive charts and visualizations

### Query Interface
- Search bar with autocomplete
- Quick filter buttons
- Real-time results display

## Error Handling

The system includes comprehensive error handling for:
- Database connection issues
- Invalid queries
- Missing data
- Network timeouts
- API failures

## Testing

Run the integration test:
```bash
python test_integration.py
```

This will verify:
- Server connectivity
- RAG query processing
- Table data access
- API endpoint functionality

## Troubleshooting

### Common Issues

1. **Server won't start:**
   - Check if port 5000 is available
   - Verify all dependencies are installed
   - Check .env file configuration

2. **Database connection fails:**
   - Verify Supabase credentials
   - Check network connectivity
   - Ensure database tables exist

3. **RAG queries not working:**
   - Check if ChromaDB is initialized
   - Verify embedding service is running
   - Check query format

4. **Frontend not loading:**
   - Ensure Flask is serving static files
   - Check browser console for errors
   - Verify CORS settings

## Future Enhancements

- Advanced chart types
- Query history
- Saved queries
- Export functionality
- Multi-language support
- Advanced filtering options
