# app.py - Your Secure Backend with RAG Integration
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import pandas as pd
import numpy as np
import json

# Import RAG functions from simplified version
from rag_simple import interpret_query_simple, fetch_and_answer, supabase, TABLES, generate_chart_data

load_dotenv() # This loads the .env file

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') # Safely gets key from .env
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

# Serve static files
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

# RAG endpoint for natural language queries
@app.route('/api/rag-query', methods=['POST'])
def rag_query():
    try:
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        # Use simplified RAG to interpret and fetch data
        decision = interpret_query_simple(query)
        table, cols = decision.get("table"), decision.get("columns", [])
        
        if not table or table not in TABLES:
            return jsonify({
                'error': "Sorry, I can't answer that request with the current database.",
                'suggested_tables': TABLES
            }), 400
        
        # Fetch data from Supabase
        response = supabase.table(table).select("*").limit(1000).execute()
        if not response.data:
            return jsonify({'error': f'No data in table {table}'}), 400
        
        df = pd.DataFrame(response.data)
        query_lower = query.lower()
        
        # Handle different types of queries
        result = process_query(df, query_lower, table, cols)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'RAG query failed: {str(e)}'}), 500

# Get table data endpoint
@app.route('/api/table/<table_name>', methods=['GET'])
def get_table_data(table_name):
    try:
        if table_name not in TABLES:
            return jsonify({'error': 'Invalid table name'}), 400
        
        response = supabase.table(table_name).select("*").limit(1000).execute()
        if not response.data:
            return jsonify({'error': f'No data in table {table_name}'}), 400
        
        df = pd.DataFrame(response.data)
        
        return jsonify({
            'table': table_name,
            'data': df.to_dict(orient='records'),
            'columns': df.columns.tolist(),
            'count': len(df)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch table data: {str(e)}'}), 500

# Get available tables
@app.route('/api/tables', methods=['GET'])
def get_tables():
    return jsonify({'tables': TABLES})

# Your frontend will send requests to this new endpoint
@app.route('/api/agent', methods=['POST'])
def agent_proxy():
    # Get the request data from your frontend
    frontend_data = request.json
    
    # Make the secure request to the REAL Gemini API from your server
    response = requests.post(GEMINI_API_URL, json=frontend_data)
    
    # Send the response from Gemini back to your frontend
    return jsonify(response.json())


def process_query(df, query_lower, table, cols):
    """Process different types of queries and return appropriate responses"""
    
    # Handle counts
    if "number of" in query_lower or "count" in query_lower:
        if "completed" in query_lower and "order_status" in df.columns:
            count_val = df[df["order_status"].str.lower() == "completed"].shape[0]
        elif "education verification" in query_lower and "subject_id" in df.columns:
            count_val = df.shape[0]
        else:
            count_val = len(df)
        return {
            'type': 'count',
            'value': count_val,
            'message': f'There are {count_val} records'
        }
    
    # Handle unique values
    if "unique" in query_lower:
        col = cols[0] if cols else df.columns[0]
        unique_vals = df[col].drop_duplicates().tolist()
        return {
            'type': 'unique',
            'column': col,
            'values': unique_vals,
            'message': f'Unique values in {col}: {unique_vals}'
        }
    
    # Handle chart generation requests
    if any(keyword in query_lower for keyword in ["chart", "graph", "plot", "bar", "line", "visualization"]):
        chart_type = "bar"  # default
        if "line" in query_lower:
            chart_type = "line"
        elif "bar" in query_lower:
            chart_type = "bar"
        elif "pie" in query_lower:
            chart_type = "pie"
        
        # Determine what to chart
        if cols:
            chart_column = cols[0]
        else:
            # Find the best column to chart
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            
            if chart_type == "line" and numeric_cols:
                chart_column = numeric_cols[0]
            elif categorical_cols:
                chart_column = categorical_cols[0]
            else:
                chart_column = df.columns[0]
        
        chart_data = generate_chart_data(df, chart_column, chart_type, table)
        
        # Handle error responses from chart generation
        if chart_data.get('type') == 'error':
            return chart_data
            
        return chart_data
    
    # Handle distributions
    if "distribution" in query_lower:
        col = cols[0] if cols else df.columns[0]
        if pd.api.types.is_numeric_dtype(df[col]):
            # For numeric data, return histogram data
            hist_data = df[col].value_counts(bins=20).to_dict()
            return {
                'type': 'distribution',
                'column': col,
                'data': hist_data,
                'chart_type': 'histogram',
                'message': f'Distribution of {col}'
            }
        else:
            # For categorical data, return count data
            dist_data = df[col].value_counts().to_dict()
            return {
                'type': 'distribution',
                'column': col,
                'data': dist_data,
                'chart_type': 'bar',
                'message': f'Distribution of {col}'
            }
    
    # Handle time filters
    if "since yesterday" in query_lower:
        time_cols = [c for c in df.columns if "time" in c]
        if time_cols:
            from datetime import datetime, timedelta
            yesterday = datetime.now() - timedelta(days=1)
            filtered_df = df[pd.to_datetime(df[time_cols[0]]) >= yesterday]
            return {
                'type': 'time_filter',
                'count': filtered_df.shape[0],
                'message': f'Records since yesterday: {filtered_df.shape[0]}'
            }
    
    # Default: return sample data
    sample = df.head(10).to_dict(orient="records")
    return {
        'type': 'sample',
        'data': sample,
        'columns': df.columns.tolist(),
        'total_count': len(df),
        'message': f'Sample data from {table} table'
    }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)