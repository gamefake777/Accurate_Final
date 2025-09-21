# ===============================  
# 1. Load Environment Variables
# ===============================
import os
import requests
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from supabase import create_client
from datetime import datetime, timedelta
import json

# Ensure kaleido is installed
try:
    import kaleido
except ImportError:
    print("⚠️ Please install kaleido: pip install kaleido")

os.makedirs("charts", exist_ok=True)
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or not OPENROUTER_API_KEY:
    raise ValueError("⚠️ Please set SUPABASE_URL, SUPABASE_KEY, and OPENROUTER_API_KEY in .env")

# ===============================  
# 2. Connect to Supabase
# ===============================
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===============================  
# 3. Schema Snapshot
# ===============================
SCHEMA = {
    "order_request": ["order_id", "orderpackageid", "ordersubjectid", "ordercompanycode",
                      "order_status", "order_packagecode", "order_request_time", "order_received_time"],
    "search_status": ["status_code", "status"],
    "search_type": ["search_type_code", "search_type", "search_type_category"],
    "subject": ["subject_id", "subject_name", "subject_alias", "subject_contact",
                "subject_address1", "subject_address2", "sbj_city"],
    "package": ["package_code", "package_name", "package_price", "comp_code"],
    "company": ["comp_id", "comp_name", "comp_code"]
}
TABLES = list(SCHEMA.keys())

# ===============================  
# 4. Simple Query Interpreter (No ChromaDB)
# ===============================
def interpret_query_simple(user_query: str):
    """Simple keyword-based query interpretation"""
    query_lower = user_query.lower()
    
    # Map keywords to tables
    table_keywords = {
        "order": "order_request",
        "request": "order_request", 
        "orders": "order_request",
        "subject": "subject",
        "subjects": "subject",
        "person": "subject",
        "people": "subject",
        "company": "company",
        "companies": "company",
        "package": "package",
        "packages": "package",
        "search": "search_status",
        "status": "search_status",
        "type": "search_type"
    }
    
    # Find the best matching table
    best_table = None
    best_score = 0
    
    for keyword, table in table_keywords.items():
        if keyword in query_lower:
            best_table = table
            best_score += 1
    
    # If no specific table found, default to order_request
    if not best_table:
        best_table = "order_request"
    
    # Map keywords to columns
    column_keywords = {
        "status": "order_status",
        "completed": "order_status",
        "pending": "order_status",
        "name": "subject_name",
        "company": "comp_name",
        "package": "package_name",
        "price": "package_price",
        "time": "order_request_time",
        "date": "order_request_time"
    }
    
    relevant_columns = []
    for keyword, column in column_keywords.items():
        if keyword in query_lower:
            relevant_columns.append(column)
    
    return {"table": best_table, "columns": relevant_columns}

