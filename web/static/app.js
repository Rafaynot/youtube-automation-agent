// YouTube Agent Studio - Interactive Dashboard Logic
document.addEventListener("DOMContentLoaded", () => {
  initThemeToggle();
  initTabs();
  initMobileNavigation();
  loadChannelData();
  initHookScorer();
  initTitleLinter();
  initScriptWriter();
  initChapters();
  initVoiceEditor();
  initLinkModal();
  initStudioAnalytics();
  initAuditTab();
  initSeoTab();
  initShortsTab();
  initPlanTab();
  initCommentTab();
});

// ==========================================================================
// TOAST NOTIFICATION SYSTEM (YouTube Style Floating Toaster)
// ==========================================================================
function showToast(message, type = "info", duration = 3000) {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `yt-toast yt-toast-${type}`;

  const iconMap = {
    success: "fa-solid fa-circle-check",
    error: "fa-solid fa-circle-exclamation",
    warning: "fa-solid fa-triangle-exclamation",
    info: "fa-solid fa-circle-info"
  };
  const iconClass = iconMap[type] || iconMap.info;

  toast.innerHTML = `
    <i class="${iconClass} yt-toast-icon"></i>
    <span class="yt-toast-msg">${message}</span>
    <button class="yt-toast-close" aria-label="Dismiss">&times;</button>
  `;

  const closeBtn = toast.querySelector(".yt-toast-close");
  closeBtn.addEventListener("click", () => dismissToast(toast));

  container.appendChild(toast);

  // Trigger smooth slide-in
  requestAnimationFrame(() => {
    toast.classList.add("yt-toast-visible");
  });

  const timer = setTimeout(() => {
    dismissToast(toast);
  }, duration);

  function dismissToast(el) {
    clearTimeout(timer);
    el.classList.remove("yt-toast-visible");
    el.classList.add("yt-toast-hiding");
    setTimeout(() => {
      if (el.parentNode) el.parentNode.removeChild(el);
    }, 250);
  }
}

// 0. Official YouTube Light / Dark Theme Switcher
function initThemeToggle() {
  const toggleBtn = document.getElementById("btn-theme-toggle");
  const icon = document.getElementById("theme-toggle-icon");
  const text = document.getElementById("theme-toggle-text");

  function applyTheme(theme, isUserAction = false) {
    if (theme === "light") {
      document.body.classList.remove("dark-theme");
      document.body.classList.add("light-theme");
      if (icon) {
        icon.className = "fa-solid fa-sun";
        icon.style.color = "#d97706";
      }
      if (text) text.textContent = "Light";
      localStorage.setItem("yt_theme", "light");
      if (isUserAction) showToast("Switched to YouTube Light Theme", "info");
    } else {
      document.body.classList.remove("light-theme");
      document.body.classList.add("dark-theme");
      if (icon) {
        icon.className = "fa-solid fa-moon";
        icon.style.color = "";
      }
      if (text) text.textContent = "Dark";
      localStorage.setItem("yt_theme", "dark");
      if (isUserAction) showToast("Switched to YouTube Dark Theme", "info");
    }
  }

  // Load saved theme or default to dark
  const saved = localStorage.getItem("yt_theme") || "dark";
  applyTheme(saved, false);

  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      const isCurrentlyLight = document.body.classList.contains("light-theme");
      applyTheme(isCurrentlyLight ? "dark" : "light", true);
    });
  }
}

// 1. Tab Navigation & Mobile Synchronized Switching
const tabMeta = {
  "tab-channel": { title: "Channel Hub", desc: "Overview and content library for Fear Studio" },
  "tab-studio": { title: "Studio Analytics", desc: "Official YouTube Analytics API & private performance metrics" },
  "tab-audit": { title: "Channel Audit (yt-audit)", desc: "Packaging health, mobile cutoff & the ONE biggest fix this week" },
  "tab-hook": { title: "Hook Scorer (yt-script)", desc: "5-Property diagnostic & formula detection" },
  "tab-title": { title: "Title & Thumbnail (yt-package)", desc: "Dual desktop & mobile packaging inspector" },
  "tab-script": { title: "AI Script Studio (yt-script)", desc: "Spoken horror scripts with retention beats" },
  "tab-seo": { title: "SEO & Tags Studio (yt-seo)", desc: "Search snippet above the fold, query targets & focused tags" },
  "tab-shorts": { title: "Shorts Extractor (yt-shorts)", desc: "Repurpose premises into 3 viral vertical shorts" },
  "tab-chapters": { title: "Chapters & EDL (yt-chapters / yt-edit)", desc: "YouTube validated timestamps and cut lists" },
  "tab-plan": { title: "Content Calendar (yt-plan)", desc: "4-Week upload schedule sized to creator production hours" },
  "tab-comment": { title: "Comment Responder (yt-comment)", desc: "4-Pile comment triage and authentic voice replies" },
  "tab-voice": { title: "Voice Profile", desc: "Channel identity and tone guidelines (config/voice.md)" }
};

function switchTab(targetId) {
  const navButtons = document.querySelectorAll(".nav-item");
  const bottomNavButtons = document.querySelectorAll(".bottom-nav-item");
  const tabPanes = document.querySelectorAll(".tab-pane");
  const pageTitle = document.getElementById("page-title");
  const pageDesc = document.getElementById("page-desc");
  const contentArea = document.querySelector(".content-scrollable");

  // Deactivate all
  navButtons.forEach(b => b.classList.remove("active"));
  bottomNavButtons.forEach(b => b.classList.remove("active"));
  tabPanes.forEach(p => p.classList.remove("active"));

  // Activate matching sidebar nav item
  const activeSidebarBtn = document.querySelector(`.nav-item[data-tab="${targetId}"]`);
  if (activeSidebarBtn) activeSidebarBtn.classList.add("active");

  // Activate matching bottom nav item (if present)
  const activeBottomBtn = document.querySelector(`.bottom-nav-item[data-tab="${targetId}"]`);
  if (activeBottomBtn) activeBottomBtn.classList.add("active");

  // Activate tab pane
  const targetPane = document.getElementById(targetId);
  if (targetPane) targetPane.classList.add("active");

  // Update title & description
  if (tabMeta[targetId]) {
    if (pageTitle) pageTitle.textContent = tabMeta[targetId].title;
    if (pageDesc) pageDesc.textContent = tabMeta[targetId].desc;
  }

  // Close mobile drawer if open
  closeMobileDrawer();

  // Scroll to top
  if (contentArea) contentArea.scrollTop = 0;
}

function initTabs() {
  const navButtons = document.querySelectorAll(".nav-item");
  navButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-tab");
      switchTab(targetId);
    });
  });

  const bottomNavButtons = document.querySelectorAll(".bottom-nav-item[data-tab]");
  bottomNavButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-tab");
      switchTab(targetId);
    });
  });
}

