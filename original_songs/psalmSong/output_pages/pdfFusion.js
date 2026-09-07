const fs = require('fs');
const path = require('path');
const { PDFDocument } = require('pdf-lib');

(async () => {
  try {
    // output_pages フォルダ内のPDFを順番に指定
    const inputFiles = [
      'psalm5B.pdf',
      'psalm5B(2).pdf',
    ];

    // output_pages フォルダのパス
    const inputFolder = path.join(__dirname, 'output_pages');

    // 出力先PDF（psalmSong フォルダに作る）
    const outputPath = path.join(__dirname, 'merged_psalms.pdf');

    const mergedPdf = await PDFDocument.create();

    for (const file of inputFiles) {
      const filePath = path.join(inputFolder, file); // フォルダ付きパス
      const pdfBytes = fs.readFileSync(filePath);
      const pdfDoc = await PDFDocument.load(pdfBytes);

      const pages = await mergedPdf.copyPages(pdfDoc, pdfDoc.getPageIndices());
      pages.forEach(page => mergedPdf.addPage(page));
      console.log(`Added: ${file}`);
    }

    const mergedPdfBytes = await mergedPdf.save();
    fs.writeFileSync(outputPath, mergedPdfBytes);

    console.log(`Merged PDF saved as: ${outputPath}`);
  } catch (err) {
    console.error('Error:', err);
  }
})();
