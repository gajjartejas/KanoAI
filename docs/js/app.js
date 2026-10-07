/**
 * app.js: Core coordinator for Gujarati Font Stroke Animator.
 * Manages category filters, Barakhadi consonant sub-bar, search, character selection,
 * and keyboard navigation.
 */

class App {
  constructor() {
    this.catalog = [];
    this.filteredCatalog = [];
    this.currentCategory = 'kakko'; // Default to kakko
    this.currentConsonantGroup = '1_k'; // Default barakhadi group
    this.currentChar = null;
    this.searchQuery = '';
  }

  async init() {
    // 1. Initialize Managers
    window.soundManager.initUI();
    window.stageManager.initUI();

    // 2. Load Catalog
    if (window.GUJARATI_CATALOG && window.GUJARATI_CATALOG.length > 0) {
      this.catalog = window.GUJARATI_CATALOG;
    } else {
      try {
        const res = await fetch('assets/catalog.json');
        this.catalog = await res.json();
      } catch (e) {
        console.error('Failed to load catalog.json:', e);
      }
    }

    // 3. Setup UI listeners
    this.setupCategoryTabs();
    this.setupSearchBar();
    this.setupKeyboardNavigation();

    // 4. Initial Render (supports ?cat= query param)
    const urlParams = new URLSearchParams(window.location.search);
    const catParam = urlParams.get('cat');
    if (catParam && ['kakko', 'barakhadi', 'numbers', 'all'].includes(catParam)) {
      this.setCategory(catParam);
    } else {
      this.applyFilters();
      if (this.filteredCatalog.length > 0) {
        this.selectCharacter(this.filteredCatalog[0], false);
      }
    }
  }

  setupCategoryTabs() {
    document.querySelectorAll('.cat-tab').forEach((tab) => {
      tab.addEventListener('click', (e) => {
        const cat = e.currentTarget.getAttribute('data-cat');
        this.setCategory(cat);
      });
    });
  }

  setCategory(category) {
    this.currentCategory = category;
    document.querySelectorAll('.cat-tab').forEach((tab) => {
      tab.classList.toggle('active', tab.getAttribute('data-cat') === category);
    });

    // Show/hide Barakhadi consonant sub-bar
    const barakhadiBar = document.getElementById('barakhadi-bar');
    if (barakhadiBar) {
      barakhadiBar.style.display = category === 'barakhadi' ? 'flex' : 'none';
      if (category === 'barakhadi' && barakhadiBar.children.length === 0) {
        this.renderBarakhadiConsonantBar();
      }
    }

    this.applyFilters();
    if (this.filteredCatalog.length > 0) {
      this.selectCharacter(this.filteredCatalog[0], true);
    }
  }

  renderBarakhadiConsonantBar() {
    const bar = document.getElementById('barakhadi-bar');
    if (!bar) return;
    bar.innerHTML = '';

    // Get unique base consonant groups
    const groups = [];
    const seen = new Set();
    this.catalog
      .filter((c) => c.category === 'barakhadi')
      .forEach((c) => {
        if (!seen.has(c.group)) {
          seen.add(c.group);
          groups.push({ group: c.group, base_char: c.base_char, en: c.group_en });
        }
      });

    groups.forEach((g) => {
      const chip = document.createElement('button');
      chip.className = 'consonant-chip' + (g.group === this.currentConsonantGroup ? ' active' : '');
      chip.innerText = g.base_char;
      chip.title = `${g.base_char} (${g.en})`;
      chip.onclick = () => {
        this.currentConsonantGroup = g.group;
        document.querySelectorAll('.consonant-chip').forEach((c) => {
          c.classList.toggle('active', c === chip);
        });
        this.applyFilters();
        if (this.filteredCatalog.length > 0) {
          this.selectCharacter(this.filteredCatalog[0], true);
        }
      };
      bar.appendChild(chip);
    });
  }

  setupSearchBar() {
    const input = document.getElementById('search-input');
    if (!input) return;

    input.addEventListener('input', (e) => {
      this.searchQuery = e.target.value.trim().toLowerCase();
      this.applyFilters();
    });
  }