# ===============================  
# 5. Chart Generation Functions
# ===============================
def generate_chart_data(df, column, chart_type, table_name):
    """Generate chart data for frontend display with validation and insights"""
    
    # Check if column is numerical
    is_numeric = pd.api.types.is_numeric_dtype(df[column])
    original_chart_type = chart_type
    
    # For line charts, we prefer numerical data but can work with categorical
    if chart_type == "line" and not is_numeric:
        # Convert categorical to numerical for line chart (count-based)
        chart_type = "bar"  # Fallback to bar chart for categorical data
        print(f"Note: Converting line chart to bar chart for categorical column '{column}'")
    
    # Generate insights about the data
    insights = generate_data_insights(df, column, chart_type, original_chart_type)
    
    if chart_type == "line":
        if is_numeric:
            # For numerical data, create line chart with proper sorting
            data = df[column].value_counts().sort_index()
            labels = [str(x) for x in data.index.tolist()]
            values = data.values.tolist()
        else:
            # Fallback to bar chart for categorical data
            data = df[column].value_counts()
            labels = data.index.tolist()
            values = data.values.tolist()
            chart_type = "bar"  # Override to bar chart
    
    elif chart_type == "bar":
        if is_numeric:
            # For numerical data, create histogram-like bar chart
            data = df[column].value_counts().sort_index()
            labels = [str(x) for x in data.index.tolist()]
            values = data.values.tolist()
        else:
            # For categorical data, count occurrences and sort by frequency
            data = df[column].value_counts().sort_values(ascending=False)
            labels = data.index.tolist()
            values = data.values.tolist()
    
    elif chart_type == "pie":
        # Pie chart - count occurrences (works for both numerical and categorical)
        data = df[column].value_counts()
        labels = data.index.tolist()
        values = data.values.tolist()
    
    else:
        # Default to bar chart
        data = df[column].value_counts()
        labels = data.index.tolist()
        values = data.values.tolist()
        chart_type = "bar"
    
    return {
        'type': 'chart',
        'chart_type': chart_type,
        'title': f'{chart_type.title()} Chart of {column}',
        'labels': labels,
        'data': values,
        'column': column,
        'table': table_name,
        'total_records': len(df),
        'is_numeric': is_numeric,
        'insights': insights,
        'message': f'Generated {chart_type} chart for {column} from {table_name} table'
    }

def generate_data_insights(df, column, chart_type, original_chart_type=None):
    """Generate insights about the data for better analysis"""
    insights = []
    
    # Basic statistics
    total_records = len(df)
    unique_values = df[column].nunique()
    null_count = df[column].isnull().sum()
    
    insights.append(f"📊 **Data Overview**: {total_records:,} total records, {unique_values:,} unique values")
    
    # Add note if chart type was converted
    if original_chart_type and original_chart_type != chart_type:
        insights.append(f"🔄 **Chart Conversion**: Converted from {original_chart_type} to {chart_type} chart for better data visualization")
    
    if null_count > 0:
        insights.append(f"⚠️ **Missing Data**: {null_count:,} null values ({null_count/total_records*100:.1f}%)")
    
    # Data type specific insights
    if pd.api.types.is_numeric_dtype(df[column]):
        # Numerical data insights
        mean_val = df[column].mean()
        median_val = df[column].median()
        std_val = df[column].std()
        min_val = df[column].min()
        max_val = df[column].max()
        
        insights.append(f"📈 **Statistics**: Mean: {mean_val:.2f}, Median: {median_val:.2f}, Std: {std_val:.2f}")
        insights.append(f"📏 **Range**: {min_val:.2f} to {max_val:.2f}")
        
        # Distribution insights
        if chart_type == "line":
            insights.append("📊 **Trend Analysis**: Line chart shows distribution pattern of numerical values")
        elif chart_type == "bar":
            insights.append("📊 **Distribution**: Bar chart shows frequency distribution of numerical values")
            
    else:
        # Categorical data insights
        most_common = df[column].mode().iloc[0] if not df[column].mode().empty else "N/A"
        most_common_count = df[column].value_counts().iloc[0] if not df[column].empty else 0
        most_common_pct = (most_common_count / total_records) * 100
        
        insights.append(f"🏆 **Most Common**: '{most_common}' appears {most_common_count:,} times ({most_common_pct:.1f}%)")
        
        if chart_type == "pie":
            insights.append("🥧 **Distribution**: Pie chart shows proportional distribution of categories")
        elif chart_type == "bar":
            insights.append("📊 **Categories**: Bar chart shows frequency of each category (sorted by frequency)")
        elif chart_type == "line":
            insights.append("📈 **Trend**: Line chart shows distribution pattern of categorical values")
    
    # Data quality insights
    if unique_values == total_records:
        insights.append("💡 **Note**: All values are unique - consider if this column is an identifier")
    elif unique_values < 10:
        insights.append("💡 **Note**: Low cardinality - good for categorical analysis")
    
    # Trend insights for time-based data
    if 'time' in column.lower() or 'date' in column.lower():
        try:
            df_temp = df.copy()
            df_temp[column] = pd.to_datetime(df_temp[column], errors='coerce')
            if not df_temp[column].isnull().all():
                date_range = df_temp[column].max() - df_temp[column].min()
                insights.append(f"📅 **Time Range**: {date_range.days} days of data")
        except:
            pass
    
    return insights

