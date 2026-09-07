from pdf2image import convert_from_path
import pytesseract

# ここにあなたがPopplerを置いた場所を書く（例）
poppler_path = r"C:\tools\poppler-24.07.0\Library\bin"

# テスト用のPDF（デスクトップとかに置いたやつでOK）
pdf_path = r"C:\Users\hsksn\OneDrive\画像\仕事(イザヤ)\WebChange\教会式次第\psalmSong\output_pages\psalm1.pdf"

images = convert_from_path(pdf_path, poppler_path=poppler_path)
print(f"変換成功！{len(images)}ページあります")

for i, image in enumerate(images):
    text = pytesseract.image_to_string(image, lang='jpn')  # 日本語ならjpn
    print(f"\n--- {i+1}ページ目 ---\n{text}")