  applyFilters() {
    let list = this.catalog;

    // Filter by Category
    if (this.currentCategory !== 'all') {
      list = list.filter((c) => c.category === this.currentCategory);
    }

    // If Barakhadi category and no search, filter by current consonant group
    if (this.currentCategory === 'barakhadi' && !this.searchQuery) {
      list = list.filter((c) => c.group === this.currentConsonantGroup);
    }

    // Filter by Search Query
    if (this.searchQuery) {
      list = list.filter((c) => {
        const charMatch = c.char && c.char.includes(this.searchQuery);
        const enMatch = c.en && c.en.toLowerCase().includes(this.searchQuery);
        const nameMatch = c.name_gu && c.name_gu.includes(this.searchQuery);
        const nameEnMatch = c.name_en && c.name_en.toLowerCase().includes(this.searchQuery);
        const numMatch = c.num !== undefined && String(c.num) === this.searchQuery;
        return charMatch || enMatch || nameMatch || nameEnMatch || numMatch;
      });
    }

    this.filteredCatalog = list;
    this.renderCharacterGrid();
  }

  renderCharacterGrid() {
    const grid = document.getElementById('char-grid');
    if (!grid) return;
    grid.innerHTML = '';

    if (this.filteredCatalog.length === 0) {
      grid.innerHTML = `
        <div class="empty-state">
          <span class="icon">🔍</span>
          <p>No characters match "${this.searchQuery}"</p>
        </div>
      `;
      return;
    }

    this.filteredCatalog.forEach((item) => {
      const btn = document.createElement('button');
      const isSelected = this.currentChar && this.currentChar.id === item.id;
      btn.className = 'char-btn' + (isSelected ? ' active' : '');

      let subText = item.en || '';
      if (item.category === 'numbers') {
        subText = `${item.num} (${item.name_en})`;
      }

      btn.innerHTML = `
        <span class="sound-indicator">🔊</span>
        <span class="char-glyph">${item.char}</span>
        <span class="char-sub">${subText}</span>
      `;

      btn.title = `${item.char} - ${subText}`;
      btn.onclick = () => this.selectCharacter(item, true);

      grid.appendChild(btn);
    });
  }

  selectCharacter(item, playSound = true) {
    this.currentChar = item;

    // Update active state in grid buttons
    document.querySelectorAll('.char-btn').forEach((btn) => {
      const glyph = btn.querySelector('.char-glyph');
      btn.classList.toggle('active', glyph && glyph.innerText === item.char);
    });

    // Update Banner
    this.updateHeaderBanner(item);

    // Load SVG into Stages
    window.stageManager.loadCharacter(item);

    // Play Kano Pronunciation Sound
    if (playSound && item.audio) {
      window.soundManager.playAudio(item.audio);
    }

    // Forward character selection to handwriting practice suite
    const frame = document.getElementById('handwriting-frame');
    if (frame && frame.contentWindow) {
      try {
        frame.contentWindow.postMessage({
          type: 'SELECT_CHARACTER',
          char: item.char,
          id: item.id,
          ref_svg: item.ref_svg,
          name: item.en || item.name_en || '',
          category: item.category,
        }, '*');
      } catch (err) {}
    }

    // If in TTS mode, update TTS textarea with the selected character
    const secTTS = document.getElementById('section-tts');
    if (secTTS && secTTS.style.display !== 'none') {
      const ttsInput = document.getElementById('tts-input-text');
      if (ttsInput) {
        ttsInput.value = item.char;
        ttsInput.dispatchEvent(new Event('input'));
      }
    }
  }

