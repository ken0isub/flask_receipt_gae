import gspread
import datetime
from oauth2client.service_account import ServiceAccountCredentials


def write_sheet(price, store, category, date, note, who, point):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        'del/project-delete-soon.json', scope)
    gc = gspread.authorize(credentials)

    # ローカルでは以下で "C:\Users\kenta\AppData\Roaming\gspread\service_account.json"を読み込む
    # gc = gspread.service_account()

    SPREADSHEET_KEY = '1oTHL36fBbPvpjH2KT1sdxgHjFHwgQ5gmqSxGXugamwc'
    workbook = gc.open_by_key(SPREADSHEET_KEY)
    worksheet = workbook.worksheet('Form Responses 1')

    timestamp = datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S')

    col_list = worksheet.col_values(1)
    print(col_list)
    print(len(col_list))
    last_row = len(col_list) + 1

    target_range = 'A' + str(last_row) + ':H' + str(last_row)
    ds = worksheet.range(target_range)
    ds[0].value = timestamp
    ds[1].value = price
    ds[2].value = store
    ds[3].value = category
    ds[4].value = date
    ds[5].value = note
    ds[6].value = who
    ds[7].value = point

    worksheet.update_cells(ds)

if __name__ == '__main__':
    write_sheet()