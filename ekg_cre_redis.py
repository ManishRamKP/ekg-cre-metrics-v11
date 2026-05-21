import os
from flask import Flask, request, jsonify
import redis
import pandas as pd
import json
from datetime import datetime

app = Flask(__name__)

# Initialize Redis connection
redis_graph = redis.Redis(
    host=os.environ.get('REDIS_HOST', 'localhost'),
    port=6379,
    password=os.environ.get('REDIS_PASSWORD', ''),
    decode_responses=True
)
GRAPH_NAME = 'nodes_finflowgraph'

def fetch_edges():
    query = "MATCH (src)-[r:OUTBOUND]->(dest) RETURN id(r) AS edge_id, src.gstin AS source_gstin, dest.gstin AS dest_gstin"
    response = redis_graph.execute_command("GRAPH.QUERY", GRAPH_NAME, query)
    headers = response[0]
    rows = [[value for value in row] for row in response[1]]
    edges_df = pd.DataFrame(rows, columns=headers)
    return edges_df

@app.route('/edges', methods=['POST'])
def manage_edges():
    json_data = request.json
    edges_df = fetch_edges()

    response_details = []

    for row in json_data:
        current_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
        source_gstin = row['ptgstin']
        dest_gstin = row['ctin']
        matched_edges = edges_df[(edges_df['source_gstin'] == source_gstin) & (edges_df['dest_gstin'] == dest_gstin)]

        properties = {
            "1_3_months": row.get("1_3_months", 0),
            "2_3_months": row.get("2_3_months", 0),
            "3_3_months": row.get("3_3_months", 0),
            "4_3_months": row.get("4_3_months", 0),
            "numberofinvoices": row.get("numberofinvoices", 0),
            "avginvoiceamount": row.get("avginvoiceamount", 0),
            "opvin": row.get("opvin", ''),
            "invoice_to_cashflow_ema": row.get("invoice_to_cashflow_ema", 0),
            "recentdate": row.get("recentdate", ''),
            "source": row.get("source", ''),
            "ptgstinscore": row.get("ptgstinscore", 0),
            "ctinscore": row.get("ctinscore", 0),
            "totalinvoiceamount": row.get("totalinvoiceamount", 0),
            "lasttimestamp": row.get("lasttimestamp", current_date),
            "edgecreatedtimestamp": row.get("edgecreatedtodaytimestamp", current_date),
            "cremetricsupdatedtimestamp": row.get("cremetricsupdatedtimestamp", current_date)
        }

        if not matched_edges.empty:
            # Update existing edges
            for _, edge in matched_edges.iterrows():
                edge_id = edge['edge_id']
                properties_update_string = ", ".join([f"r.`{key}` = {json.dumps(value)}" for key, value in properties.items()])
                update_query = f"MATCH ()-[r]->() WHERE id(r) = {edge_id} SET {properties_update_string}"
                redis_graph.execute_command("GRAPH.QUERY", GRAPH_NAME, update_query)
                response_details.append({"action": "updated", "edge_id": edge_id, "source_gstin": source_gstin, "dest_gstin": dest_gstin})                
                                 
                        
        else:
            # Create new edges
            properties_string = ', '.join(f'`{key}`: {json.dumps(value)}' for key, value in properties.items())
            create_query = (
                f"MERGE (a:enterprise{{gstin: '{source_gstin}'}}) "
                f"MERGE (b:enterprise{{gstin: '{dest_gstin}'}}) "
                f"MERGE (a)-[:OUTBOUND {{{properties_string}}}]->(b)"
            )
            redis_graph.execute_command("GRAPH.QUERY", GRAPH_NAME, create_query)
            response_details.append({"action": "created", "source_gstin": source_gstin, "dest_gstin": dest_gstin})

    return jsonify({
        "message": "Edge processing complete",
        "details": response_details
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5000)