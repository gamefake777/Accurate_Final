# Accurate Background Verification System

A comprehensive background verification platform with RAG (Retrieval-Augmented Generation) integration, featuring natural language querying capabilities and real-time data analytics.

## 🚀 Features

- **Natural Language Queries**: Ask questions about your data in plain English
- **Real-time Database Access**: Direct connection to Supabase database
- **Interactive Dashboard**: Modern web interface with voice recognition
- **Data Visualization**: Dynamic charts and graphs for data insights
- **Multi-table Support**: Access to order requests, subjects, companies, packages, and more
- **Voice Interface**: "Hey Accurate" wake word for hands-free operation
- **RESTful API**: Complete API endpoints for data access and querying

## 📋 Prerequisites

Before setting up the application, ensure you have:

- Python 3.8 or higher
- pip (Python package installer)
- A Supabase account and project
- Google Gemini API key
- OpenRouter API key 

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd accuratee-main/Accurate
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root directory with the following variables:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# API Keys
GEMINI_API_KEY=your_google_gemini_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

**Important**: Replace the placeholder values with your actual API keys and Supabase credentials.

## 🗄️ Database Setup

### Supabase Configuration

1. **Create a Supabase Project**:
   - Go to [supabase.com](https://supabase.com)
   - Create a new project
   - Note down your project URL and anon key

2. **Database Tables**:
   The system expects the following tables in your Supabase database:

   - `order_request`: Order management data
   - `subject`: Subject/person information
   - `company`: Company details
   - `package`: Package information
   - `search_status`: Search status codes
   - `search_type`: Search type definitions

3. **Table Schema**:
   Ensure your tables have the expected columns as defined in the `rag_simple.py` file.

## 🚀 Running the Application

### 1. Start the Backend Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

### 2. Access the Web Interface

Open your web browser and navigate to:
```
http://localhost:5000
```

### 3. Verify Installation

Run the integration test to ensure everything is working:

```bash
python test_integration.py
```

## 📖 Usage Guide

### Web Interface

1. **Main Dashboard**: 
   - Use the search bar to ask natural language questions
   - Click on quick filter buttons for common queries
   - Use the microphone icon for voice input

2. **Database Tables Dashboard**:
   - Click "Dashboard" to access table browser
   - Select any table to view its data
   - Use "Back to Main" to return to the search interface

### Natural Language Queries

The system supports various types of queries:

#### Count Queries
- "How many records are there?"
- "Count completed orders"
- "Number of education verifications"

#### Distribution Queries
- "Show distribution of order_status"
- "What's the distribution of package types?"

#### Unique Value Queries
- "Show unique values in order_status"
- "What are the different companies?"

#### Chart Generation
- "Create a bar chart of order_status"
- "Show me a pie chart of package types"
- "Generate a line chart of order trends"

#### Time-based Queries
- "Records since yesterday"
- "Orders from last week"

### API Endpoints

#### Query Data
```http
POST /api/rag-query
Content-Type: application/json

{
  "query": "How many completed orders are there?"
}
```

#### Get Table Data
```http
GET /api/table/{table_name}
```

#### List Available Tables
```http
GET /api/tables
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Your Supabase project URL | Yes |
| `SUPABASE_KEY` | Your Supabase anonymous key | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `OPENROUTER_API_KEY` | OpenRouter API key | Optional |

### Database Configuration

The system automatically connects to your Supabase database using the provided credentials. Ensure your database has the required tables and proper permissions.

## 🧪 Testing

### Run Integration Tests

```bash
python test_integration.py
```

This will test:
- Server connectivity
- RAG query processing
- Table data access
- API endpoint functionality

### Manual Testing

1. Start the application
2. Open the web interface
3. Try various natural language queries
4. Test the dashboard functionality
5. Verify chart generation

## 🐛 Troubleshooting

### Common Issues

#### Server Won't Start
- **Port 5000 in use**: Change the port in `app.py` or kill the process using port 5000
- **Missing dependencies**: Run `pip install -r requirements.txt`
- **Environment variables**: Check your `.env` file configuration

#### Database Connection Fails
- **Invalid credentials**: Verify your Supabase URL and key
- **Network issues**: Check your internet connection
- **Table permissions**: Ensure your Supabase key has read access to tables

#### RAG Queries Not Working
- **Empty database**: Ensure your tables have data
- **Invalid queries**: Try simpler queries first
- **API limits**: Check your API key usage limits

#### Frontend Not Loading
- **Static files**: Ensure Flask is serving static files correctly
- **Browser console**: Check for JavaScript errors
- **CORS issues**: Verify CORS is enabled in the Flask app

### Getting Help

1. Check the console output for error messages
2. Verify all environment variables are set correctly
3. Ensure all dependencies are installed
4. Check your Supabase project status
5. Review the API key permissions

## 📁 Project Structure

```
Accurate/
├── app.py                 # Main Flask application
├── rag_simple.py         # RAG query processing
├── index.html            # Web interface
├── style.css             # Styling
├── script.js             # Frontend JavaScript
├── requirements.txt      # Python dependencies
├── test_integration.py   # Integration tests
├── charts/               # Generated chart files
├── chroma_db/           # ChromaDB storage
└── README.md            # This file
```

## 🔒 Security Notes

- Never commit your `.env` file to version control
- Use environment variables for all sensitive data
- Regularly rotate your API keys
- Implement proper authentication for production use
- Use HTTPS in production environments

## 🚀 Deployment

### Production Considerations

1. **Environment Variables**: Use secure environment variable management
2. **Database Security**: Implement proper database access controls
3. **API Rate Limiting**: Add rate limiting to prevent abuse
4. **HTTPS**: Use SSL certificates for secure communication
5. **Monitoring**: Implement logging and monitoring
6. **Backup**: Regular database backups

### Docker Deployment (Optional)

Create a `Dockerfile` for containerized deployment:

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

## 📈 Performance Optimization

- **Database Indexing**: Add indexes to frequently queried columns
- **Caching**: Implement Redis caching for frequently accessed data
- **Query Optimization**: Optimize database queries
- **CDN**: Use CDN for static assets
- **Load Balancing**: Implement load balancing for high traffic

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- Check the troubleshooting section
- Review the integration test output
- Check the console logs for error messages
- Ensure all prerequisites are met

## 🔄 Updates

To update the application:
1. Pull the latest changes
2. Update dependencies: `pip install -r requirements.txt`
3. Restart the application
4. Run integration tests

---

**Note**: This application is designed for background verification data management. Ensure compliance with data protection regulations in your jurisdiction.
