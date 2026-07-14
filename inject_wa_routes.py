import os

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

main_index = -1
for i, line in enumerate(lines):
    if line.strip().startswith("if __name__ == '__main__':") or line.strip().startswith('if __name__ == "__main__":'):
        main_index = i
        break

if main_index == -1:
    print("Could not find __main__ block")
else:
    new_routes = """
# ==========================================
# WHATSAPP REPORTS (TELFINY API)
# ==========================================

import csv
import io

@app.route('/whatsapp-reports')
@login_required
def whatsapp_reports():
    return render_template('whatsapp_reports.html')

@app.route('/api/whatsapp/request-report', methods=['POST'])
@login_required
def request_whatsapp_report():
    data = request.json
    from_date = data.get('fromDate')
    to_date = data.get('toDate')

    if not from_date or not to_date:
        return jsonify({'success': False, 'message': 'Missing dates'}), 400

    api_key = os.getenv("TELFINY_API_KEY")
    if not api_key:
        return jsonify({'success': False, 'message': 'API Key not configured'}), 500

    url = "https://hub.telinfy.com/unified/developer/api/v1/whatsapp/reports/request-download"
    try:
        res = requests.post(
            url,
            headers={"x-api-key": api_key, "Content-Type": "application/json"},
            json={"fromDate": from_date, "toDate": to_date}
        )
        # Some APIs return 400 with success:false inside, so parse JSON first
        resp_data = res.json()
        return jsonify(resp_data), res.status_code
    except Exception as e:
        logger.error(f"Error requesting WhatsApp report: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/whatsapp/poll-report/<file_id>', methods=['GET'])
@login_required
def poll_whatsapp_report(file_id):
    api_key = os.getenv("TELFINY_API_KEY")
    url = f"https://hub.telinfy.com/unified/developer/api/v1/whatsapp/reports/file/{file_id}"

    try:
        res = requests.get(url, headers={"x-api-key": api_key})
        
        content_type = res.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            data = res.json()
            return jsonify(data), res.status_code
            
        # If it's a file (CSV), parse it!
        content = res.content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(content))
        
        # Aggregation
        sent = 0
        delivered = 0
        read = 0
        failed = 0
        failed_messages = []
        
        # Flexible column name detection
        fieldnames = [f.lower() for f in (reader.fieldnames or [])]
        
        status_col = next((f for f in fieldnames if 'status' in f), None)
        mobile_col = next((f for f in fieldnames if 'mobile' in f or 'number' in f or 'phone' in f), None)
        reason_col = next((f for f in fieldnames if 'reason' in f or 'error' in f or 'desc' in f), None)
        date_col = next((f for f in fieldnames if 'date' in f or 'time' in f), None)
        
        for row in reader:
            # Map back from lower to actual
            actual_row = {k.lower(): v for k, v in row.items() if k}
            
            status = actual_row.get(status_col, '').lower() if status_col else ''
            
            if status == 'sent':
                sent += 1
            elif status == 'delivered':
                delivered += 1
            elif status == 'read':
                read += 1
            elif status == 'failed':
                failed += 1
                failed_messages.append({
                    'mobile': actual_row.get(mobile_col, 'N/A') if mobile_col else 'N/A',
                    'date': actual_row.get(date_col, 'N/A') if date_col else 'N/A',
                    'reason': actual_row.get(reason_col, 'N/A') if reason_col else 'N/A',
                })
            else:
                # Catch-all if status names differ slightly
                if 'fail' in status or 'error' in status:
                    failed += 1
                    failed_messages.append({
                        'mobile': actual_row.get(mobile_col, 'N/A') if mobile_col else 'N/A',
                        'date': actual_row.get(date_col, 'N/A') if date_col else 'N/A',
                        'reason': actual_row.get(reason_col, 'N/A') if reason_col else 'N/A',
                    })
                elif 'sent' in status or 'submitted' in status:
                    sent += 1
                elif 'deliver' in status:
                    delivered += 1
                elif 'read' in status:
                    read += 1
        
        return jsonify({
            'status': 'completed',
            'data': {
                'sent': sent,
                'delivered': delivered,
                'read': read,
                'failed': failed,
                'failed_messages': failed_messages
            }
        })

    except Exception as e:
        logger.error(f"Error polling WhatsApp report: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

"""
    lines.insert(main_index, new_routes)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Routes added successfully")
