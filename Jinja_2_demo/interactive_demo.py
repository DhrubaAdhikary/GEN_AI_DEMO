"""
Interactive Healthcare Analytics Demo
Ask queries and get insights with visualizations!
"""

import json
import os
import sys
import re
import asyncio
import asyncio

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prompt_constellatiion import render__prompt, build_html_table

# Try to import from bedrock_connector (with AWS Secrets Manager)
try:
    from bedrock_connector.gemini_connector import (
        genai, GEMINI_MODEL_ID, _get_gemini_model, astream_gemini_synthesis
    )
    print("✅ Gemini API configured from AWS Secrets Manager")
    GEMINI_CONFIGURED = True
except Exception as e:
    print(f"⚠️  Could not load Gemini from bedrock_connector: {e}")
    print("   Set ENV=DEV to use AWS Secrets Manager\n")
    GEMINI_CONFIGURED = False
    GEMINI_MODEL_ID = None
    astream_gemini_synthesis = None


def handle_query(user_query, query_type):
    """Universal handler for both table and marketshare queries"""
    
    if query_type == 'table':
        print("\n" + "="*80)
        print("📊 GENERATING TABLE RESPONSE")
        print("="*80 + "\n")
        
        # Mock table data
        table_columns = [
            "physician_id", "physician_name", "specialty", "drug_name",
            "prescriptions_count", "total_patients", "avg_dosage_mg", "region"
        ]
        
        table_rows = [
            {"physician_id": "HCP001", "physician_name": "Dr. Sarah Johnson", "specialty": "Cardiology", 
             "drug_name": "Atorvastatin", "prescriptions_count": 245, "total_patients": 198, "avg_dosage_mg": 40, "region": "Northeast"},
            {"physician_id": "HCP002", "physician_name": "Dr. Michael Chen", "specialty": "Cardiology", 
             "drug_name": "Atorvastatin", "prescriptions_count": 312, "total_patients": 267, "avg_dosage_mg": 40, "region": "West"},
            {"physician_id": "HCP003", "physician_name": "Dr. Emily Rodriguez", "specialty": "Endocrinology", 
             "drug_name": "Metformin", "prescriptions_count": 428, "total_patients": 389, "avg_dosage_mg": 1000, "region": "South"},
            {"physician_id": "HCP004", "physician_name": "Dr. James Wilson", "specialty": "Cardiology", 
             "drug_name": "Lisinopril", "prescriptions_count": 198, "total_patients": 176, "avg_dosage_mg": 20, "region": "Midwest"},
            {"physician_id": "HCP005", "physician_name": "Dr. Lisa Anderson", "specialty": "Endocrinology", 
             "drug_name": "Metformin", "prescriptions_count": 356, "total_patients": 312, "avg_dosage_mg": 850, "region": "Northeast"},
            {"physician_id": "HCP006", "physician_name": "Dr. Robert Martinez", "specialty": "Neurology", 
             "drug_name": "Gabapentin", "prescriptions_count": 287, "total_patients": 245, "avg_dosage_mg": 300, "region": "West"},
            {"physician_id": "HCP007", "physician_name": "Dr. Jennifer Lee", "specialty": "Cardiology", 
             "drug_name": "Atorvastatin", "prescriptions_count": 401, "total_patients": 342, "avg_dosage_mg": 80, "region": "South"},
            {"physician_id": "HCP008", "physician_name": "Dr. David Brown", "specialty": "Psychiatry", 
             "drug_name": "Sertraline", "prescriptions_count": 523, "total_patients": 489, "avg_dosage_mg": 100, "region": "Midwest"},
            {"physician_id": "HCP009", "physician_name": "Dr. Maria Garcia", "specialty": "Rheumatology", 
             "drug_name": "Methotrexate", "prescriptions_count": 156, "total_patients": 134, "avg_dosage_mg": 15, "region": "Northeast"},
            {"physician_id": "HCP010", "physician_name": "Dr. Thomas White", "specialty": "Endocrinology", 
             "drug_name": "Insulin Glargine", "prescriptions_count": 289, "total_patients": 223, "avg_dosage_mg": 35, "region": "West"},
        ]
        
        columns_metadata = {
            "physician_id": "Unique identifier for the healthcare provider",
            "physician_name": "Full name of the prescribing physician",
            "specialty": "Medical specialty of the physician",
            "drug_name": "Name of the prescribed pharmaceutical product",
            "prescriptions_count": "Total number of prescriptions written in the reporting period",
            "total_patients": "Total number of unique patients who received prescriptions",
            "avg_dosage_mg": "Average dosage prescribed in milligrams",
            "region": "Geographic region where the physician practices"
        }
        
        visualization = {
            "chart_type": "TABLE",
            "title": "Top Prescribers Analysis",
            "description": "Healthcare providers ranked by prescription volume"
        }
        
        table_text = json.dumps(table_rows)
        
    else:  # marketshare
        print("\n" + "="*80)
        print("📈 GENERATING MARKET SHARE RESPONSE")
        print("="*80 + "\n")
        
        # Mock marketshare data
        table_rows = [
            {
                "name": "Northeast",
                "data": [
                    {"name": "Atorvastatin", "value": 890},
                    {"name": "Metformin", "value": 784},
                    {"name": "Lisinopril", "value": 567},
                    {"name": "Gabapentin", "value": 423},
                    {"name": "Sertraline", "value": 678}
                ]
            },
            {
                "name": "South",
                "data": [
                    {"name": "Atorvastatin", "value": 829},
                    {"name": "Metformin", "value": 923},
                    {"name": "Lisinopril", "value": 634},
                    {"name": "Gabapentin", "value": 512},
                    {"name": "Sertraline", "value": 701}
                ]
            },
            {
                "name": "Midwest",
                "data": [
                    {"name": "Atorvastatin", "value": 745},
                    {"name": "Metformin", "value": 678},
                    {"name": "Lisinopril", "value": 789},
                    {"name": "Gabapentin", "value": 456},
                    {"name": "Sertraline", "value": 890}
                ]
            },
            {
                "name": "West",
                "data": [
                    {"name": "Atorvastatin", "value": 956},
                    {"name": "Metformin", "value": 812},
                    {"name": "Lisinopril", "value": 701},
                    {"name": "Gabapentin", "value": 634},
                    {"name": "Sertraline", "value": 756}
                ]
            }
        ]
        
        table_columns = ["region", "drug", "prescription_volume"]
        columns_metadata = {
            "region": "Geographic region in the United States",
            "drug": "Pharmaceutical product name",
            "prescription_volume": "Total number of prescriptions"
        }
        
        visualization = {
            "chart_type": "MARKETSHARE_GRAPH",
            "title": "Drug Market Share by Region",
            "description": "Stacked bar chart showing drug distribution across regions"
        }
        
        table_text = json.dumps(table_rows)
    
    # Render prompt
    prompt_str, rendered_html = render__prompt(
        subquery=user_query,
        table_text=table_text,
        visualization=visualization,
        user_pref={"format": "detailed" if query_type == 'table' else "chart"},
        table_columns=table_columns,
        table_rows=table_rows,
        columns_metadata=columns_metadata
    )
    
    # Call Gemini with async streaming
    if GEMINI_CONFIGURED:
        print("\n🤖 Generating AI insights (streaming)...\n")
        print("-" * 80)
        
        try:
            # Use async streaming from bedrock_connector
            async def stream_response():
                full_response = []
                async for piece in astream_gemini_synthesis(GEMINI_MODEL_ID, prompt_str):
                    print(piece, end="", flush=True)
                    full_response.append(piece)
                return "".join(full_response)
            
            response_text = asyncio.run(stream_response())
            
            print("\n" + "=" * 80)
            
            # Display data below AI insights
            if query_type == 'table':
                print("📊 TABLE DATA")
                print("=" * 80 + "\n")
                print(rendered_html)
            else:
                print("📈 CHART DATA (JSON)")
                print("=" * 80 + "\n")
                print(json.dumps(table_rows, indent=2))
            
            print("\n" + "=" * 80)
            print("✅ Response complete!")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n⚠️ Gemini not configured. Please set ENV=DEV to use AWS Secrets Manager.")


