<?php
// --- 必要ライブラリ読み込み ---
require __DIR__ . '/vendor/autoload.php';

use Mpdf\Mpdf;
use setasign\Fpdi\Fpdi;

// --------- 設定ここから ----------
$BASE_PDFS = [
    __DIR__ . '/base_order1.pdf',
    __DIR__ . '/base_order2.pdf',
    __DIR__ . '/base_order3.pdf'
];
$SONGBOOK_PDFS = [
    "psalter" => __DIR__ . "/songs1.pdf",   // 詩篇歌集
    "hymnal"  => __DIR__ . "/songs2.pdf"    // 通常の讃美歌
];
$READINGS_JSON  = __DIR__ . '/readings.json';

// 出力先（Web 公開フォルダ）
$OUTPUT_PDF = __DIR__ . '/../public_html/order_of_worship_latest.pdf';
// ---------------------------------

// 1) 今週の日曜日を計算（日本時間）
$today  = new DateTime('now', new DateTimeZone('Asia/Tokyo'));
$weekday = (int)$today->format('w'); // 0=日曜
if ($weekday === 0) {
    $sunday = clone $today;
} else {
    $sunday = (clone $today)->modify('next sunday');
}
$dateKey = $sunday->format('Y-m-d');

// 2) JSON 読み込み
$data = json_decode(file_get_contents($READINGS_JSON), true);
if (!isset($data[$dateKey])) {
    die("この日付の朗読データがありません: $dateKey\n");
}
$info = $data[$dateKey];

// 3) mPDF で「朗読PDF」作成
$tmpReadings = __DIR__ . '/tmp_readings.pdf';
$mpdf = new Mpdf([
    'mode' => 'utf-8',
    'format' => 'A4',
]);

$html = '<h2>本日の聖書朗読</h2>';

$html .= '<h3>旧約聖書朗読</h3>';
$html .= '<p><strong>' . htmlspecialchars($info['ot']['ref']) . '</strong></p>';
$html .= '<p>' . nl2br(htmlspecialchars($info['ot']['text'])) . '</p>';

$html .= '<h3>詩篇朗読</h3>';
$html .= '<p><strong>' . htmlspecialchars($info['psalm']['ref']) . '</strong></p>';
$html .= '<p>' . nl2br(htmlspecialchars($info['psalm']['text'])) . '</p>';

$html .= '<h3>使徒書朗読</h3>';
$html .= '<p><strong>' . htmlspecialchars($info['epistle']['ref']) . '</strong></p>';
$html .= '<p>' . nl2br(htmlspecialchars($info['epistle']['text'])) . '</p>';

$html .= '<h3>福音書朗読</h3>';
$html .= '<p><strong>' . htmlspecialchars($info['gospel']['ref']) . '</strong></p>';
$html .= '<p>' . nl2br(htmlspecialchars($info['gospel']['text'])) . '</p>';

$mpdf->WriteHTML($html);
$mpdf->Output($tmpReadings, \Mpdf\Output\Destination::FILE);

// 4) FPDI で PDF を結合
$pdf = new Fpdi();

// 4a) 式文PDF（固定部分 3ファイル）
foreach ($BASE_PDFS as $basePdf) {
    $pageCount = $pdf->setSourceFile($basePdf);
    for ($pageNo = 1; $pageNo <= $pageCount; $pageNo++) {
        $tplId = $pdf->importPage($pageNo);
        $size = $pdf->getTemplateSize($tplId);
        $pdf->AddPage($size['orientation'], [$size['width'], $size['height']]);
        $pdf->useTemplate($tplId);
    }
}

// 4b) 朗読PDFを追加
$readPageCount = $pdf->setSourceFile($tmpReadings);
for ($pageNo = 1; $pageNo <= $readPageCount; $pageNo++) {
    $tplId = $pdf->importPage($pageNo);
    $size = $pdf->getTemplateSize($tplId);
    $pdf->AddPage($size['orientation'], [$size['width'], $size['height']]);
    $pdf->useTemplate($tplId);
}

// 4c) 賛美歌PDF（必要ページだけ追加）
$songPageCount = $pdf->setSourceFile($SONGBOOK_PDF);
foreach ($info['songs'] as $song) {

    // JSON の "book" に従ってPDFを選択
    $book = $song['book'];     // "psalter" or "hymnal"
    $pageNo = (int)$song['num'];

    if (!isset($SONGBOOK_PDFS[$book])) continue;

    $songPdf = $SONGBOOK_PDFS[$book];

    $songPageCount = $pdf->setSourceFile($songPdf);

    if ($pageNo < 1 || $pageNo > $songPageCount) continue;

    $tplId = $pdf->importPage($pageNo);
    $size = $pdf->getTemplateSize($tplId);
    $pdf->AddPage($size['orientation'], [$size['width'], $size['height']]);
    $pdf->useTemplate($tplId);
}

// 5) 最終PDFを保存（Web公開フォルダへ）
$pdf->Output($OUTPUT_PDF, 'F');

echo "礼拝式文PDFを生成しました: $dateKey\n";
