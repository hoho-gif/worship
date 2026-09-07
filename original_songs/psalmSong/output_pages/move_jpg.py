from pathlib import Path
import shutil

# このプログラムが置かれているフォルダ
folder = Path(__file__).parent

# JPGを移動するフォルダ
output_folder = folder / "jpg_output"

# jpg_outputフォルダがなければ作成
output_folder.mkdir(exist_ok=True)

# 現在のフォルダにあるJPGファイルを取得
jpg_files = list(folder.glob("*.jpg")) + list(folder.glob("*.JPG"))

if not jpg_files:
    print("JPGファイルが見つかりませんでした。")
    exit()

print(f"{len(jpg_files)}個のJPGファイルを移動します。\n")

# JPGファイルを移動
for jpg_file in jpg_files:

    destination = output_folder / jpg_file.name

    shutil.move(jpg_file, destination)

    print(f"移動: {jpg_file.name}")

print("\nすべてのJPGファイルを移動しました！")