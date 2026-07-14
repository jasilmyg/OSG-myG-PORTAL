import os

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find start and end indices
start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if "@app.route('/api/whatsapp/request-report', methods=['POST'])" in line:
        start_idx = i
    if "if __name__ == '__main__':" in line:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    new_code = '''@app.route('/api/webhooks/telfiny', methods=['POST'])
def telfiny_webhook():
    data = request.json
    if not data:
        return jsonify({'success': False}), 400
    
    msg_id = data.get('messageId')
    mobile = data.get('mobileNumber') or data.get('mobile')
    status = data.get('status', '').lower()
    reason = data.get('errorDescription') or data.get('reason') or ''
    
    if msg_id and mobile:
        try:
            conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO whatsapp_message_logs (message_id, mobile_number, status, failure_reason)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (message_id) 
                    DO UPDATE SET status = EXCLUDED.status, failure_reason = EXCLUDED.failure_reason, updated_at = CURRENT_TIMESTAMP
                """, (msg_id, mobile, status, reason))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f'Webhook DB Error: {e}')
            
    return jsonify({'success': True}), 200

@app.route('/api/whatsapp/request-report', methods=['POST'])
@login_required
def request_whatsapp_report():
    data = request.json
    from_date = data.get('fromDate')
    to_date = data.get('toDate')

    if not from_date or not to_date:
        return jsonify({'success': False, 'message': 'Missing dates'}), 400

    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT status, COUNT(*) as count 
                FROM whatsapp_message_logs 
                WHERE created_at::date >= %s AND created_at::date <= %s
                GROUP BY status
            """, (from_date, to_date))
            
            stats_rows = cur.fetchall()
            stats = {row['status']: row['count'] for row in stats_rows}
            
            cur.execute("""
                SELECT mobile_number as mobile, TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') as date, failure_reason as reason 
                FROM whatsapp_message_logs 
                WHERE created_at::date >= %s AND created_at::date <= %s AND status IN ('failed', 'error')
                ORDER BY created_at DESC
                LIMIT 100
            """, (from_date, to_date))
            failed_messages = cur.fetchall()
            
        conn.close()
        
        return jsonify({
            'success': True,
            'fileID': f'local_{from_date}_{to_date}',
            'status': 'completed',
            'data': {
                'sent': stats.get('sent', 0) + stats.get('submitted', 0),
                'delivered': stats.get('delivered', 0),
                'read': stats.get('read', 0),
                'failed': stats.get('failed', 0) + stats.get('error', 0),
                'failed_messages': failed_messages
            }
        }), 200
    except Exception as e:
        logger.error(f'Error querying DB for report: {e}')
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/whatsapp/poll-report/<file_id>', methods=['GET'])
@login_required
def poll_whatsapp_report(file_id):
    if file_id.startswith('local_'):
        parts = file_id.split('_')
        from_date = parts[1]
        to_date = parts[2]
        
        try:
            conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM whatsapp_message_logs 
                    WHERE created_at::date >= %s AND created_at::date <= %s
                    GROUP BY status
                """, (from_date, to_date))
                
                stats_rows = cur.fetchall()
                stats = {row['status']: row['count'] for row in stats_rows}
                
                cur.execute("""
                    SELECT mobile_number as mobile, TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') as date, failure_reason as reason 
                    FROM whatsapp_message_logs 
                    WHERE created_at::date >= %s AND created_at::date <= %s AND status IN ('failed', 'error')
                    ORDER BY created_at DESC
                    LIMIT 100
                """, (from_date, to_date))
                failed_messages = cur.fetchall()
                
            conn.close()
            
            return jsonify({
                'status': 'completed',
                'data': {
                    'sent': stats.get('sent', 0) + stats.get('submitted', 0),
                    'delivered': stats.get('delivered', 0),
                    'read': stats.get('read', 0),
                    'failed': stats.get('failed', 0) + stats.get('error', 0),
                    'failed_messages': failed_messages
                }
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    return jsonify({'success': False, 'message': 'Invalid file ID'}), 400

'''
    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(lines[:start_idx])
        f.write(new_code)
        f.writelines(lines[end_idx:])
    print('Replaced endpoints successfully.')
else:
    print('Failed to find start or end index')
