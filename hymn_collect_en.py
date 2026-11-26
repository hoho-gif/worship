import re
import sys
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode


DRIVE_FOLDER_ID = "1BARDuH3SPRbd0nvwWwO-9nQ-opy-obfC"
PDF_NAME_PATTERN = re.compile(r"^(?P<date>\d{8})_reihai_somgs_eng\.pdf$", re.IGNORECASE)
START_DATE = "20261122"
RENDER_DPI = 300
JPEG_QUALITY = 100
REQUEST_TIMEOUT = 30

BASE_FOLDER = Path(__file__).resolve().parent
SONG1_FOLDER = BASE_FOLDER / "song1"
SONG2_FOLDER = BASE_FOLDER / "song2"


class DriveFolderParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current_file_id = None
        self.title_file_id = None
        self.title_parts = []
        self.entries = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "div":
            entry_id = attributes.get("id", "")
            if entry_id.startswith("entry-"):
                self.current_file_id = entry_id.removeprefix("entry-")

            classes = attributes.get("class", "").split()
            if "flip-entry-title" in classes and self.current_file_id:
                self.title_file_id = self.current_file_id
                self.title_parts = []

    def handle_data(self, data):
        if self.title_file_id:
            self.title_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "div" and self.title_file_id:
            title = "".join(self.title_parts).strip()
            if title:
                self.entries.append((title, self.title_file_id))
            self.title_file_id = None
            self.title_parts = []


def load_folder_entries(opener):
    url = "https://drive.google.com/embeddedfolderview?" + urlencode(
        {"id": DRIVE_FOLDER_ID}
    ) + "#list"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with opener.open(request, timeout=REQUEST_TIMEOUT) as response:
        page = response.read().decode("utf-8", errors="replace")

    parser = DriveFolderParser()
    parser.feed(page)
    return parser.entries


def download_pdf(opener, file_id):
    params = {"export": "download", "id": file_id}
    url = "https://drive.google.com/uc?" + urlencode(params)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with opener.open(request, timeout=REQUEST_TIMEOUT) as response:
        content = response.read()

    if content.startswith(b"%PDF"):
        return content

    page = content.decode("utf-8", errors="replace")
    confirmation = re.search(r"confirm=([0-9A-Za-z_-]+)", page)
    if confirmation:
        params["confirm"] = confirmation.group(1)
        url = "https://drive.google.com/uc?" + urlencode(params)
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with opener.open(request, timeout=REQUEST_TIMEOUT) as response:
            content = response.read()

    if not content.startswith(b"%PDF"):
        raise ValueError(
            "Google DriveからPDFを取得できませんでした。共有設定とファイルを確認してください。"
        )
    return content


def render_page_half(page, left_side, pymupdf, image_module):
    rect = page.rect
    midpoint = (rect.x0 + rect.x1) / 2
    clip = (
        pymupdf.Rect(rect.x0, rect.y0, midpoint, rect.y1)
        if left_side
        else pymupdf.Rect(midpoint, rect.y0, rect.x1, rect.y1)
    )
    pixmap = page.get_pixmap(
        matrix=pymupdf.Matrix(RENDER_DPI / 72, RENDER_DPI / 72),
        clip=clip,
        colorspace=pymupdf.csRGB,
        alpha=False,
    )
    return image_module.frombytes(
        "RGB",
        (pixmap.width, pixmap.height),
        pixmap.samples,
    )


def convert_pdf(pdf_data, song1_path, song2_path, pymupdf, image_module):
    document = pymupdf.open(stream=pdf_data, filetype="pdf")
    try:
        if not len(document):
            raise ValueError("PDFにページがありません。")

        page = document[0]
        left_image = render_page_half(page, True, pymupdf, image_module)
        right_image = render_page_half(page, False, pymupdf, image_module)
    finally:
        document.close()

    try:
        left_image.save(
            song1_path,
            "JPEG",
            quality=JPEG_QUALITY,
            subsampling=0,
            dpi=(RENDER_DPI, RENDER_DPI),
        )
        right_image.save(
            song2_path,
            "JPEG",
            quality=JPEG_QUALITY,
            subsampling=0,
            dpi=(RENDER_DPI, RENDER_DPI),
        )
    finally:
        left_image.close()
        right_image.close()


def select_pdfs(entries, start_date):
    pdfs = []
    for name, file_id in entries:
        match = PDF_NAME_PATTERN.fullmatch(name)
        if not match:
            continue
        try:
            file_date = datetime.strptime(match.group("date"), "%Y%m%d").date()
        except ValueError:
            print(f"日付が不正なためスキップします: {name}", file=sys.stderr)
            continue
        if file_date >= start_date:
            pdfs.append((name, file_id, file_date.strftime("%Y-%m-%d")))

    return sorted(pdfs, key=lambda pdf: pdf[2])


def main():
    if not re.fullmatch(r"\d{8}", START_DATE):
        print("START_DATEはYYYYMMDD形式で指定してください。", file=sys.stderr)
        return 1
    try:
        start_date = datetime.strptime(START_DATE, "%Y%m%d").date()
    except ValueError:
        print(f"START_DATEの日付が不正です: {START_DATE}", file=sys.stderr)
        return 1

    try:
        import pymupdf
        from PIL import Image
    except ImportError as error:
        print(
            "PDF変換に必要なライブラリがありません。"
            " `python -m pip install PyMuPDF Pillow` を実行してください。",
            file=sys.stderr,
        )
        return 1

    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(CookieJar())
    )
    try:
        entries = load_folder_entries(opener)
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError) as error:
        print(f"Google Driveフォルダーを読み込めませんでした: {error}", file=sys.stderr)
        return 1

    pdfs = select_pdfs(entries, start_date)

    if not pdfs:
        print("対象のPDFがGoogle Driveフォルダーに見つかりませんでした。")
        return 1

    SONG1_FOLDER.mkdir(parents=True, exist_ok=True)
    SONG2_FOLDER.mkdir(parents=True, exist_ok=True)
    failures = 0

    for name, file_id, date_string in pdfs:
        song1_path = SONG1_FOLDER / f"{date_string}_en.jpg"
        song2_path = SONG2_FOLDER / f"{date_string}_en.jpg"
        try:
            pdf_data = download_pdf(opener, file_id)
            convert_pdf(pdf_data, song1_path, song2_path, pymupdf, Image)
        except (
            HTTPError,
            URLError,
            TimeoutError,
            OSError,
            ValueError,
            pymupdf.FileDataError,
        ) as error:
            failures += 1
            print(f"処理に失敗しました: {name}: {error}", file=sys.stderr)
            continue

        print(f"処理完了: {name}")
        print(f"  左半分（詩編）: {song1_path}")
        print(f"  右半分（讃美歌）: {song2_path}")

    if failures:
        print(f"{failures}件のPDFを処理できませんでした。", file=sys.stderr)
        return 1

    print(f"\n{len(pdfs)}件のPDFの処理が完了しました。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())