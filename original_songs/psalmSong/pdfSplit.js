const fs = require('fs');
const path = require('path');
const { PDFDocument } = require('pdf-lib');

(async () => {
  try {
    // 元PDFのパス
    const inputPath = path.join(__dirname, 'psalm100-150.pdf');

    // 出力フォルダ
    const outputFolder = path.join(__dirname, 'output_pages');

    // フォルダがなければ作成
    if (!fs.existsSync(outputFolder)) {
      fs.mkdirSync(outputFolder);
      console.log(`Created folder: ${outputFolder}`);
    }

    // PDF 読み込み
    const pdfBytes = fs.readFileSync(inputPath);
    const pdfDoc = await PDFDocument.load(pdfBytes);

    console.log(`Total pages: ${pdfDoc.getPageCount()}`);

    // 1ページずつ分割して output_pages に保存
    for (let i = 0; i < pdfDoc.getPageCount(); i++) {
      const newPdf = await PDFDocument.create();
      const [copiedPage] = await newPdf.copyPages(pdfDoc, [i]);
      newPdf.addPage(copiedPage);

      const pdfBytesNew = await newPdf.save();
      const outputPath = path.join(outputFolder, `psalm${i+101}.pdf`);
      fs.writeFileSync(outputPath, pdfBytesNew);

      console.log(`Saved: ${outputPath}`);
    }

    console.log('All pages from psalm100-150.pdf have been split successfully!');

  } catch (err) {
    console.error('Error:', err);
  }
})();
