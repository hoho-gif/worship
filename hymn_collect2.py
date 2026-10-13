import csv
import io
import os
import re
import shutil
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import urlopen


# ==========================================
# 設定
# ==========================================

# Googleスプレッドシートの共有URL
spreadsheet_url = "https://docs.google.com/spreadsheets/d/15zrUpKyzcz8PgqX7eBPxm0WnL_udhQ-Qy5A2PXBQ9v0/edit?usp=sharing"

# 空欄ならURLのgidを使用（URLにもなければ先頭タブ）。タブを固定する場合はgidを指定
spreadsheet_gid = ""

# 抽出を開始するシート上の行番号
start_row = 2


def load_public_sheet_rows(url, selected_gid, first_row):
    parsed_url = urlparse(url)
    match = re.search(r"/spreadsheets/d/([^/]+)", parsed_url.path)

    if not match:
        raise ValueError("Googleスプレッドシートの共有URLを設定してください。")

    if first_row < 1:
        raise ValueError("start_rowには1以上の行番号を指定してください。")

    gid = selected_gid or parse_qs(parsed_url.query).get("gid", [None])[0]
    if not gid and parsed_url.fragment:
        gid = parse_qs(parsed_url.fragment).get("gid", [None])[0]
    gid = gid or "0"

    csv_url = (
        f"https://docs.google.com/spreadsheets/d/{match.group(1)}"
        f"/export?format=csv&gid={gid}"
    )

    with urlopen(csv_url, timeout=30) as response:
        csv_text = response.read().decode("utf-8-sig")

    return list(csv.reader(io.StringIO(csv_text)))[first_row - 1:]


def format_date_value(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")

    date_text = str(value).strip()
    for date_format in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_text, date_format).strftime("%Y-%m-%d")
        except ValueError:
            continue

    return date_text


# ------------------------------------------
# 詩篇のファイルを探すフォルダ
# ------------------------------------------

psalm_source_folder = "psalm_jpg"


# ------------------------------------------
# 聖歌のファイルを探すフォルダ
# ------------------------------------------

hymn_source_folder = "hymn_jpg"


# ------------------------------------------
# 詩篇のコピー先
# ------------------------------------------

psalm_destination_folder = "song2"


# ------------------------------------------
# 聖歌のコピー先
# ------------------------------------------

hymn_destination_folder = "song2"


# ------------------------------------------
# TXTファイルの出力先
# ------------------------------------------

txt_destination_folder = "song2"


# ==========================================
# 詩篇から「148A」のような名前を抽出
# ==========================================

def extract_psalm_name(text):

    if not text:
        return ""

    text = str(text).strip()

    # 「詩篇」または「詩編」を削除
    #
    # 例：
    # 詩篇148A(1,5,7)
    # ↓
    # 148A(1,5,7)

    if text.startswith("詩篇"):
        text = text[2:]

    elif text.startswith("詩編"):
        text = text[2:]


    # "("以降を削除
    #
    # 148A(1,5,7)
    # ↓
    # 148A

    text = text.split("(")[0]

    return text.strip()


# ==========================================
# 聖歌から番号を抽出
# ==========================================

def extract_hymn_name(text):

    if not text:
        return ""

    text = str(text).strip()

    # 「聖歌」を削除
    #
    # 例：
    # 聖歌75
    # ↓
    # 75

    if text.startswith("聖歌"):
        text = text[2:]


    # "("以降を削除
    #
    # 聖歌390(1,3,4)
    # ↓
    # 390

    text = text.split("(")[0]

    return text.strip()


# ==========================================
# 数字の先頭ゼロを無視して比較するための正規化
# ==========================================

def normalize_for_match(text):

    # 文字列中の数字のかたまりを、
    # 先頭ゼロを取り除いた数値に置き換える
    #
    # 例：
    # "hymn_029" → "hymn_29"
    # "psalm007A" → "psalm7A"

    return re.sub(
        r"\d+",
        lambda m: str(int(m.group())),
        text
    )


# ==========================================
# コピー先フォルダを作成
# ==========================================

os.makedirs(
    psalm_destination_folder,
    exist_ok=True
)

os.makedirs(
    hymn_destination_folder,
    exist_ok=True
)

os.makedirs(
    txt_destination_folder,
    exist_ok=True
)


# ==========================================
# 公開スプレッドシートを読み込む
# ==========================================

try:
    sheet_rows = load_public_sheet_rows(
        spreadsheet_url,
        spreadsheet_gid,
        start_row
    )

except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, csv.Error, ValueError) as error:
    print(f"公開スプレッドシートを読み込めません：{error}")
    print("URLと「リンクを知っている全員が閲覧可」の共有設定を確認してください。")

    input("Enterキーを押して終了...")
    exit()


# ==========================================
# スプレッドシートを1行ずつ処理
# ==========================================

