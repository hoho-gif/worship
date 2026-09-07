# 必要なライブラリをインポート
from PIL import Image
import pytesseract

# 画像を開く
image = Image.open("cropped_image.png")

# 画像から文字を読み取る（数字のみに限定する設定例）
# configで数字だけ(digits)を対象にするよう指定すると精度が上がります
text = pytesseract.image_to_string(image, config="--psm 6 outputbase digits")

print(text)
# 出力例: 12345