def classify_query(query):
    """Classify user query to determine visualization type"""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['table', 'physician', 'doctor', 'prescription', 'list']):
        return 'table'
    elif any(word in query_lower for word in ['market', 'share', 'distribution', 'chart', 'graph', 'region']):
        return 'marketshare'
    else:
        return 'unknown'


def main():
    """Main interactive loop"""
    print("\n" + "="*80)
    print("🏥 INTERACTIVE HEALTHCARE ANALYTICS DEMO")
    print("="*80)
    print("\nAvailable queries:")
    print("  • 'Give me a table' - Shows physician prescription data")
    print("  • 'Give me marketshare' - Shows drug market share by region")
    print("  • 'quit' or 'exit' - Exit the program")
    print("\n" + "="*80 + "\n")
    
    while True:
        try:
            user_query = input("Your query: ").strip()
            
            if not user_query:
                continue
            
            if user_query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            # Classify query
            query_type = classify_query(user_query)
            
            if query_type == 'table':
                handle_query(user_query, 'table')
            elif query_type == 'marketshare':
                handle_query(user_query, 'marketshare')
            else:
                print(f"\n❓ I didn't understand that query.")
                print("Try asking for 'table' or 'marketshare'")
            
            print("\n" + "="*80 + "\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n✗ Error: {e}")
            print("Try again with a different query.\n")


if __name__ == "__main__":
    main()
