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

spreadsheet_url = "https://docs.google.com/spreadsheets/d/15zrUpKyzcz8PgqX7eBPxm0WnL_udhQ-Qy5A2PXBQ9v0/edit?usp=sharing"
spreadsheet_gid = "743073611"
start_row = 47

psalm_source_folder = "psalm_jpg"
hymn_source_folder = "hymn_jpg"

# 列番号は0から数える: Z列=25、AA列=26
collections = [
	(25, "song1", False),
	(26, "song2", True),
]


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
	match = re.match(r"^(\d{4})[-/.年](\d{1,2})(?:[-/.月])?(\d{1,2})日?", date_text)
	if match:
		try:
			return datetime(*(int(part) for part in match.groups())).strftime("%Y-%m-%d")
		except ValueError as error:
			raise ValueError(f"日付の値が不正です：{date_text}") from error

	for date_format in (
		"%Y-%m-%d",
		"%Y/%m/%d",
		"%Y.%m.%d",
		"%m/%d/%Y",
		"%m-%d-%y",
	):
		try:
			return datetime.strptime(date_text, date_format).strftime("%Y-%m-%d")
		except ValueError:
			continue

	raise ValueError(f"日付をYYYY-MM-DDに変換できません：{date_text}")


def extract_psalm_name(text):
	if not text:
		return ""

	text = str(text).strip()
	if text.startswith(("詩篇", "詩編")):
		text = text[2:]

	return text.split("(")[0].strip()


def extract_hymn_name(text):
	if not text:
		return ""

	text = str(text).strip()
	if text.startswith("聖歌"):
		text = text[2:]

	return text.split("(")[0].strip()


def normalize_for_match(text):
	return re.sub(r"\d+", lambda match: str(int(match.group())), text)


for _, destination_folder, _ in collections:
	os.makedirs(destination_folder, exist_ok=True)


try:
	sheet_rows = load_public_sheet_rows(
		spreadsheet_url,
		spreadsheet_gid,
		start_row,
	)
except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, csv.Error, ValueError) as error:
	print(f"公開スプレッドシートを読み込めません：{error}")
	print("URLと「リンクを知っている全員が閲覧可」の共有設定を確認してください。")
	input("Enterキーを押して終了...")
	raise SystemExit(1)


for row in sheet_rows:
	date_value = row[1] if len(row) > 1 else ""
	if not date_value:
		continue

	row_collections = [
		(row[column_index], destination_folder, ignore_leading_zeroes)
		for column_index, destination_folder, ignore_leading_zeroes in collections
		if len(row) > column_index and row[column_index]
	]
	if not row_collections:
		continue

	try:
		date_string = format_date_value(date_value)
	except ValueError as error:
		print(error)
		continue

	for cell_value, destination_folder, ignore_leading_zeroes in row_collections:
		cell_text = str(cell_value).strip()

		txt_file_path = os.path.join(destination_folder, f"{date_string}.txt")
		with open(txt_file_path, "w", encoding="utf-8") as txt_file:
			txt_file.write(cell_text)

		print("----------------------------------")
		print(f"TXTファイル作成：{txt_file_path}")
		print(f"  内容：{cell_text}")

		if cell_text.startswith(("詩篇", "詩編")):
			extracted_name = extract_psalm_name(cell_text)
			source_folder = psalm_source_folder
			search_name = "psalm" + extracted_name
			file_type = "詩篇"
		elif cell_text.startswith("聖歌"):
			extracted_name = extract_hymn_name(cell_text)
			source_folder = hymn_source_folder
			search_name = "hymn_" + extracted_name
			file_type = "聖歌"
		else:
			print(f"【種類不明】{cell_text}")
			continue

		if not extracted_name:
			print(f"{file_type}番号を抽出できませんでした：{cell_text}")
			continue

		final_name = f"{date_string}.jpg"
		print(f"日付          ：{date_string}")
		print(f"元のセル      ：{cell_text}")
		print(f"種類          ：{file_type}")
		print(f"抽出した番号  ：{extracted_name}")
		print(f"検索する名前  ：{search_name}")
		print(f"検索フォルダ  ：{source_folder}")
		print(f"新しい名前    ：{final_name}")

		found = False
		for root, _, files in os.walk(source_folder):
			for filename in files:
				name_without_extension = os.path.splitext(filename)[0]
				if ignore_leading_zeroes:
					matches = normalize_for_match(name_without_extension) == normalize_for_match(search_name)
				else:
					matches = name_without_extension == search_name

				if not matches:
					continue

				source_file = os.path.join(root, filename)
				destination_file = os.path.join(destination_folder, final_name)
				shutil.copy2(source_file, destination_file)
				print("コピー完了！")
				print(f"  元ファイル ：{source_file}")
				print(f"  新ファイル ：{destination_file}")
				found = True
				break

			if found:
				break

		if not found:
			print(f"【見つかりません】{search_name}")


print()
print("==========================================")
print("すべての処理が完了しました。")
print("==========================================")
input("Enterキーを押して終了...")