// Mobile Slide-over Drawer & Bottom Navigation Controls
function closeMobileDrawer() {
  const sidebar = document.querySelector(".sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");
  sidebar?.classList.remove("drawer-open");
  backdrop?.classList.remove("active");
  document.body.classList.remove("drawer-no-scroll");
}

function openMobileDrawer() {
  const sidebar = document.querySelector(".sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");
  sidebar?.classList.add("drawer-open");
  backdrop?.classList.add("active");
  document.body.classList.add("drawer-no-scroll");
}

function initMobileNavigation() {
  const mobileMenuBtn = document.getElementById("btn-mobile-menu");
  const bottomNavMore = document.getElementById("bnav-more");
  const backdrop = document.getElementById("sidebar-backdrop");
  const sidebar = document.querySelector(".sidebar");

  mobileMenuBtn?.addEventListener("click", () => {
    if (sidebar?.classList.contains("drawer-open")) {
      closeMobileDrawer();
    } else {
      openMobileDrawer();
    }
  });

  bottomNavMore?.addEventListener("click", () => {
    openMobileDrawer();
  });

  backdrop?.addEventListener("click", () => {
    closeMobileDrawer();
  });
}

// 2. Channel Data Loading
let allChannelVideos = [];

async function loadChannelData() {
  try {
    const res = await fetch("/api/channel");
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("ch-name").textContent = data.name || "Channel";
    document.getElementById("ch-handle").textContent = data.handle || "";
    document.getElementById("hub-channel-name").textContent = data.name || "Channel";
    document.getElementById("hub-channel-desc").textContent = data.description || "No description set.";
    
    // Subscriber count & public video count
    const rawSubs = data.subscriber_count || "120 subscribers";
    const cleanSubs = rawSubs.replace(/subscribers?/i, "").trim();
    const subsEl = document.getElementById("hub-subscriber-count");
    if (subsEl) subsEl.textContent = cleanSubs || "120";

    const rawVideos = data.video_count_public || `${data.total_recent_videos || 9} videos`;
    const cleanVideos = rawVideos.replace(/videos?/i, "").trim();
    const vCountEl = document.getElementById("hub-video-count");
    if (vCountEl) vCountEl.textContent = cleanVideos || "39";

    if (data.url) {
      document.getElementById("hub-yt-link").href = data.url;
    }

    // Set official Avatar / PFP
    if (data.avatar) {
      const chAv = document.getElementById("ch-avatar");
      if (chAv) chAv.innerHTML = `<img src="${data.avatar}" alt="PFP" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">`;
      const heroAv = document.querySelector(".hero-avatar");
      if (heroAv) heroAv.innerHTML = `<img src="${data.avatar}" alt="PFP" style="width:100%;height:100%;border-radius:14px;object-fit:cover;">`;
      const studioAv = document.getElementById("studio-ch-avatar");
      if (studioAv) studioAv.innerHTML = `<img src="${data.avatar}" alt="PFP" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">`;
    }

    // Set official Banner
    if (data.banner) {
      const hero = document.querySelector(".channel-hero");
      if (hero) {
        hero.style.background = `linear-gradient(rgba(10, 12, 16, 0.78), rgba(18, 21, 28, 0.95)), url('${data.banner}') center/cover no-repeat`;
      }
    }

    allChannelVideos = data.recent_videos || [];
    renderVideos(allChannelVideos);
    initVideoFilters();
  } catch (err) {
    console.error("Failed to load channel:", err);
  }
}

function initVideoFilters() {
  const searchInput = document.getElementById("video-search-input");
  const sortSelect = document.getElementById("video-sort-select");

  function applyFilters() {
    let filtered = [...allChannelVideos];
    const q = (searchInput?.value || "").toLowerCase().trim();
    if (q) {
      filtered = filtered.filter(v => (v.title || "").toLowerCase().includes(q));
    }
    const sortVal = sortSelect?.value || "default";
    if (sortVal === "az") {
      filtered.sort((a, b) => (a.title || "").localeCompare(b.title || ""));
    } else if (sortVal === "za") {
      filtered.sort((a, b) => (b.title || "").localeCompare(a.title || ""));
    }
    renderVideos(filtered);
  }

  if (searchInput) searchInput.addEventListener("input", applyFilters);
  if (sortSelect) sortSelect.addEventListener("change", applyFilters);
}

function renderVideos(videos) {
  const container = document.getElementById("videos-container");
  container.innerHTML = "";

  if (!videos.length) {
    container.innerHTML = "<p class='sub-text' style='padding: 20px 0;'>No matching videos found.</p>";
    return;
  }

  videos.forEach((v, idx) => {
    const card = document.createElement("div");
    card.className = "video-card";
    const thumbUrl = v.thumbnail || `https://i.ytimg.com/vi/${v.videoId}/hqdefault.jpg`;
    card.innerHTML = `
      <div class="video-thumb-container">
        <img src="${thumbUrl}" alt="${escapeHtml(v.title)}" class="video-card-thumb-img" loading="lazy">
        <span class="video-card-badge">#${idx + 1}</span>
      </div>
      <div class="video-card-info">
        <div class="video-title" title="${escapeHtml(v.title)}">${escapeHtml(v.title)}</div>
        <div class="video-meta-label">${escapeHtml(v.label || '')}</div>
      </div>
      <div class="video-card-actions">
        <button class="btn btn-sm btn-secondary btn-score-title-quick" data-title="${escapeHtml(v.title)}">
          <i class="fa-solid fa-tag"></i> Lint Title
        </button>
        <button class="btn btn-sm btn-secondary btn-score-hook-quick" data-hook="${escapeHtml(v.title)}">
          <i class="fa-solid fa-bullseye"></i> Test Hook
        </button>
        <a href="${v.url}" target="_blank" class="btn btn-sm btn-secondary" title="Watch on YouTube">
          <i class="fa-brands fa-youtube" style="color: #ff0033;"></i>
        </a>
      </div>
    `;
    container.appendChild(card);
  });

  // Attach quick action listeners
  document.querySelectorAll(".btn-score-title-quick").forEach(b => {
    b.addEventListener("click", () => {
      const title = b.getAttribute("data-title");
      document.getElementById("nav-btn-title").click();
      document.getElementById("input-title").value = title;
      document.getElementById("btn-lint-title").click();
    });
  });

  document.querySelectorAll(".btn-score-hook-quick").forEach(b => {
    b.addEventListener("click", () => {
      const hook = b.getAttribute("data-hook");
      document.getElementById("nav-btn-hook").click();
      document.getElementById("hook-input").value = hook;
      document.getElementById("btn-score-hook").click();
    });
  });
}

