import os
import sys
from pypdf import PdfReader, PdfWriter


def merge_pdfs(input_files, output_file="merged.pdf"):
    """
    複数のPDFファイルを1つに結合する
    
    Args:
        input_files: 結合したいPDFファイルのリスト
        output_file: 出力ファイル名
    """
    
    print(f"=== PDF結合開始 ===")
    print(f"出力ファイル: {output_file}")
    print()
    
    # 結合用のWriterを作成
    writer = PdfWriter()
    total_pages = 0
    
    # 各PDFを順番に追加
    for i, pdf_file in enumerate(input_files, 1):
        if not os.path.isfile(pdf_file):
            print(f"  [警告] ファイルが見つかりません: {pdf_file} (スキップ)")
            continue
        
        try:
            reader = PdfReader(pdf_file)
            page_count = len(reader.pages)
            
            # 全ページを追加
            for page in reader.pages:
                writer.add_page(page)
            
            total_pages += page_count
            print(f"  ✓ {i}. {os.path.basename(pdf_file)} ({page_count}ページ)")
            
        except Exception as e:
            print(f"  [エラー] {pdf_file} の読み込み失敗: {e}")
            continue
    
    # ファイルが1つも追加されなかった場合
    if total_pages == 0:
        print("\n結合するPDFがありませんでした。")
        return
    
    # 結合したPDFを保存
    try:
        with open(output_file, "wb") as f:
            writer.write(f)
        
        print()
        print(f"=== 完了 ===")
        print(f"結合ファイル数: {len(input_files)}")
        print(f"総ページ数: {total_pages}")
        print(f"保存先: {os.path.abspath(output_file)}")
        
    except Exception as e:
        print(f"\n[エラー] ファイルの保存に失敗: {e}")


# ===================================
# 使い方
# ===================================
if __name__ == "__main__":
    
    # コマンドライン引数で使う場合
    if len(sys.argv) > 1:
        # 引数の解析
        input_files = []
        output_file = "merged.pdf"
        
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == "-o" and i + 1 < len(sys.argv):
                output_file = sys.argv[i + 1]
                i += 2
            else:
                input_files.append(sys.argv[i])
                i += 1
        
        if not input_files:
            print("使い方:")
            print(f"  python {sys.argv[0]} file1.pdf file2.pdf file3.pdf -o output.pdf")
            print(f"  python {sys.argv[0]} hymn_*.pdf -o all_hymns.pdf")
            sys.exit(1)
        
        merge_pdfs(input_files, output_file)
    
    else:
        # コード内で直接指定する場合
        INPUT_FILES = [
            "hymn_97.pdf",
            "hymn_97,1.pdf",
        ]
        OUTPUT_FILE = "merged_hymns.pdf"
        
        merge_pdfs(INPUT_FILES, OUTPUT_FILE)
        
        print("\n💡 コマンドラインでの使い方:")
        print(f"  python {os.path.basename(__file__)} file1.pdf file2.pdf -o output.pdf")
        print(f"  例: python {os.path.basename(__file__)} hymn_*.pdf -o all_hymns.pdf")