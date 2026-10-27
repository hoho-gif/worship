"""
同じフォルダにあるファイルのファイル名の一部を抽出し、
psalm_en_chech.xlsx に書き込むプログラム。

使い方:
    python extract_filenames.py

必要なライブラリ:
    pip install openpyxl
"""

import re
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook

# ===== 設定（ここを変更して使ってください） =====

# 抽出したい部分を表す正規表現。()で囲んだ部分が抽出されます。
# 例1: "psalm_en_001.mp3" から "001" を取り出す → r"psalm_en_(\d+)"
# 例2: "psalm_en_001.mp3" から "psalm_en_001"（拡張子なし）→ r"(.+)\.\w+$"
# 例3: "Psalm 23 - Czech.txt" から "23" を取り出す → r"Psalm (\d+)"
PATTERN = r"psalm_(\d+[A-Za-z]*)_en\.pdf"

OUTPUT_NAME = "psalm_en_chech.xlsx"

# ===== ここから下は基本的に変更不要 =====


def main() -> None:
    # このスクリプトが置かれているフォルダを対象にする
    folder = Path(__file__).resolve().parent
    regex = re.compile(PATTERN)

    wb = Workbook()
    ws = wb.active
    ws.title = "filenames"
    ws.append(["元のファイル名", "抽出した部分"])

    rows = []
    for path in sorted(
        folder.iterdir(),
        key=lambda item: [
            int(part) if part.isdigit() else part.casefold()
            for part in re.split(r"(\d+)", item.name)
        ],
    ):
        # フォルダ、出力ファイル自身、このスクリプト自身は除外
        if not path.is_file():
            continue
        if path.name in (OUTPUT_NAME, Path(__file__).name):
            continue
        # Excelの一時ファイル(~$...)も除外
        if path.name.startswith("~$"):
            continue

        match = regex.search(path.name)
        # マッチしなければ空欄にして、後で見つけやすくする
        extracted = match.group(1) if match else ""
        rows.append((path.name, extracted))

    for row in rows:
        ws.append(row)

    # 列幅を調整
    ws.column_dimensions["A"].width = 40
    ws.column_dimensions["B"].width = 20

    output_path = folder / OUTPUT_NAME
    try:
        wb.save(output_path)
    except PermissionError:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output_path = folder / (
            f"{Path(OUTPUT_NAME).stem}_{timestamp}{Path(OUTPUT_NAME).suffix}"
        )
        wb.save(output_path)
        print(
            f"{OUTPUT_NAME} に保存できなかったため、別名で保存しました。"
            "Excelで開いている場合は、閉じてから再実行すると元のファイルを更新できます。"
        )
    print(f"{len(rows)} 件を {output_path.name} に書き込みました。")
    unmatched = [name for name, ext in rows if not ext]
    if unmatched:
        print(f"パターンに一致しなかったファイル: {len(unmatched)} 件")
        for name in unmatched:
            print("  -", name)


if __name__ == "__main__":
    main()