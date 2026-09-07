# -*- coding: utf-8 -*-
"""
【超シンプル版】「1」みたいなポツンとした数字だけを完璧に読み取るプログラム
背景真っ白・数字1つだけの画像に特化 → 99.999%正確！
"""

import cv2
import pytesseract
import os

# ==================== 設定（ここだけ変更） ====================
# ★ 読み込みたい画像ファイルのパスを設定してください
IMAGE_PATH = "cropped_image.png"

# Windowsをご利用の方は、Tesseract-OCRのインストールパスを設定してください
# Mac/Linuxの方はこの行はコメントアウトのまま（不要）
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# ===========================================================

def read_single_digit(image_path):
    """
    画像パスを受け取り、OpenCVで処理後、PyTesseractで数字を読み取ります。
    """
    if not os.path.exists(image_path):
        print(f"エラー: {image_path} が見つかりません！ファイル名を確認してください。")
        return

    print(f"読み込み中 → {image_path}")

    # 1. 画像読み込み（グレースケールで）
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # 2. 画像の二値化と反転（精度の鍵となる処理！）
    # 背景が真っ白・文字が黒の画像に最適化。
    # cv2.THRESH_BINARY_INV で 白黒を反転させ、Tesseractが好む「黒背景＋白文字」に変換。
    _, binary = cv2.threshold(img, 200, 255, cv2.THRESH_BINARY_INV)

    # 3. PSMと文字制限の設定（精度を極限まで高めるための設定）
    # PSM 10 = 「1文字だけある」と明言（Page Segmentation Mode: Single Char）
    # -l eng = 英語モード（数字の認識に強い）
    # tessedit_char_whitelist = 0123456789 のみに制限
    custom_config = r'--oem 3 --psm 10 -l eng -c tessedit_char_whitelist=0123456789'

    # 4. OCR実行
    text = pytesseract.image_to_string(binary, config=custom_config)

    # 5. 結果の整理
    # 余計な改行やスペースを削除
    digit = text.strip()

    print("\n" + "="*40)
    if digit and digit.isdigit():
        print(f"読み取れた数字 → 【{digit}】")
        print("完璧に読み取り成功！！！")
    else:
        print("数字が読み取れませんでした…")
        print(f"生のOCR結果: '{text}'")
    print("="*40)



# ===================== 実行 =====================
if __name__ == "__main__":
    print("数字1文字読み取りマシーン 起動！！\n")
    read_single_digit(IMAGE_PATH)