# ===============================  
# 5. Fetch + Analyze Data
# ===============================
def fetch_and_answer(query: str):
    decision = interpret_query_simple(query)
    table, cols = decision.get("table"), decision.get("columns", [])
    
    if not table or table not in TABLES:
        print("🙏 Sorry, I can't answer that request with the current database.")
        return
    
    try:
        response = supabase.table(table).select("*").limit(1000).execute()
        if not response.data:
            print(f"⚠️ No data in table {table}")
            return
        
        df = pd.DataFrame(response.data)
        query_lower = query.lower()
        
        # ===============================  
        # Handle counts
        # ===============================
        if "number of" in query_lower or "count" in query_lower:
            if "completed" in query_lower and "order_status" in df.columns:
                count_val = df[df["order_status"].str.lower() == "completed"].shape[0]
            elif "education verification" in query_lower and "subject_id" in df.columns:
                count_val = df.shape[0]
            else:
                count_val = len(df)
            print(f"\n💡 Answer:\nThere are {count_val} records")
            return
        
        # ===============================  
        # Handle unique values
        # ===============================
        if "unique" in query_lower:
            col = cols[0] if cols else df.columns[0]
            unique_vals = df[col].drop_duplicates().tolist()
            print(f"\n💡 Answer:\nUnique values in '{col}': {unique_vals}")
            return
        
        # ===============================  
        # Handle chart generation requests
        # ===============================
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
            return chart_data
        
        # ===============================  
        # Handle distributions
        # ===============================
        if "distribution" in query_lower:
            col = cols[0] if cols else df.columns[0]
            if pd.api.types.is_numeric_dtype(df[col]):
                plt.figure(figsize=(8,5))
                sns.histplot(df[col], kde=True, bins=20)
                plt.title(f"Distribution of {col}")
                path = f"charts/{table}_{col}_hist.png"
                plt.savefig(path, bbox_inches="tight")
                plt.close()
                print(f"\n💡 Answer:\nHistogram saved: {path}")
            else:
                plt.figure(figsize=(8,5))
                sns.countplot(y=df[col], order=df[col].value_counts().index)
                plt.title(f"Distribution of {col}")
                path = f"charts/{table}_{col}_dist.png"
                plt.savefig(path, bbox_inches="tight")
                plt.close()
                print(f"\n💡 Answer:\nDistribution chart saved: {path}")
            return
        
        # ===============================  
        # Handle time filters like "since yesterday"
        # ===============================
        if "since yesterday" in query_lower:
            time_cols = [c for c in df.columns if "time" in c]
            if time_cols:
                yesterday = datetime.now() - timedelta(days=1)
                df = df[pd.to_datetime(df[time_cols[0]]) >= yesterday]
                print(f"\n💡 Answer:\nRecords since yesterday: {df.shape[0]}")
            return
        
        # ===============================  
        # Default: show sample data
        # ===============================
        sample = df.head().to_dict(orient="records")
        print("\n💡 Answer:\nSample data:")
        for r in sample:
            print(r)
            
    except Exception as e:
        print(f"❌ Error processing query: {e}")

# ===============================  
# 6. Interactive Loop
# ===============================
if __name__ == "__main__":
    print("💡 Ask me questions about the database (type 'bye' to exit).")
    print("✅ Using simplified query interpreter (no ChromaDB required)")
    while True:
        user_query = input("\nEnter your query: ")
        if user_query.strip().lower() == "bye":
            print("👋 Goodbye!")
            break
        fetch_and_answer(user_query)