for row in sheet_rows:


    # ======================================
    # B列 → 日付
    # ======================================

    date_value = row[1] if len(row) > 1 else ""


    # ======================================
    # Z列 → 詩篇・聖歌
    # ======================================

    cell_value = row[26] if len(row) > 26 else ""


    # ======================================
    # 空欄ならスキップ
    # ======================================

    if not date_value or not cell_value:
        continue


    # ======================================
    # 日付を文字列に変換
    # ======================================

    date_string = format_date_value(date_value)


    # ======================================
    # Excelのセル内容を文字列にする
    # ======================================

    cell_text = str(
        cell_value
    ).strip()


    # ======================================
    # TXTファイルを作成
    # ======================================

    txt_file_name = (
        date_string
        + ".txt"
    )

    txt_file_path = os.path.join(
        txt_destination_folder,
        txt_file_name
    )


    # ======================================
    # Z列の内容をそのままTXTに書き込む
    # ======================================

    with open(
        txt_file_path,
        "w",
        encoding="utf-8"
    ) as txt_file:

        txt_file.write(
            cell_text
        )


    print("----------------------------------")
    print(
        f"TXTファイル作成：{txt_file_path}"
    )

    print(
        f"  内容：{cell_text}"
    )


    # ======================================
    # 詩篇の場合
    # ======================================

    if (
        cell_text.startswith("詩篇")
        or cell_text.startswith("詩編")
    ):


        # ----------------------------------
        # 詩篇番号を抽出
        # ----------------------------------

        extracted_name = extract_psalm_name(
            cell_text
        )


        if not extracted_name:

            print(
                f"詩篇番号を抽出できませんでした：{cell_text}"
            )

            continue


        # ----------------------------------
        # 検索するファイル名
        # ----------------------------------

        search_name = (
            "psalm"
            + extracted_name
        )


        # ----------------------------------
        # コピー後のファイル名
        # ----------------------------------

        final_name = (
            date_string
            + ".jpg"
        )


        # ----------------------------------
        # 検索フォルダ
        # ----------------------------------

        source_folder = psalm_source_folder


        # ----------------------------------
        # コピー先フォルダ
        # ----------------------------------

        destination_folder = (
            psalm_destination_folder
        )


        file_type = "詩篇"


    # ======================================
    # 聖歌の場合
    # ======================================

    elif cell_text.startswith("聖歌"):


        # ----------------------------------
        # 聖歌番号を抽出
        # ----------------------------------

        extracted_name = extract_hymn_name(
            cell_text
        )


        if not extracted_name:

            print(
                f"聖歌番号を抽出できませんでした：{cell_text}"
            )

            continue


        # ----------------------------------
        # 検索するファイル名
        # ----------------------------------

        # 例：
        #
        # 聖歌75
        # ↓
        # hymn_75

        search_name = (
            "hymn_"
            + extracted_name
        )


        # ----------------------------------
        # コピー後のファイル名
        # ----------------------------------

        final_name = (
            date_string
            + ".jpg"
        )


        # ----------------------------------
        # 検索フォルダ
        # ----------------------------------

        source_folder = hymn_source_folder


        # ----------------------------------
        # コピー先フォルダ
        # ----------------------------------

        destination_folder = (
            hymn_destination_folder
        )


        file_type = "聖歌"


    # ======================================
    # その他
    # ======================================

    else:

        print(
            f"【種類不明】{cell_text}"
        )

        continue


    # ======================================
    # 処理内容を表示
    # ======================================

    print(
        f"日付          ：{date_string}"
    )

    print(
        f"元のセル      ：{cell_text}"
    )

    print(
        f"種類          ：{file_type}"
    )

    print(
        f"抽出した番号  ：{extracted_name}"
    )

    print(
        f"検索する名前  ：{search_name}"
    )

    print(
        f"検索フォルダ  ：{source_folder}"
    )

    print(
        f"新しい名前    ：{final_name}"
    )


    # ======================================
    # ファイルを探す
    # ======================================

    found = False


    for root, dirs, files in os.walk(
        source_folder
    ):

        for filename in files:


            # 拡張子を除いたファイル名
            name_without_extension = os.path.splitext(
                filename
            )[0]


            # ==================================
            # ファイル名が一致
            # （数字の先頭ゼロの有無を無視して比較する）
            # ==================================

            if normalize_for_match(name_without_extension) == normalize_for_match(search_name):


                source_file = os.path.join(
                    root,
                    filename
                )


                # ==================================
                # コピー先
                # ==================================

                destination_file = os.path.join(
                    destination_folder,
                    final_name
                )


                # ==================================
                # コピー
                # ==================================

                shutil.copy2(
                    source_file,
                    destination_file
                )


                print(
                    "コピー完了！"
                )

                print(
                    f"  元ファイル ：{source_file}"
                )

                print(
                    f"  新ファイル ：{destination_file}"
                )

                found = True

                break

        # ファイルが見つかったら
        # サブフォルダ検索を終了

        if found:
            break

    # ======================================
    # ファイルが見つからなかった場合
    # ======================================

    if not found:

        print(
            f"【見つかりません】{search_name}"
        )
# ==========================================
# 終了
# ==========================================

print()
print("==========================================")
print("すべての処理が完了しました。")
print("==========================================")

input("Enterキーを押して終了...")