// 3. Hook Scorer
function initHookScorer() {
  const input = document.getElementById("hook-input");
  const btn = document.getElementById("btn-score-hook");
  const results = document.getElementById("hook-results-panel");

  btn.addEventListener("click", async () => {
    const text = input.value.trim();
    if (!text) return;

    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Scoring...`;

    try {
      const res = await fetch("/api/hookscore", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: jsonBody({ hook: text })
      });
      const data = await res.json();
      displayHookResults(data);
    } catch (err) {
      showToast("Error scoring hook: " + err, "error");
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<i class="fa-solid fa-bolt"></i> Score Hook`;
    }
  });

  // Presets
  document.querySelectorAll(".preset-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      input.value = chip.getAttribute("data-hook");
      btn.click();
    });
  });
}

function displayHookResults(data) {
  const panel = document.getElementById("hook-results-panel");
  panel.classList.remove("hidden");

  document.getElementById("hook-verdict-num").textContent = data.verdict;
  const bandBadge = document.getElementById("hook-band-badge");
  bandBadge.textContent = data.band;
  bandBadge.className = "verdict-band band-" + data.band.toLowerCase();

  document.getElementById("hook-formula-name").textContent = data.formula;
  document.getElementById("hook-weakest-prop").textContent = data.weakest;
  document.getElementById("hook-fix-advice").textContent = data.fix || "Good balance across all 5 properties.";

  // Update progress bars
  const props = ["specificity", "address", "stakes", "curiosity", "brevity"];
  props.forEach(p => {
    const val = data.parts[p.toUpperCase()] || 0;
    const bar = document.getElementById(`bar-${p}`);
    const txt = document.getElementById(`val-${p}`);
    if (bar) bar.style.width = `${val}%`;
    if (txt) txt.textContent = `${val}/100`;
  });
}

// 4. Title & Thumbnail Linter
function initTitleLinter() {
  const inputTitle = document.getElementById("input-title");
  const inputThumb = document.getElementById("input-thumb");
  const btn = document.getElementById("btn-lint-title");
  const charCount = document.getElementById("title-char-count");
  const wordCount = document.getElementById("thumb-word-count");

  function updateCounters() {
    charCount.textContent = inputTitle.value.length;
    const words = inputThumb.value.trim().split(/\s+/).filter(Boolean);
    wordCount.textContent = words.length;

    // Live update simulator
    document.getElementById("sim-desktop-title").textContent = inputTitle.value || "Your Title Here";
    document.getElementById("sim-thumb-text").textContent = inputThumb.value.toUpperCase() || "THUMBNAIL";
    
    const cut = inputTitle.value.slice(0, 40);
    document.getElementById("sim-mobile-title").textContent = cut ? `"${cut}..."` : "--";
  }

  inputTitle.addEventListener("input", updateCounters);
  inputThumb.addEventListener("input", updateCounters);

  btn.addEventListener("click", async () => {
    const title = inputTitle.value.trim();
    if (!title) return;

    btn.disabled = true;
    try {
      const res = await fetch("/api/title", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: jsonBody({ title, thumb: inputThumb.value.trim() })
      });
      const data = await res.json();
      displayTitleResults(data);
    } catch (err) {
      showToast("Error linting title: " + err, "error");
    } finally {
      btn.disabled = false;
    }
  });
}

function displayTitleResults(data) {
  const panel = document.getElementById("title-results-panel");
  panel.classList.remove("hidden");

  document.getElementById("packaging-score").textContent = `${data.score}/100`;

  const issuesBox = document.getElementById("lint-issues-box");
  issuesBox.innerHTML = "";
  if (data.issues && data.issues.length) {
    data.issues.forEach(([kind, msg]) => {
      const div = document.createElement("div");
      div.className = "issue-item";
      div.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> <strong>${escapeHtml(kind)}:</strong> ${escapeHtml(msg)}`;
      issuesBox.appendChild(div);
    });
  }

  const goodsBox = document.getElementById("lint-goods-box");
  goodsBox.innerHTML = "";
  if (data.good && data.good.length) {
    data.good.forEach(msg => {
      const div = document.createElement("div");
      div.className = "good-item";
      div.innerHTML = `<i class="fa-solid fa-circle-check"></i> ${escapeHtml(msg)}`;
      goodsBox.appendChild(div);
    });
  }
}

// 5. Script Writer
function initScriptWriter() {
  const topic = document.getElementById("script-topic");
  const btn = document.getElementById("btn-generate-script");
  const resultBox = document.getElementById("script-result-box");
  const resultBody = document.getElementById("script-text-body");

  btn.addEventListener("click", async () => {
    const input = topic.value.trim();
    if (!input) {
      showToast("Please enter a video topic or idea first!", "warning");
      return;
    }

    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Assembling Script...`;

    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: jsonBody({ skill: "yt-script", input })
      });
      const data = await res.json();
      resultBox.classList.remove("hidden");

      if (data.mode === "ai") {
        resultBody.textContent = data.result;
      } else {
        resultBody.textContent = data.prompt;
      }
      showToast("Script generated successfully!", "success");
      resultBox.scrollIntoView({ behavior: "smooth" });
    } catch (err) {
      showToast("Failed to generate script: " + err, "error");
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<i class="fa-solid fa-scroll"></i> Generate Horror Script`;
    }
  });

  document.getElementById("btn-copy-script").addEventListener("click", () => {
    navigator.clipboard.writeText(resultBody.textContent);
    showToast("Script copied to clipboard!", "success");
  });
}

// 6. Chapters Generator
function initChapters() {
  const input = document.getElementById("transcript-input");
  const btn = document.getElementById("btn-gen-chapters");
  const box = document.getElementById("chapters-output-box");
  const text = document.getElementById("chapters-result-text");

  btn.addEventListener("click", async () => {
    const transcript = input.value.trim();
    if (!transcript) return;

    btn.disabled = true;
    try {
      const res = await fetch("/api/chapters", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: jsonBody({ transcript, target: 7 })
      });
      const data = await res.json();
      box.classList.remove("hidden");
      text.textContent = data.chapters || "Could not generate chapters from input.";
      showToast("Validated chapters generated!", "success");
    } catch (err) {
      showToast("Chapters Error: " + err, "error");
    } finally {
      btn.disabled = false;
    }
  });

  document.getElementById("btn-copy-chapters").addEventListener("click", () => {
    navigator.clipboard.writeText(text.textContent);
    showToast("Chapters copied to clipboard!", "success");
  });
}

// 7. Voice Profile Editor
async function initVoiceEditor() {
  const editor = document.getElementById("voice-editor");
  const btn = document.getElementById("btn-save-voice");

  try {
    const res = await fetch("/api/voice");
    const data = await res.json();
    editor.value = data.content || "";
  } catch (err) {
    console.error("Failed to load voice:", err);
  }

  btn.addEventListener("click", async () => {
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Saving...`;
    try {
      await fetch("/api/voice/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: jsonBody({ content: editor.value })
      });
      showToast("Voice profile saved successfully!", "success");
    } catch (err) {
      showToast("Save failed: " + err, "error");
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<i class="fa-solid fa-floppy-disk"></i> Save Changes`;
    }
  });
}

// 8. Re-link Channel Modal
function initLinkModal() {
  const modal = document.getElementById("modal-link");
  const btnOpen = document.getElementById("btn-relink-channel");
  const btnClose = document.getElementById("modal-close-btn");
  const btnCancel = document.getElementById("modal-cancel-btn");
  const btnSubmit = document.getElementById("modal-submit-link");
  const inputUrl = document.getElementById("modal-input-url");

  btnOpen.addEventListener("click", () => modal.classList.remove("hidden"));
  btnClose.addEventListener("click", () => modal.classList.add("hidden"));
  btnCancel.addEventListener("click", () => modal.classList.add("hidden"));

  btnSubmit.addEventListener("click", async () => {
    const url = inputUrl.value.trim();
    if (!url) return;

    btnSubmit.disabled = true;
    btnSubmit.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Fetching...`;

    try {
      const res = await fetch("/api/link", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: jsonBody({ url })
      });
      const data = await res.json();
      if (data.error) {
        showToast("Error: " + data.error, "error");
      } else {
        showToast(`Successfully linked: ${data.name}!`, "success");
        modal.classList.add("hidden");
        loadChannelData();
        initVoiceEditor();
      }
    } catch (err) {
      showToast("Link failed: " + err, "error");
    } finally {
      btnSubmit.disabled = false;
      btnSubmit.innerHTML = `<i class="fa-solid fa-link"></i> Link Channel Now`;
    }
  });
}

