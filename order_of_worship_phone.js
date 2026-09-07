/* ==========================================================================
   order_of_worship_phone.js
   その週の日曜日の日付から、賛美の楽譜画像と聖書朗読箇所をまとめて
   自動で読み込んで表示する。あわせて、右上の文字サイズ切り替え
   （小・標準・大）も扱う。

   ファイルの置き場所（このルールに合わせてください）:
     song1/YYYY-MM-DD.jpg … 賛美［１］の楽譜
     song1/YYYY-MM-DD.txt … 賛美［１］の何番・何節などの情報（任意）
     song2/YYYY-MM-DD.jpg … 賛美［２］の楽譜
     song2/YYYY-MM-DD.txt … 賛美［２］の何番・何節などの情報（任意）

     read1/YYYY-MM-DD.html または read1/YYYY-MM-DD.txt … 旧約聖書からの朗読
     read2/YYYY-MM-DD.html または read2/YYYY-MM-DD.txt … 詩篇からの交読
     read3/YYYY-MM-DD.html または read3/YYYY-MM-DD.txt … 使徒書からの朗読
     read4/YYYY-MM-DD.html または read4/YYYY-MM-DD.txt … 福音書からの朗読

   朗読は .html を優先して探し、無ければ同じ日付の .txt を探します
   （.txt の場合、改行はそのまま改行として表示されます）。
   どちらも無い場合は、元のプレースホルダーの文言のままにします。

   ※ ブラウザで直接ファイルを開く（file://）と、朗読部分の fetch が
   　 ブロックされることがあります。ローカルサーバー経由（http://...）
   　 で開いてください（楽譜画像の読み込みは file:// でも動作します）。
   ========================================================================== */

(function () {
  "use strict";

  var READING_FOLDERS = [
    { folder: "read1", elementId: "read1-content" }, // 旧約聖書からの朗読
    { folder: "read2", elementId: "read2-content" }, // 詩篇からの交読
    { folder: "read3", elementId: "read3-content" }, // 使徒書からの朗読
    { folder: "read4", elementId: "read4-content" }  // 福音書からの朗読
  ];

  /**
   * 「今日」を基準に、直近の日曜日の日付を返す。
   * 今日が日曜日ならその日、それ以外の曜日なら直前に過ぎた日曜日を返す。
   */
  function getUpcomingSunday(baseDate) {
    var date = new Date(baseDate.getTime());
    var day = date.getDay(); // 0 = 日曜, 1 = 月曜, ... 6 = 土曜
    date.setDate(date.getDate() - day);
    return date;
  }

  /** Dateオブジェクトを "YYYY-MM-DD" 形式の文字列に変換する */
  function formatDate(date) {
    var yyyy = date.getFullYear();
    var mm = String(date.getMonth() + 1).padStart(2, "0");
    var dd = String(date.getDate()).padStart(2, "0");
    return yyyy + "-" + mm + "-" + dd;
  }

  /* ---------- 賛美の楽譜画像 ---------- */

  function setSongImages(dateStr) {
    var song1 = document.getElementById("song1-img");
    var song2 = document.getElementById("song2-img");

    if (song1) {
      song1.src = "song1/" + dateStr + ".jpg";
    }
    if (song2) {
      song2.src = "song2/" + dateStr + ".jpg";
    }
  }

  /** 指定したURLを取得し、成功したらテキストを返す。失敗したらnullを返す */
  function tryFetchText(url) {
    return fetch(url, { cache: "no-store" })
      .then(function (res) {
        if (!res.ok) return null;
        return res.text();
      })
      .catch(function () {
        return null;
      });
  }

  /**
   * 賛美の「何番・何節」などの情報を、同じ日付の song1/song2 フォルダの
   * .txt ファイルから読み込んで、画像の直前の要素に差し込む。
   * ファイルが無い場合は何もしない（元のプレースホルダーは空のまま）。
   */
  function setSongInfo(dateStr) {
    var songs = [
      { folder: "song1", elementId: "song1-info" },
      { folder: "song2", elementId: "song2-info" }
    ];

    songs.forEach(function (item) {
      var el = document.getElementById(item.elementId);
      if (!el) return;

      var url = item.folder + "/" + dateStr + ".txt";
      tryFetchText(url).then(function (text) {
        if (text === null) return; // 見つからなければ何もしない
        el.textContent = text;
      });
    });
  }

  /* ---------- 聖書朗読箇所 ---------- */

  /** .html を優先して探し、無ければ .txt を探す */
  function loadReading(folder, dateStr) {
    var htmlUrl = folder + "/" + dateStr + ".html";
    var txtUrl = folder + "/" + dateStr + ".txt";

    return tryFetchText(htmlUrl).then(function (htmlContent) {
      if (htmlContent !== null) {
        return { type: "html", content: htmlContent };
      }
      return tryFetchText(txtUrl).then(function (txtContent) {
        if (txtContent !== null) {
          return { type: "txt", content: txtContent };
        }
        return null; // どちらも見つからなかった
      });
    });
  }

  function setReadings(dateStr) {
    READING_FOLDERS.forEach(function (item) {
      var el = document.getElementById(item.elementId);
      if (!el) return;

      loadReading(item.folder, dateStr).then(function (result) {
        if (!result) return; // 見つからなければ元の文言のまま
        if (result.type === "html") {
          el.innerHTML = result.content;
        } else {
          el.textContent = result.content;
        }
      });
    });
  }

  /* ---------- 文字サイズ切り替え（小・標準・大） ---------- */

  var FONT_SIZE_STORAGE_KEY = "orderOfWorshipFontSize";
  var FONT_SIZE_CLASSES = {
    small: "font-size-small",
    standard: "", // 標準はクラス無し（デフォルト）
    large: "font-size-large"
  };

  function applyFontSize(size) {
    var html = document.documentElement;
    html.classList.remove("font-size-small", "font-size-large");
    var cls = FONT_SIZE_CLASSES[size];
    if (cls) {
      html.classList.add(cls);
    }

    var buttons = document.querySelectorAll(".font-size-toggle button");
    buttons.forEach(function (btn) {
      if (btn.getAttribute("data-size") === size) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });
  }

  function initFontSizeToggle() {
    var toggle = document.getElementById("font-size-toggle");
    if (!toggle) return;

    var savedSize = null;
    try {
      savedSize = localStorage.getItem(FONT_SIZE_STORAGE_KEY);
    } catch (e) {
      savedSize = null;
    }
    applyFontSize(savedSize && FONT_SIZE_CLASSES.hasOwnProperty(savedSize) ? savedSize : "standard");

    toggle.addEventListener("click", function (event) {
      var btn = event.target.closest("button[data-size]");
      if (!btn) return;
      var size = btn.getAttribute("data-size");
      applyFontSize(size);
      try {
        localStorage.setItem(FONT_SIZE_STORAGE_KEY, size);
      } catch (e) {
        /* localStorageが使えない環境では保存をあきらめる */
      }
    });
  }

  /* ---------- まとめて実行 ---------- */

  function setWeeklyContent() {
    var sunday = getUpcomingSunday(new Date());
    var dateStr = formatDate(sunday);

    setSongImages(dateStr);
    setSongInfo(dateStr);
    setReadings(dateStr);
  }

  function init() {
    setWeeklyContent();
    initFontSizeToggle();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();