  updateHeaderBanner(item) {
    const glyphEl = document.getElementById('banner-glyph');
    const titleEl = document.getElementById('banner-title');
    const subtitleEl = document.getElementById('banner-subtitle');
    const tagCat = document.getElementById('banner-tag-cat');
    const tagStrokes = document.getElementById('banner-tag-strokes');

    if (glyphEl) glyphEl.innerText = item.char;

    if (titleEl) {
      let title = item.char;
      if (item.en) title += ` (${item.en})`;
      if (item.name_gu) title += ` - ${item.name_gu}`;
      titleEl.innerText = title;
    }

    if (subtitleEl) {
      if (item.category === 'numbers') {
        subtitleEl.innerText = `Gujarati Numeral: ${item.num} (${item.name_en})`;
      } else if (item.category === 'barakhadi') {
        subtitleEl.innerText = `Barakhadi: Base '${item.base_char}' with Vowel '${item.vowel_sign || "A"}'`;
      } else {
        subtitleEl.innerText = `Kakko ${item.type === 'vowel' ? 'Vowel (સ્વર)' : 'Consonant (વ્યંજન)'}`;
      }
    }

    if (tagCat) {
      tagCat.innerText = item.category.toUpperCase();
    }
    if (tagStrokes) {
      tagStrokes.innerText = `${item.stroke_count || 1} Stroke${(item.stroke_count || 1) > 1 ? 's' : ''}`;
    }
  }

  setupKeyboardNavigation() {
    window.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT') return;

      if (e.code === 'ArrowRight' || e.code === 'ArrowDown') {
        e.preventDefault();
        this.stepCharacter(1);
      } else if (e.code === 'ArrowLeft' || e.code === 'ArrowUp') {
        e.preventDefault();
        this.stepCharacter(-1);
      } else if (e.code === 'Space') {
        e.preventDefault();
        window.stageManager.replay();
      } else if (e.key === 'p' || e.key === 'P') {
        e.preventDefault();
        window.soundManager.replayCurrent();
      }
    });
  }

  stepCharacter(delta) {
    if (!this.currentChar || this.filteredCatalog.length === 0) return;
    const idx = this.filteredCatalog.findIndex((c) => c.id === this.currentChar.id);
    if (idx === -1) return;

    let nextIdx = (idx + delta + this.filteredCatalog.length) % this.filteredCatalog.length;
    this.selectCharacter(this.filteredCatalog[nextIdx], true);

    // Scroll into view
    const buttons = document.querySelectorAll('.char-btn');
    if (buttons[nextIdx]) {
      buttons[nextIdx].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }
}

window.switchSuite = function(suite) {
  const isHandwriting = suite === 'handwriting';
  const isTTS = suite === 'tts';
  const isAnimator = !isHandwriting && !isTTS;

  const tabAnimator = document.getElementById('tab-btn-animator');
  const tabHandwriting = document.getElementById('tab-btn-handwriting');
  const tabTTS = document.getElementById('tab-btn-tts');

  const secAnimator = document.getElementById('section-animator');
  const secHandwriting = document.getElementById('section-handwriting');
  const secTTS = document.getElementById('section-tts');
  const tagline = document.getElementById('suite-tagline');

  if (tabAnimator) {
    tabAnimator.classList.toggle('active', isAnimator);
    tabAnimator.setAttribute('aria-selected', isAnimator.toString());
  }
  if (tabHandwriting) {
    tabHandwriting.classList.toggle('active', isHandwriting);
    tabHandwriting.setAttribute('aria-selected', isHandwriting.toString());
  }
  if (tabTTS) {
    tabTTS.classList.toggle('active', isTTS);
    tabTTS.setAttribute('aria-selected', isTTS.toString());
  }

  if (secAnimator) secAnimator.style.display = isAnimator ? 'flex' : 'none';
  if (secHandwriting) {
    secHandwriting.style.display = isHandwriting ? 'flex' : 'none';
    if (isHandwriting) {
      const frame = document.getElementById('handwriting-frame');
      if (frame && frame.contentWindow) {
        try {
          frame.contentWindow.postMessage({ type: 'REQUEST_HEIGHT' }, '*');
          if (window.app && window.app.currentChar) {
            frame.contentWindow.postMessage({
              type: 'SELECT_CHARACTER',
              char: window.app.currentChar.char,
              id: window.app.currentChar.id,
              ref_svg: window.app.currentChar.ref_svg,
              name: window.app.currentChar.en || window.app.currentChar.name_en || '',
              category: window.app.currentChar.category,
            }, '*');
          }
        } catch (err) {}
      }
    }
  }
  if (secTTS) {
    secTTS.style.display = isTTS ? 'flex' : 'none';
    if (isTTS && window.ttsStudio && !window.ttsStudio.initialized) {
      window.ttsStudio.init();
      window.ttsStudio.initialized = true;
    }
  }

  if (tagline) {
    if (isTTS) {
      tagline.textContent = 'AI4Bharat IndicF5 (Flow-Matching) & Indic-TTS / Bodhan Indic-Speak • Neural Gujarati Voice Studio';
    } else if (isHandwriting) {
      tagline.textContent = 'Interactive Tracing, Word Quiz, Free Draw ML & Offline Benchmarks';
    } else {
      tagline.textContent = 'Reference Template (Light) vs Medial Ridge Auto-Generated (Bold) • 565 Characters';
    }
  }

  const hash = isTTS ? '#tts' : (isHandwriting ? '#handwriting' : '#animator');
  if (window.history && window.history.replaceState) {
    window.history.replaceState(null, '', hash);
  } else {
    window.location.hash = hash;
  }
};