// 9. Official YouTube Studio Analytics Suite (OAuth 2.0)
let currentStudioDays = "28";

async function initStudioAnalytics() {
  const setupCard = document.getElementById("studio-setup-card");
  const connectedCard = document.getElementById("studio-connected-card");
  const statusBadge = document.getElementById("studio-status-badge");
  const btnSaveCreds = document.getElementById("btn-save-oauth-creds");
  const btnAuth = document.getElementById("btn-start-oauth-login");
  const btnRefresh = document.getElementById("btn-refresh-studio");
  const hubDateFilter = document.getElementById("hub-date-filter");
  const studioDatePills = document.querySelectorAll("#studio-date-pills .filter-pill");

  // Check current auth status
  async function checkStatus() {
    try {
      const res = await fetch("/api/studio/status");
      const data = await res.json();
      if (data.authenticated) {
        setupCard.classList.add("hidden");
        connectedCard.classList.remove("hidden");
        statusBadge.textContent = "CONNECTED";
        statusBadge.style.color = "var(--accent-green)";

        // Load complete Studio suite
        loadStudioOverview();
        loadAllStudioData(currentStudioDays);
      } else {
        setupCard.classList.remove("hidden");
        connectedCard.classList.add("hidden");
        statusBadge.textContent = data.has_credentials ? "READY TO LOGIN" : "NEEDS SETUP";
      }
    } catch (e) {
      console.error("Studio status check error:", e);
    }
  }

  // Load Channel Lifetime Overview (Subscriber Count, Total Videos, Lifetime Views & Hours)
  async function loadStudioOverview() {
    try {
      const res = await fetch("/api/studio/overview");
      if (!res.ok) return;
      const ov = await res.json();

      const subStr = ov.subscriber_count || "120 subscribers";
      const cleanSub = subStr.replace(/subscribers?/i, "").trim();
      const vidStr = ov.video_count || "39 videos";
      const cleanVid = vidStr.replace(/videos?/i, "").trim();
      const ltViewsStr = (ov.lifetime_views || 67935).toLocaleString();
      const ltHoursStr = (ov.lifetime_hours || 165.7).toLocaleString() + " hrs";

      // Studio Tab Overview Bar & Avatar
      const stSub = document.getElementById("studio-overview-subs");
      if (stSub) stSub.textContent = subStr;
      const stVid = document.getElementById("studio-overview-videos");
      if (stVid) stVid.textContent = vidStr;
      const stLtV = document.getElementById("studio-overview-lifetime-views");
      if (stLtV) stLtV.textContent = ltViewsStr;
      const stLtH = document.getElementById("studio-overview-lifetime-hours");
      if (stLtH) stLtH.textContent = ltHoursStr;

      if (ov.avatar) {
        const studioAv = document.getElementById("studio-ch-avatar");
        if (studioAv) {
          studioAv.innerHTML = `<img src="${ov.avatar}" alt="Fear Studio" class="studio-avatar-img">`;
        }
      }
      if (ov.title) {
        const stName = document.getElementById("studio-ch-name");
        if (stName) stName.textContent = ov.title;
      }

      // Sync Hero badges on Channel Hub
      const hubSub = document.getElementById("hub-subscriber-count");
      if (hubSub) hubSub.textContent = cleanSub;
      const hubVid = document.getElementById("hub-video-count");
      if (hubVid) hubVid.textContent = cleanVid;
      const hubLtV = document.getElementById("hub-lifetime-views");
      if (hubLtV) {
        const vNum = ov.lifetime_views || 67935;
        hubLtV.textContent = (vNum >= 1000 ? (vNum / 1000).toFixed(1) + "K" : vNum);
      }
    } catch (e) {
      console.error("Failed to load studio overview:", e);
    }
  }

  // Master fetch for all Studio widgets in the selected period
  function loadAllStudioData(days) {
    loadStudioReport(days);
    loadStudioTrend(days);
    loadTopVideos(days);
  }

  // 1. Studio Report (Metric Cards & Banner)
  async function loadStudioReport(days = "28") {
    try {
      const res = await fetch(`/api/studio/report?days=${encodeURIComponent(days)}`);
      const rep = await res.json();
      if (rep.error) {
        console.warn("Studio API Notice:", rep.error);
        return;
      }

      const viewsStr = (rep.views || 0).toLocaleString();
      const hoursStr = (rep.watch_time_hours || 0).toLocaleString() + " hrs";
      const avgPctStr = rep.average_view_percentage || "--";
      const avgDurStr = rep.average_view_duration || "--";
      const net = rep.subscribers_net || 0;
      const subsStr = (net > 0 ? "+" : "") + net;

      // Update Studio Tab Cards
      const periodEl = document.getElementById("studio-report-period");
      if (periodEl) periodEl.textContent = rep.period || `Last ${days} days`;

      document.getElementById("metric-views").textContent = viewsStr;
      document.getElementById("metric-hours").textContent = hoursStr;
      document.getElementById("metric-avg-pct").textContent = avgPctStr;
      document.getElementById("metric-avg-dur").textContent = avgDurStr;
      document.getElementById("metric-subs").textContent = subsStr;

      const subDetail = document.getElementById("metric-subs-detail");
      if (subDetail) {
        const g = rep.subscribers_gained || 0;
        const l = rep.subscribers_lost || 0;
        subDetail.textContent = `Gained: +${g} | Lost: -${l}`;
      }

      // Update Channel Hub Top Banner
      const hubViews = document.getElementById("hub-stat-views");
      if (hubViews) hubViews.textContent = viewsStr;
      const hubHours = document.getElementById("hub-stat-hours");
      if (hubHours) hubHours.textContent = hoursStr;
      const hubPct = document.getElementById("hub-stat-pct");
      if (hubPct) hubPct.textContent = avgPctStr;
      const hubDur = document.getElementById("hub-stat-dur");
      if (hubDur) hubDur.textContent = avgDurStr;
      const hubSubs = document.getElementById("hub-stat-subs");
      if (hubSubs) hubSubs.textContent = subsStr;

      // Update period badge text
      const periodLabelStr = days === "lifetime" ? "Lifetime" : `${days}d`;
      document.querySelectorAll(".banner-period-label").forEach(lbl => {
        lbl.textContent = periodLabelStr;
      });
    } catch (e) {
      console.error("Error loading report:", e);
    }
  }

  // 2. Studio Daily Trend Chart
  async function loadStudioTrend(days = "28") {
    try {
      const res = await fetch(`/api/studio/trend?days=${encodeURIComponent(days)}`);
      if (!res.ok) return;
      const data = await res.json();
      renderStudioTrendSvg(data.trend || []);
    } catch (e) {
      console.error("Error loading trend:", e);
    }
  }

  function renderStudioTrendSvg(trend) {
    const svg = document.getElementById("studio-svg-chart");
    const tooltip = document.getElementById("chart-tooltip");
    if (!svg) return;

    if (!trend || trend.length === 0) {
      svg.innerHTML = `
        <text x="400" y="110" fill="#5e697d" font-size="14" text-anchor="middle" font-family="var(--font-main)">
          No daily analytics recorded in this period
        </text>`;
      return;
    }

    const width = 800;
    const height = 220;
    const padX = 40;
    const padY = 30;
    const innerW = width - padX * 2;
    const innerH = height - padY * 2;

    const maxViews = Math.max(...trend.map(t => t.views), 10);
    const n = trend.length;

    const pts = trend.map((t, i) => {
      const x = padX + (n > 1 ? (i / (n - 1)) * innerW : innerW / 2);
      const y = height - padY - (t.views / maxViews) * innerH;
      return { x, y, data: t };
    });

    const pathD = pts.reduce((acc, p, idx) => (idx === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`), "");
    const areaD = `${pathD} L ${pts[pts.length - 1].x} ${height - padY} L ${pts[0].x} ${height - padY} Z`;

    // Generate grid lines
    let gridLines = "";
    for (let g = 0; g <= 4; g++) {
      const gy = height - padY - (g / 4) * innerH;
      const gv = Math.round((g / 4) * maxViews);
      gridLines += `
        <line x1="${padX}" y1="${gy}" x2="${width - padX}" y2="${gy}" stroke="rgba(255,255,255,0.06)" stroke-dasharray="3,3" />
        <text x="${padX - 8}" y="${gy + 4}" fill="#5e697d" font-size="10" text-anchor="end" font-family="var(--font-mono)">${gv}</text>
      `;
    }

    // Interactive circle markers
    let markers = "";
    pts.forEach((p, idx) => {
      markers += `
        <circle cx="${p.x}" cy="${p.y}" r="4" fill="#ff2b55" stroke="#0a0c10" stroke-width="2" class="chart-point" data-idx="${idx}"></circle>
      `;
    });

    svg.innerHTML = `
      <defs>
        <linearGradient id="viewsGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#ff2b55" stop-opacity="0.45" />
          <stop offset="100%" stop-color="#ff2b55" stop-opacity="0.0" />
        </linearGradient>
      </defs>
      ${gridLines}
      <path d="${areaD}" fill="url(#viewsGrad)" />
      <path d="${pathD}" fill="none" stroke="#ff2b55" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
      ${markers}
    `;

    // Tooltip hover interactions
    const chartContainer = document.getElementById("studio-chart-container");
    svg.querySelectorAll(".chart-point").forEach(dot => {
      dot.addEventListener("mouseenter", e => {
        const idx = parseInt(e.target.getAttribute("data-idx"));
        const item = trend[idx];
        if (!item || !tooltip) return;

        tooltip.innerHTML = `
          <div style="font-weight:700; color:#fff; margin-bottom:2px;">${item.date}</div>
          <div style="color:var(--yt-crimson); font-weight:800;"><i class="fa-solid fa-eye"></i> ${item.views.toLocaleString()} views</div>
          <div style="color:#9aa5b8; font-size:10px;"><i class="fa-solid fa-clock"></i> ${item.watch_time_hours} hrs watch time</div>
        `;
        tooltip.classList.remove("hidden");
        const rect = chartContainer.getBoundingClientRect();
        const pt = pts[idx];
        const tipX = (pt.x / width) * rect.width;
        const tipY = (pt.y / height) * rect.height - 55;
        tooltip.style.left = `${tipX}px`;
        tooltip.style.top = `${tipY}px`;
      });

      dot.addEventListener("mouseleave", () => {
        if (tooltip) tooltip.classList.add("hidden");
      });
    });
  }

  // 3. Top Performing Videos in Period
  async function loadTopVideos(days = "28") {
    const tbody = document.getElementById("studio-top-videos-body");
    if (!tbody) return;

    try {
      const res = await fetch(`/api/studio/top-videos?days=${encodeURIComponent(days)}&limit=8`);
      if (!res.ok) return;
      const data = await res.json();
      const videos = data.videos || [];

      tbody.innerHTML = "";
      if (!videos.length) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 20px; color: var(--text-muted);">No video activity recorded for this period.</td></tr>`;
        return;
      }

      videos.forEach((v, idx) => {
        const tr = document.createElement("tr");
        const viewsStr = (v.views || 0).toLocaleString();
        const hrsStr = (v.watch_time_hours || 0).toLocaleString() + " hrs";
        const durStr = v.avg_duration || "0m 0s";

        tr.innerHTML = `
          <td><span class="table-rank-badge">#${idx + 1}</span></td>
          <td>
            <div class="table-video-cell">
              <img src="${v.thumbnail}" alt="" class="table-mini-thumb">
              <span class="table-video-title" title="${escapeHtml(v.title)}">${escapeHtml(v.title)}</span>
            </div>
          </td>
          <td style="text-align: right;" class="table-num">${viewsStr}</td>
          <td style="text-align: right;" class="table-num">${hrsStr}</td>
          <td style="text-align: right;" class="table-num">${durStr}</td>
          <td style="text-align: center;">
            <div style="display:flex; justify-content:center; gap:6px;">
              <button class="btn btn-sm btn-secondary btn-table-title" data-title="${escapeHtml(v.title)}" title="Lint Title">
                <i class="fa-solid fa-tag"></i>
              </button>
              <button class="btn btn-sm btn-secondary btn-table-hook" data-hook="${escapeHtml(v.title)}" title="Score Hook">
                <i class="fa-solid fa-bullseye"></i>
              </button>
              <a href="${v.url}" target="_blank" class="btn btn-sm btn-secondary" title="Watch on YouTube">
                <i class="fa-brands fa-youtube" style="color: #ff0033;"></i>
              </a>
            </div>
          </td>
        `;
        tbody.appendChild(tr);
      });

      // Quick listeners in table
      tbody.querySelectorAll(".btn-table-title").forEach(b => {
        b.addEventListener("click", () => {
          const t = b.getAttribute("data-title");
          document.getElementById("nav-btn-title").click();
          document.getElementById("input-title").value = t;
          document.getElementById("btn-lint-title").click();
        });
      });

      tbody.querySelectorAll(".btn-table-hook").forEach(b => {
        b.addEventListener("click", () => {
          const h = b.getAttribute("data-hook");
          document.getElementById("nav-btn-hook").click();
          document.getElementById("hook-input").value = h;
          document.getElementById("btn-score-hook").click();
        });
      });
    } catch (e) {
      console.error("Failed to load top videos:", e);
    }
  }

  // Synchronize Date Filter Controls
  function setPeriod(days) {
    currentStudioDays = days;

    // 1. Update Studio tab pills
    studioDatePills.forEach(p => {
      if (p.getAttribute("data-days") === days) {
        p.classList.add("active");
      } else {
        p.classList.remove("active");
      }
    });

    // 2. Update Channel Hub dropdown
    if (hubDateFilter) {
      hubDateFilter.value = days;
    }

    // 3. Reload everything with the new period
    loadAllStudioData(currentStudioDays);
  }

  // Pill click handler
  studioDatePills.forEach(pill => {
    pill.addEventListener("click", () => {
      const d = pill.getAttribute("data-days");
      setPeriod(d);
    });
  });

  // Hub dropdown handler
  if (hubDateFilter) {
    hubDateFilter.addEventListener("change", e => {
      setPeriod(e.target.value);
    });
  }

  // Save Credentials button
  btnSaveCreds.addEventListener("click", async () => {
    const clientId = document.getElementById("oauth-client-id").value.trim();
    const clientSecret = document.getElementById("oauth-client-secret").value.trim();
    if (!clientId || !clientSecret) {
      showToast("Please enter both Client ID and Client Secret!", "warning");
      return;
    }
    btnSaveCreds.disabled = true;
    try {
      const res = await fetch("/api/studio/credentials", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: jsonBody({ client_id: clientId, client_secret: clientSecret })
      });
      const data = await res.json();
      if (data.success) {
        showToast("Credentials saved! Now sign in with Google.", "success");
        checkStatus();
      } else {
        showToast("Error saving credentials: " + data.error, "error");
      }
    } catch (err) {
      showToast("Failed to save credentials: " + err, "error");
    } finally {
      btnSaveCreds.disabled = false;
    }
  });

  // Start OAuth Login button
  btnAuth.addEventListener("click", async () => {
    btnAuth.disabled = true;
    btnAuth.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Opening Google Login...`;
    try {
      await fetch("/api/studio/auth", { method: "POST" });
      showToast("Google Login window opened in browser!", "info", 5000);
      // Poll for completion
      const interval = setInterval(async () => {
        const res = await fetch("/api/studio/status");
        const data = await res.json();
        if (data.authenticated) {
          clearInterval(interval);
          checkStatus();
          showToast("Studio Analytics Connected Successfully!", "success");
        }
      }, 3000);
    } catch (err) {
      showToast("Auth failed: " + err, "error");
    } finally {
      btnAuth.disabled = false;
      btnAuth.innerHTML = `<i class="fa-brands fa-google"></i> Sign In With Google & Authorize`;
    }
  });

  // Refresh Studio Data button
  btnRefresh.addEventListener("click", () => {
    loadAllStudioData(currentStudioDays);
  });

  checkStatus();
}

// 10. Channel Audit Tab (yt-audit)
function initAuditTab() {
  const btn = document.getElementById("btn-run-audit");
  const container = document.getElementById("audit-results-container");
  if (!btn || !container) return;

  btn.addEventListener("click", async () => {
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Auditing Channel...`;
    container.innerHTML = `<p class="sub-text" style="padding:30px; text-align:center;"><i class="fa-solid fa-spinner fa-spin"></i> Analyzing recent upload packaging, hook diagnostics, and studio metrics...</p>`;

    try {
      const res = await fetch("/api/audit");
      const data = await res.json();
      if (data.error) {
        container.innerHTML = `<div class="lint-issue-tag" style="padding:16px;"><strong>Error:</strong> ${escapeHtml(data.error)}</div>`;
        return;
      }

      const pFix = data.primary_fix || {};
      const working = data.working_well || [];
      const audits = data.title_audits || [];

      let tableRows = "";
      audits.forEach((a, i) => {
        const thumb = a.thumbnail || `https://i.ytimg.com/vi/${a.videoId}/hqdefault.jpg`;
        const cutWarning = a.chars > 40 ? `<span style="color:var(--accent-red); font-size:11px; font-weight:700;"><i class="fa-solid fa-triangle-exclamation"></i> Mobile Cut (${a.chars}c)</span>` : `<span style="color:var(--accent-green); font-size:11px;">OK (${a.chars}c)</span>`;
        tableRows += `
          <tr>
            <td>${i + 1}</td>
            <td>
              <div class="table-video-cell">
                <img src="${thumb}" class="table-mini-thumb" alt="">
                <span class="table-video-title" title="${escapeHtml(a.title)}">${escapeHtml(a.title)}</span>
              </div>
            </td>
            <td>${cutWarning}</td>
            <td style="text-align:center;"><span class="table-num">${a.score}/100</span></td>
            <td style="text-align:right;"><span class="pill-badge">${escapeHtml(a.hook_formula || 'Unclassified')}</span></td>
          </tr>
        `;
      });

      container.innerHTML = `
        <div class="audit-summary-strip">
          <div class="audit-stat-card">
            <span class="audit-stat-label">Packaging Health Score</span>
            <strong class="audit-stat-val" style="color: ${data.health_score > 75 ? 'var(--accent-green)' : 'var(--accent-yellow)'}">${data.health_score}/100</strong>
          </div>
          <div class="audit-stat-card">
            <span class="audit-stat-label">Mobile Cutoff Exposure</span>
            <strong class="audit-stat-val" style="color: var(--accent-red);">${data.mobile_cutoff_percentage}</strong>
          </div>
          <div class="audit-stat-card">
            <span class="audit-stat-label">Videos Evaluated</span>
            <strong class="audit-stat-val">${data.total_audited} Uploads</strong>
          </div>
        </div>

        <div class="audit-primary-fix-card">
          <div class="fix-header-badge"><i class="fa-solid fa-fire"></i> THE ONE BIGGEST FIX THIS WEEK</div>
          <h3 class="fix-title">${escapeHtml(pFix.title || 'Packaging Optimization')}</h3>
          <div class="fix-grid">
            <div class="fix-item">
              <span class="fix-item-lbl"><i class="fa-solid fa-circle-exclamation"></i> Leak Identified:</span>
              <p>${escapeHtml(pFix.leak || '')}</p>
            </div>
            <div class="fix-item">
              <span class="fix-item-lbl"><i class="fa-solid fa-bullseye"></i> Immediate Action:</span>
              <p>${escapeHtml(pFix.action || '')}</p>
            </div>
            <div class="fix-item">
              <span class="fix-item-lbl"><i class="fa-solid fa-chart-line"></i> Expected Impact:</span>
              <p>${escapeHtml(pFix.impact || '')}</p>
            </div>
          </div>
        </div>

        <div class="audit-two-col">
          <div class="audit-box-col">
            <h4><i class="fa-solid fa-circle-check" style="color:var(--accent-green);"></i> 3 Things Already Working Well</h4>
            <ul class="audit-list">
              ${working.map(w => `<li><i class="fa-solid fa-check"></i> ${escapeHtml(w)}</li>`).join("")}
            </ul>
          </div>
          <div class="audit-box-col">
            <h4><i class="fa-solid fa-hand" style="color:var(--accent-red);"></i> What NOT To Do Yet</h4>
            <p class="audit-warning-text">${escapeHtml(data.not_to_do_yet || '')}</p>
          </div>
        </div>

        <div class="studio-top-content-section" style="margin-top:20px;">
          <h4 style="margin-bottom:12px;"><i class="fa-solid fa-list-ol"></i> Evaluated Titles & Mobile Truncation</h4>
          <table class="studio-table">
            <thead>
              <tr>
                <th style="width:30px;">#</th>
                <th>Title</th>
                <th>Cutoff Status</th>
                <th style="text-align:center;">Score</th>
                <th style="text-align:right;">Formula</th>
              </tr>
            </thead>
            <tbody>${tableRows}</tbody>
          </table>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<p class="sub-text">Audit failed: ${err}</p>`;
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<i class="fa-solid fa-stethoscope"></i> Re-Run Audit`;
    }
  });
}

// 11. SEO & Tags Studio (yt-seo)
function initSeoTab() {
  const btn = document.getElementById("btn-gen-seo");
  const input = document.getElementById("seo-input-topic");
  const outputBox = document.getElementById("seo-result-box");
  const contentDisplay = document.getElementById("seo-content-display");
  const copyBtn = document.getElementById("btn-copy-seo-desc");
  if (!btn || !input) return;

  btn.addEventListener("click", async () => {
    const text = input.value.trim();
    if (!text) return;

    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Generating...`;

    try {
      const res = await fetch("/api/seo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: jsonBody({ topic: text })
      });
      const data = await res.json();
      if (data.error) {
        showToast("SEO Error: " + data.error, "error");
        return;
      }
      showToast("SEO Package generated successfully!", "success");

      outputBox.classList.remove("hidden");
      contentDisplay.innerHTML = `
        <div style="margin-bottom: 16px;">
          <strong style="color:var(--yt-crimson); font-size:12px; text-transform:uppercase; letter-spacing:0.5px;">First 2 Lines (Above "...more" Cutoff):</strong>
          <div style="background:rgba(0,0,0,0.4); padding:10px 14px; border-radius:6px; margin-top:6px; font-family:var(--font-mono); font-size:12.5px;">
            ${escapeHtml(data.snippet_above_fold)}
          </div>
        </div>

        <div style="margin-bottom: 16px;">
          <strong style="color:var(--accent-yellow); font-size:12px; text-transform:uppercase; letter-spacing:0.5px;">3 Search Queries This Video Must Win:</strong>
          <ul style="margin-top:6px; padding-left:18px; font-size:13px; color:#fff;">
            ${data.target_queries.map(q => `<li style="margin-bottom:4px;">"${escapeHtml(q)}"</li>`).join("")}
          </ul>
        </div>

        <div style="margin-bottom: 16px;">
          <strong style="color:var(--accent-cyan); font-size:12px; text-transform:uppercase; letter-spacing:0.5px;">Focused Disambiguation Tags (${data.tag_count}):</strong>
          <div style="display:flex; flex-wrap:wrap; gap:6px; margin-top:8px;">
            ${data.tags.map(t => `<span class="pill-badge" style="cursor:pointer;" onclick="navigator.clipboard.writeText('${t}')" title="Click to copy tag">${escapeHtml(t)}</span>`).join("")}
          </div>
        </div>

        <div>
          <strong style="color:var(--text-secondary); font-size:12px; text-transform:uppercase; letter-spacing:0.5px;">Full Description Block:</strong>
          <pre id="seo-full-desc-text" style="background:rgba(0,0,0,0.5); padding:12px; border-radius:8px; margin-top:6px; font-family:var(--font-mono); font-size:12px; white-space:pre-wrap; max-height:220px; overflow-y:auto;">${escapeHtml(data.description_body)}</pre>
        </div>
      `;

      if (copyBtn) {
        copyBtn.onclick = () => {
          navigator.clipboard.writeText(data.description_body);
          showToast("Full description copied to clipboard!", "success");
        };
      }
    } catch (e) {
      showToast("SEO Generation Failed: " + e, "error");
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<i class="fa-solid fa-magnifying-glass-chart"></i> Generate SEO Package`;
    }
  });
}

// 12. Viral Shorts Extractor (yt-shorts)
function initShortsTab() {
  const btn = document.getElementById("btn-gen-shorts");
  const input = document.getElementById("shorts-input-text");
  const resultBox = document.getElementById("shorts-result-box");
  if (!btn || !input) return;

  btn.addEventListener("click", async () => {
    const text = input.value.trim();
    if (!text) return;

    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Extracting Shorts...`;

    try {
      const res = await fetch("/api/shorts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: jsonBody({ text })
      });
      const data = await res.json();
      if (data.error) {
        showToast("Shorts Error: " + data.error, "error");
        return;
      }
      showToast("3 Viral Shorts concepts generated!", "success");

      resultBox.classList.remove("hidden");
      resultBox.innerHTML = "";
      (data.shorts_extracted || []).forEach(s => {
        const card = document.createElement("div");
        card.className = "short-concept-card";
        card.innerHTML = `
          <div class="short-card-header">
            <span class="short-num-badge">Short #${s.short_num}</span>
            <span class="short-duration-badge">${s.duration}</span>
          </div>
          <div class="short-hook-box">
            <span class="short-label">0-3s Visual Hook:</span>
            <strong>"${escapeHtml(s.hook_0_3s)}"</strong>
          </div>
          <div class="short-body-box">
            <span class="short-label">Spoken Narration:</span>
            <p>${escapeHtml(s.spoken_script)}</p>
          </div>
          <div class="short-loop-box">
            <span class="short-label">Seamless Loop Ending:</span>
            <em>"${escapeHtml(s.loop_ending)}"</em>
          </div>
          <div class="short-footer-row">
            <span style="font-size:11px; color:var(--text-muted);"><i class="fa-solid fa-video"></i> ${escapeHtml(s.target_format)}</span>
            <button class="btn btn-sm btn-secondary btn-copy-short" data-script="${escapeHtml(s.spoken_script)}">
              <i class="fa-solid fa-copy"></i> Copy Script
            </button>
          </div>
        `;
        resultBox.appendChild(card);
      });

      resultBox.querySelectorAll(".btn-copy-short").forEach(b => {
        b.addEventListener("click", () => {
          navigator.clipboard.writeText(b.getAttribute("data-script"));
          showToast("Short script copied to clipboard!", "success");
        });
      });
    } catch (e) {
      showToast("Failed to extract shorts: " + e, "error");
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<i class="fa-solid fa-mobile-screen-button"></i> Extract 3 Viral Shorts`;
    }
  });
}

// 13. Content Calendar (yt-plan)
function initPlanTab() {
  const btn = document.getElementById("btn-gen-plan");
  const inputHours = document.getElementById("plan-input-hours");
  const inputTheme = document.getElementById("plan-input-theme");
  const resultBox = document.getElementById("plan-result-box");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Building Schedule...`;

    try {
      const res = await fetch("/api/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: jsonBody({
          hours: inputHours ? parseInt(inputHours.value) : 8,
          theme: inputTheme ? inputTheme.value : "Horror"
        })
      });
      const data = await res.json();
      if (data.error) {
        showToast("Plan Error: " + data.error, "error");
        return;
      }
      showToast("4-Week Content Calendar generated!", "success");

      resultBox.classList.remove("hidden");
      resultBox.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
          <h4><i class="fa-solid fa-calendar-days" style="color:var(--yt-crimson);"></i> 4-Week Release Schedule (${data.cadence})</h4>
          <span class="pill-badge">${data.creator_hours_per_week} hrs/week budget</span>
        </div>
        <div class="calendar-weeks-grid">
          ${(data.weeks || []).map(w => `
            <div class="calendar-week-card">
              <div class="week-card-top">
                <span class="week-number">WEEK ${w.week}</span>
                <span class="week-tier-badge">${escapeHtml(w.tier)}</span>
              </div>
              <h5 class="week-title">${escapeHtml(w.title_concept)}</h5>
              <div class="week-meta-info">
                <span><i class="fa-solid fa-clock"></i> ${w.format}</span>
                <span><i class="fa-solid fa-calendar-check"></i> ${w.schedule || w.upload_day}</span>
              </div>
              <div class="week-strategy"><strong>Strategy:</strong> ${escapeHtml(w.why)}</div>
            </div>
          `).join("")}
        </div>
      `;
    } catch (e) {
      showToast("Plan Failed: " + e, "error");
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<i class="fa-solid fa-calendar-check"></i> Generate 4-Week Schedule`;
    }
  });
}

