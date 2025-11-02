from http.server import BaseHTTPRequestHandler
import json
import pandas as pd
from io import BytesIO

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Read request body
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        try:
            url = data.get('url', '')
            keyword = data.get('keyword', '')
            all_links = data.get('all_links', [])
            filtered_links = data.get('filtered_links', [])
            
            # Create Excel file in memory
            output = BytesIO()
            
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Sheet 1: Filtered/Displayed links
                if keyword:
                    df_filtered = pd.DataFrame(filtered_links)
                    df_filtered.to_excel(writer, sheet_name='Filtered Links', index=False)
                else:
                    df_all = pd.DataFrame(all_links)
                    df_all.to_excel(writer, sheet_name='All Links', index=False)
                
                # Sheet 2: All scraped links (always include)
                df_all = pd.DataFrame(all_links)
                df_all.to_excel(writer, sheet_name='All Scraped Links', index=False)
                
                # Get workbook and worksheet objects for formatting
                workbook = writer.book
                
                # Format for URLs (make them clickable)
                url_format = workbook.add_format({'color': 'blue', 'underline': 1})
                
                # Format filtered links sheet
                if keyword and filtered_links:
                    worksheet1 = writer.sheets['Filtered Links']
                    worksheet1.set_column('A:A', 50)  # Text column width
                    worksheet1.set_column('B:B', 80)  # URL column width
                    
                    # Make URLs clickable
                    for row_num, link in enumerate(filtered_links, start=1):
                        worksheet1.write_url(row_num, 1, link['url'], url_format, string=link['url'])
                
                # Format all links sheet
                worksheet2 = writer.sheets['All Scraped Links']
                worksheet2.set_column('A:A', 50)  # Text column width
                worksheet2.set_column('B:B', 80)  # URL column width
                
                # Make URLs clickable
                for row_num, link in enumerate(all_links, start=1):
                    worksheet2.write_url(row_num, 1, link['url'], url_format, string=link['url'])
            
            # Get the Excel file bytes
            excel_data = output.getvalue()
            
            # Send response with Excel file
            self.send_response(200)
            self.send_header('Content-type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            self.send_header('Content-Disposition', 'attachment; filename="extracted_links.xlsx"')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(excel_data)
            
        except Exception as e:
            error_response = {
                'success': False,
                'error': f'Failed to generate Excel: {str(e)}'
            }
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()