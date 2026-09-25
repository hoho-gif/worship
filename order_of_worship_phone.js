/* ==========================================================================
   order_of_worship_phone.js
   その週の日曜日の日付から、賛美の楽譜画像と聖書朗読箇所をまとめて
   自動で読み込んで表示する。あわせて、右上の文字サイズ切り替え
   （小・標準・大）も扱う。

   ファイルの置き場所（このルールに合わせてください）:
    日本語: song1/YYYY-MM-DD.jpg / song1/YYYY-MM-DD.txt
    英語:   song1/YYYY-MM-DD_en.jpg / song1/YYYY-MM-DD_en.txt
    （song2 も同じ規則）

    日本語: read1/YYYY-MM-DD.html または read1/YYYY-MM-DD.txt
    英語:   read1/YYYY-MM-DD_en.html または read1/YYYY-MM-DD_en.txt
    （read2〜read4 も同じ規則）

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

  /** 英語ページではファイル名に "_en" を付ける */
  function getLanguageSuffix() {
    var language = document.documentElement.lang.toLowerCase();
    var pageName = window.location.pathname.split("/").pop().toLowerCase();
    return language === "en" || pageName === "order_of_worship_en.html" ? "_en" : "";
  }

  /* ---------- 賛美の楽譜画像 ---------- */

  function setSongImages(dateStr) {
    var song1 = document.getElementById("song1-img");
    var song2 = document.getElementById("song2-img");
    var suffix = getLanguageSuffix();

    if (song1) {
      song1.src = "song1/" + dateStr + suffix + ".jpg";
    }
    if (song2) {
      song2.src = "song2/" + dateStr + suffix + ".jpg";
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
    var suffix = getLanguageSuffix();

    songs.forEach(function (item) {
      var el = document.getElementById(item.elementId);
      if (!el) return;

      var url = item.folder + "/" + dateStr + suffix + ".txt";
      tryFetchText(url).then(function (text) {
        if (text === null) return; // 見つからなければ何もしない
        el.textContent = text;
      });
    });
  }

  /* ---------- 聖書朗読箇所 ---------- */

  /** 英語は .html のみ、日本語は .html を優先して .txt にフォールバックする */
  function loadReading(folder, dateStr) {
    var suffix = getLanguageSuffix();
    var htmlUrl = folder + "/" + dateStr + suffix + ".html";
    var txtUrl = folder + "/" + dateStr + suffix + ".txt";

    return tryFetchText(htmlUrl).then(function (htmlContent) {
      if (htmlContent !== null) {
        return { type: "html", content: htmlContent };
      }
      if (suffix === "_en") {
        return null;
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

  /* ---------- 言語切り替え ---------- */

  /**
   * 現在、画面の一番上に表示されているセクションのidを返す。
   * まだ最初のセクションより上（表紙・目次あたり）にいる場合はnullを返す。
   */
  function getCurrentSectionId() {
    var sections = document.querySelectorAll(".order-section[id]");
    var headerOffset = 80; // 上部固定要素（文字サイズ切り替えなど）を考慮した余白
    var currentId = null;

    sections.forEach(function (section) {
      var rect = section.getBoundingClientRect();
      if (rect.top - headerOffset <= 0) {
        currentId = section.id;
      }
    });

    return currentId;
  }

  function initLanguageToggle() {
    var links = document.querySelectorAll(".language-toggle a");

    links.forEach(function (link) {
      link.addEventListener("click", function (event) {
        var target = link.getAttribute("href");
        if (!target) return;

        // 既にURLに#セクションIDが付いていればそれを優先し、
        // 無ければ今スクロールしている位置から現在のセクションを判定する
        var hash = window.location.hash || (function () {
          var id = getCurrentSectionId();
          return id ? "#" + id : "";
        })();

        if (!hash) return; // トップ付近ならそのまま通常のリンク遷移

        event.preventDefault();
        window.location.href = target + hash;
      });
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
    initLanguageToggle();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();