// 14. Comment Responder (yt-comment)
function initCommentTab() {
  const btn = document.getElementById("btn-triage-comments");
  const input = document.getElementById("comment-input-text");
  const resultBox = document.getElementById("comment-result-box");
  if (!btn || !input) return;

  btn.addEventListener("click", async () => {
    const text = input.value.trim();
    if (!text) return;

    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Triaging Comments...`;

    try {
      const res = await fetch("/api/comment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: jsonBody({ comments: text })
      });
      const data = await res.json();
      if (data.error) {
        showToast("Comment Error: " + data.error, "error");
        return;
      }
      showToast("Comments triaged and replies drafted!", "success");

      resultBox.classList.remove("hidden");
      resultBox.innerHTML = "";
      const piles = data.piles || {};

      const pileConfigs = [
        { key: "worth_answering", title: "Worth Answering", icon: "fa-circle-question", color: "var(--accent-cyan)", badge: "Priority" },
        { key: "pin_candidate", title: "Pin Candidates", icon: "fa-thumbtack", color: "var(--accent-yellow)", badge: "Sets Tone" },
        { key: "praise", title: "Praise & Support", icon: "fa-heart", color: "var(--accent-green)", badge: "Heart" },
        { key: "trash", title: "Trash / Trolls", icon: "fa-trash", color: "var(--text-muted)", badge: "Ignore" }
      ];

      pileConfigs.forEach(cfg => {
        const items = piles[cfg.key] || [];
        if (!items.length) return;

        const pileDiv = document.createElement("div");
        pileDiv.className = "comment-pile-block";
        pileDiv.innerHTML = `
          <div class="comment-pile-header">
            <span style="color:${cfg.color}; font-weight:700;"><i class="fa-solid ${cfg.icon}"></i> ${cfg.title} (${items.length})</span>
            <span class="pill-badge">${cfg.badge}</span>
          </div>
          <div class="comment-pile-items">
            ${items.map(it => `
              <div class="comment-row-item">
                <div class="comment-quote">"${escapeHtml(it.comment)}"</div>
                ${it.reply ? `<div class="comment-draft-reply"><strong>Fear Studio Voice Reply:</strong> "${escapeHtml(it.reply)}"</div>` : ''}
                <div class="comment-action-note"><i class="fa-solid fa-arrow-right"></i> ${escapeHtml(it.action)}</div>
              </div>
            `).join("")}
          </div>
        `;
        resultBox.appendChild(pileDiv);
      });
    } catch (e) {
      showToast("Comment Triage Failed: " + e, "error");
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<i class="fa-solid fa-comments"></i> Triage & Draft Replies`;
    }
  });
}

// Helper utilities
function jsonBody(obj) {
  return JSON.stringify(obj);
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
