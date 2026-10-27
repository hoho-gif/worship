import os
import cv2
import fitz  # PyMuPDF
import numpy as np

# ============================================================
# 設定(ここを書き換えてください)
# ============================================================
INPUT_PDF = "psalm_en1-150.pdf"          # 処理したいPDFファイル名
OUTPUT_PDF = "psalm1-150_en.pdf"   # 出力ファイル名
DPI = 300           # 解像度。細い線が切れる場合は400に上げる
WHITE_POINT = 0.88  # 背景が残る→下げる(0.80) / 線が薄い→上げる(0.93)

# --- 黒の強調設定 ---
BLACK_MODE = "soft"  # "soft"=滑らかな黒(推奨) / "binary"=完全な白黒2値
BLACK_POINT = 120    # この明るさ以下は真っ黒(0)になる。文字が薄い→上げる(150)
SOFT_WHITE = 200     # この明るさ以上は真っ白(255)。BLACK_POINT〜SOFT_WHITE間は滑らかに変化
BINARY_THRESHOLD = 170  # BLACK_MODE="binary" のときの境目
# ============================================================


def whiten_background(gray: np.ndarray, dpi: int, white_point: float) -> np.ndarray:
    """グレー画像の背景を白にする。"""
    k = max(3, int(dpi / 200 * 15)) | 1
    bg = cv2.dilate(gray, np.ones((k, k), np.uint8))
    bg = cv2.medianBlur(bg, max(3, int(dpi / 200 * 21)) | 1)
    bg = cv2.GaussianBlur(bg, (0, 0), dpi / 200 * 10)

    norm = gray.astype(np.float32) / np.maximum(bg.astype(np.float32), 1) * 255
    norm = np.clip(norm, 0, 255)

    wp = 255 * white_point
    return np.clip(norm / wp * 255, 0, 255).astype(np.uint8)


def blacken_text(img: np.ndarray) -> np.ndarray:
    """文字・五線・音符を真っ黒にし、背景は白のままにする。"""
    if BLACK_MODE == "binary":
        # 完全な白黒2値(くっきり。細線はやや荒れる)
        return cv2.threshold(img, BINARY_THRESHOLD, 255, cv2.THRESH_BINARY)[1]

    # soft: BLACK_POINT以下→0、SOFT_WHITE以上→255、間は線形に補間
    x = img.astype(np.float32)
    out = (x - BLACK_POINT) / max(SOFT_WHITE - BLACK_POINT, 1) * 255
    return np.clip(out, 0, 255).astype(np.uint8)


def process_pdf(src: str, dst: str, dpi: int, white_point: float):
    if not os.path.exists(src):
        raise FileNotFoundError(f"PDFが見つかりません: {src}")

    doc = fitz.open(src)
    total = len(doc)
    out_doc = fitz.open()
    print(f"入力: {src} ({total}ページ)")

    for i in range(total):
        page = doc[i]

        # ページをグレースケール画像にレンダリング
        pix = page.get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
        gray = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w)

        white = whiten_background(gray, dpi, white_point)  # 背景を白に
        result = blacken_text(white)                       # 文字を真っ黒に

        # 元のページサイズを維持して新しいPDFに貼り付け
        ok, png = cv2.imencode(".png", result)
        new_page = out_doc.new_page(width=page.rect.width, height=page.rect.height)
        new_page.insert_image(new_page.rect, stream=png.tobytes())

        # メモリ解放
        del pix, gray, white, result, png

        print(f"\r処理中: {i + 1}/{total} ページ", end="", flush=True)

    print()
    out_doc.save(dst, deflate=True, garbage=3)
    out_doc.close()
    doc.close()
    print(f"保存しました: {dst}")


if __name__ == "__main__":
    process_pdf(INPUT_PDF, OUTPUT_PDF, DPI, WHITE_POINT)