// Auto-resize handwriting iframe to exact content height without feedback loop
let lastSetFrameHeight = 0;
window.addEventListener('message', function(event) {
  if (event.data && event.data.type === 'HANDWRITING_RESIZE' && typeof event.data.height === 'number') {
    const frame = document.getElementById('handwriting-frame');
    if (frame) {
      const isMobile = window.innerWidth < 880;
      const maxHeight = isMobile ? 1200 : 750;
      const minHeight = isMobile ? 650 : 500;
      const targetHeight = Math.max(minHeight, Math.min(maxHeight, Math.ceil(event.data.height)));
      if (Math.abs(targetHeight - lastSetFrameHeight) >= 8) {
        lastSetFrameHeight = targetHeight;
        frame.style.height = targetHeight + 'px';
      }
    }
  } else if (event.data && event.data.type === 'HANDWRITING_READY') {
    const frame = document.getElementById('handwriting-frame');
    if (frame && frame.contentWindow && window.app && window.app.currentChar) {
      try {
        frame.contentWindow.postMessage({
          type: 'SELECT_CHARACTER',
          char: window.app.currentChar.char,
          id: window.app.currentChar.id,
          ref_svg: window.app.currentChar.ref_svg,
          name: window.app.currentChar.en || window.app.currentChar.name_en || '',
          category: window.app.currentChar.category,
        }, '*');
      } catch (e) {}
    }
  }
});

window.app = new App();
document.addEventListener('DOMContentLoaded', () => {
  window.app.init();

  const frame = document.getElementById('handwriting-frame');
  if (frame) {
    frame.addEventListener('load', () => {
      if (window.app && window.app.currentChar && frame.contentWindow) {
        try {
          frame.contentWindow.postMessage({
            type: 'SELECT_CHARACTER',
            char: window.app.currentChar.char,
            id: window.app.currentChar.id,
            ref_svg: window.app.currentChar.ref_svg,
            name: window.app.currentChar.en || window.app.currentChar.name_en || '',
            category: window.app.currentChar.category,
          }, '*');
        } catch (e) {}
      }
    });
  }

  const initialHash = window.location.hash;
  if (initialHash === '#tts') {
    window.switchSuite('tts');
  } else if (initialHash === '#handwriting') {
    window.switchSuite('handwriting');
  } else {
    window.switchSuite('animator');
  }

  window.addEventListener('hashchange', () => {
    const currentHash = window.location.hash;
    if (currentHash === '#tts') {
      window.switchSuite('tts');
    } else if (currentHash === '#handwriting') {
      window.switchSuite('handwriting');
    } else {
      window.switchSuite('animator');
    }
  });
});
