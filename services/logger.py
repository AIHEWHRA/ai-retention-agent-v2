import psycopg2
import os

def log_conversation(customer_input, ai_response, retention_offer_made, customer_decision, final_action, full_messages):
    conn = psycopg2.connect(
        host=os.environ["PGHOST"],
        database=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        port=os.environ["PGPORT"]
    )
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO conversations
        (customer_input, ai_response, retention_offer_made, customer_decision, final_action, full_messages)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (customer_input, ai_response, retention_offer_made, customer_decision, final_action, full_messages))
    conn.commit()
    cur.close()
    conn.close()
