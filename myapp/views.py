from django.shortcuts import render
from .forms import CSVUploadForm
import pandas as pd
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from django.conf import settings

def process_csv(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data['csv_file']
            results = process_csv_file(csv_file)
            spreadsheet_id = '1MtVBlj_L1uDASd1_WXESD_Dgl6GaXBinuDvX-DXBf6k'
            send_to_google_sheets(spreadsheet_id, results)
            return render(request, 'myapp/results.html', {'results': results, 'spreadsheet_id': spreadsheet_id})
    else:
        form = CSVUploadForm()
    return render(request, 'myapp/index.html', {'form': form})

def process_csv_file(csv_file):
    try:
        # Read the CSV file using pandas
        df = pd.read_csv(csv_file, encoding='utf-8')

        # Print the first 10 lines for debugging
        print("CSV Lines (First 10):")
        print(df.head(10))

        # Initialize dictionary to hold the key-value pairs
        key_value_pairs = {
            "Usuários (soma do mês todo)": 0,
        }

        # Process the data section by section
        data_section = False
        for index, row in df.iterrows():
            # Check for section start
            if row[0].startswith("# Data de início"):
                data_section = True
                continue
            
            # Sum the "Usuários ativos" in the data section
            if data_section and pd.notna(row[1]) and isinstance(row[1], int):
                key_value_pairs["Usuários (soma do mês todo)"] += row[1]

        # Logging the extracted data
        print("Extracted Data:", key_value_pairs)
        
        return key_value_pairs
    
    except pd.errors.EmptyDataError:
        print("No columns to parse from file")
        return {}
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return {}

def send_to_google_sheets(spreadsheet_id, data):
    creds = Credentials.from_service_account_file(
        settings.GOOGLE_SHEETS_CREDENTIALS_JSON, 
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()

    # Adding headers to the sheet
    headers = [['Key', 'Value']]
    values = [[key, value] for key, value in data.items()]
    data_to_send = headers + values

    body = {
        'values': data_to_send
    }

    RANGE_NAME = "'Página1'!A1:B{}".format(len(data_to_send) + 1)
    result = sheet.values().update(
        spreadsheetId=spreadsheet_id, range=RANGE_NAME,
        valueInputOption="RAW", body=body).execute()

    print(f'Data sent to Google Sheets: {data}')
    print(f'Range used: {RANGE_NAME}')
