import re
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


def setup_sheets_api(credentials_file):
    """
    Google Sheets APIのセットアップ
    
    Args:
        credentials_file: サービスアカウントのJSONファイルパス
    
    Returns:
        Google Sheets APIサービス
    """
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    return service


def extract_spreadsheet_id(url_or_id):
    """
    URLまたはIDからスプレッドシートIDを抽出
    
    Args:
        url_or_id: Google SheetsのURLまたはID
    
    Returns:
        スプレッドシートID
    """
    # URLの場合、IDを抽出
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url_or_id)
    if match:
        return match.group(1)
    # すでにIDの場合はそのまま返す
    return url_or_id


def get_cell_value(service, spreadsheet_id, cell_address):
    """
    指定セルの値を取得
    
    Args:
        service: Google Sheets APIサービス
        spreadsheet_id: スプレッドシートのID
        cell_address: セルのアドレス (例: 'A1', 'B5', 'Y2')
    
    Returns:
        セルの値 (str)
    """
    sheet = service.spreadsheets()
    result = sheet.values().get(
        spreadsheetId=spreadsheet_id,
        range=cell_address
    ).execute()
    
    values = result.get('values', [])
    if not values:
        return None
    
    return values[0][0]


def process_text(text):
    """
    テキストを処理する
    1. 初めの2文字を抽出
    2. それ以降の文字から()で囲まれた部分を削除
    
    Args:
        text: 処理するテキスト
    
    Returns:
        (初めの2文字, 処理後の残り)
    """
    if not text or len(text) < 2:
        return text, ""
    
    # 初めの2文字
    first_two = text[:2]
    
    # それ以降
    rest = text[2:]
    
    # ()で囲まれた部分を削除
    # 例: "12345(test)" -> "12345"
    rest_cleaned = re.sub(r'\([^)]*\)', '', rest)
    
    return first_two, rest_cleaned


def main():
    """
    メイン処理
    """
    # ===== ここを編集してください =====
    CREDENTIALS_FILE = "credentials.json"  # サービスアカウントのJSONファイル
    SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1e5gMh7QVDA-ZtThYwex__izRnC0MISi3h5liBdTpCiY/edit?gid=0#gid=0"
    CELL_ADDRESS = "Y2"  # 読み取るセル（例: A1, B5, Y2など）
    # ================================
    
    # URLからIDを抽出
    spreadsheet_id = extract_spreadsheet_id(SPREADSHEET_URL)
    
    print("=== Googleスプレッドシート文字抽出 ===")
    print(f"スプレッドシートID: {spreadsheet_id}")
    print(f"対象セル: {CELL_ADDRESS}")
    print()
    
    try:
        # Google Sheets API setup
        service = setup_sheets_api(CREDENTIALS_FILE)
        
        # セルの値を取得
        cell_value = get_cell_value(service, spreadsheet_id, CELL_ADDRESS)
        
        if cell_value is None:
            print("❌ セルが空です")
            return
        
        print(f"✅ 元のテキスト: {cell_value}")
        print()
        
        # テキスト処理
        first_two, rest = process_text(cell_value)
        
        print("=== 処理結果 ===")
        print(f"📝 初めの2文字: {first_two}")
        print(f"📝 それ以降: {rest}")
        
    except FileNotFoundError:
        print("❌ エラー: credentials.json が見つかりません")
        print()
        print("💡 セットアップ方法:")
        print("1. Google Cloud Console (https://console.cloud.google.com/) にアクセス")
        print("2. 新しいプロジェクトを作成")
        print("3. 「APIとサービス」→「ライブラリ」から「Google Sheets API」を有効化")
        print("4. 「認証情報」→「サービスアカウントを作成」")
        print("5. サービスアカウントのキー(JSON)をダウンロード")
        print("6. ダウンロードしたファイルを 'credentials.json' にリネーム")
        print("7. このスクリプトと同じフォルダに配置")
        print("8. スプレッドシートをサービスアカウントのメールと共有（閲覧権限）")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        print()
        print("💡 よくあるエラー:")
        print("- スプレッドシートがサービスアカウントと共有されていない")
        print("- Google Sheets APIが有効になっていない")
        print("- credentials.jsonのパスが間違っている")


# ===================================
# 使い方例（テキスト処理のみ）
# ===================================
def simple_example():
    """
    テキスト処理だけを試す（APIなし）
    """
    print("=== テキスト処理テスト ===")
    
    test_cases = [
        "AB12345(test)",
        "XY999(remove)",
        "12ABC(123)DEF",
        "短い",
        "ABCDEFG",
    ]
    
    for text in test_cases:
        first_two, rest = process_text(text)
        print(f"入力: {text}")
        print(f"  → 初めの2文字: '{first_two}'")
        print(f"  → それ以降: '{rest}'")
        print()


if __name__ == "__main__":
    # テキスト処理だけを試す場合
    # simple_example()
    
    # Google Sheets APIを使う場合
    main()