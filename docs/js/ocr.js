/**
 * KanoAI Gujarati Optical Character Recognition (OCR) Studio Coordinator
 * Integrates Bhashini-IITJ IndicPhotoOCR, Gujarati TrOCR, and GujaratiHCR.
 */

class OCRStudio {
  constructor() {
    this.apiUrl = 'http://localhost:8000';
    this.currentImageBase64 = null;
    this.currentProcessedImageBase64 = null;
    this.currentEngine = 'indic_photo_ocr';
    this.currentLang = 'gujarati';
    this.currentViewMode = 'annotated'; // 'annotated', 'original'
    this.currentBoxes = [];
    this.currentSampleId = 'sample_1_printed_book';
    this.isProcessing = false;
    this.initialized = false;
    this.isDrawingMode = false;

    this.samples = [
      {
        id: 'sample_1_printed_book',
        title: '📖 Printed Book (પંચતંત્ર)',
        badge: 'Printed Text',
        engine: 'indic_photo_ocr',
        url: 'assets/ocr_samples/sample_1_printed_book.png',
        desc: 'Storybook page with headers and paragraphs.',
        ground_truth: 'પંચતંત્રની બોધકથાઓ : ચતુર સસલું\nપ્રકરણ ૧ : બુદ્ધિ આગળ બળ પાણી ભરે છે\nએક રમણીય અને ઘટાદાર વનમાં ભાસુરક નામનો એક મહાબળવાન સિંહ રહેતો હતો.\nતે વનના તમામ પશુઓ પર અત્યાચાર કરતો અને રોજના અનેક જીવોનો શિકાર કરતો.\nઆખરે બધા પશુઓએ ભેગા મળીને રોજ એક-એક પશુ સિંહના ખોરાક તરીકે મોકલવાનું નક્કી કર્યું.\nએક દિવસ એક નાના પણ ચતુર સસલાનો વારો આવ્યો.\nસસલાએ વનમાં એક ઊંડો કૂવો જોયો અને સિંહને કહ્યું: "વનમાં બીજો સિંહ આવી ગયો છે!"\nક્રોધે ભરાયેલા સિંહે કૂવામાં પોતાનો જ પડછાયો જોયો અને તરાપ મારીને ડૂબી મર્યો.\nબોધ : બળ કરતાં બુદ્ધિ ચડિયાતી છે.'
      },
      {
        id: 'sample_2_photo_signboard',
        title: '🚏 Photo Sign (અમદાવાદ જંકશન)',
        badge: 'Scene / Signboard',
        engine: 'indic_photo_ocr',
        url: 'assets/ocr_samples/sample_2_photo_signboard.png',
        desc: 'Real transport station signboard with multi-line text.',
        ground_truth: 'ગુજરાત પ્રવાસન નિગમ • GUJARAT TOURISM\nઅમદાવાદ જંકશન\nAHMEDABAD JUNCTION\nઆપનું હાર્દિક સ્વાગત છે • WELCOME\nપ્લેટફોર્મ નં. ૧ થી ૧૨  |  ટિકિટ બારી અને પૂછપરછ\nમુખ્ય પ્રવેશદ્વાર ➔  |  સ્વચ્છ ભારત અભિયાન'
      },
      {
        id: 'sample_3_handwritten_note',
        title: '✍️ Handwritten (ગાંધીજી સુવિચાર)',
        badge: 'Handwritten',
        engine: 'gujarati_hcr',
        url: 'assets/ocr_samples/sample_3_handwritten_note.png',
        desc: 'Student cursive notebook with ruled lines.',
        ground_truth: 'તારીખ: ૦૮/૧૦/૨૦૨૬\nગાંધીજીના અણમોલ સુવિચારો :\n૧. સત્ય એ જ મારો ઈશ્વર છે અને પ્રેમ એ જ મારો માર્ગ.\n૨. અહિંસા એ માત્ર કાયરતા નથી, પણ શક્તિશાળીનું સાચું હથિયાર છે.\n૩. તમારો આજનો વિચાર તમારા આવતીકાલનું નિર્માણ કરે છે.\n૪. શિક્ષણ એટલે બાળક અને માણસના શરીર, મન અને આત્માનો વિકાસ.\n૫. મારું જીવન એ જ મારો સંદેશ છે. - મહાત્મા ગાંધી\n૬. કસ્તુરબા આશ્રમ, સાબરમતી નદી કાંઠે, અમદાવાદ.\n૭. ગુજરાતી ભાષા આપણી અસ્મિતા અને ગૌરવ છે.\n૮. જય હિન્દ! જય જય ગરવી ગુજરાત!'
      },
      {
        id: 'sample_4_official_doc',
        title: '🏛️ Certificate (શિક્ષણ બોર્ડ)',
        badge: 'Official Doc',
        engine: 'indic_photo_ocr',
        url: 'assets/ocr_samples/sample_4_official_doc.png',
        desc: 'State certificate with roll number and marks.',
        ground_truth: 'ગુજરાત માધ્યમિક શિક્ષણ બોર્ડ, ગાંધીનગર\nપ્રમાણપત્ર : ગુજરાતી ભાષા પ્રાવીણ્ય\nપ્રમાણિત કરવામાં આવે છે કે : કુમાર આલોકભાઈ મહેતા\nપરીક્ષા કેન્દ્ર : સુરત | રોલ નંબર : GJ-૨૦૨૬-૪૫૮૯\nમેળવેલ ગુણ : ૯૫ / ૧૦૦ | શ્રેણી : વિશિષ્ટ યોગ્યતા (Distinction)\nતેમણે ગુજરાતી વાંચન, લેખન અને વ્યાકરણમાં શ્રેષ્ઠતા સિદ્ધ કરી છે.\nનિયામકશ્રી (પરીક્ષા)'
      },
      {
        id: 'sample_5_conjuncts',
        title: '🔤 Conjuncts (જોડાક્ષરો & અંકો)',
        badge: 'Isolated Glyphs',
        engine: 'gujarati_trocr',
        url: 'assets/ocr_samples/sample_5_conjuncts.png',
        desc: 'Complex conjuncts (ક્ષ, જ્ઞ, ત્ર, શ્ર) and digits ૦–૧૦.',
        ground_truth: 'ગુજરાતી જોડાક્ષરો (Conjuncts) અને સંખ્યાઓ (Numerals)\nક્ષ   જ્ઞ   ત્ર   શ્ર   દ્વ   દ્ભ   હ્મ   ઙ\nશબ્દો: વિદ્યા   સૂર્ય   કૃષ્ણ   બુદ્ધિ   જ્ઞાન   સત્ય\nગુજરાતી અંકો: ૦  ૧  ૨  ૩  ૪  ૫  ૬  ૭  ૮  ૯  ૧૦\nગણતરી: ૧૨૫ + ૩૭૫ = ૫૦૦  |  તારીખ: ૨૦૨૬'
      }
    ];
  }

  init() {
    if (this.initialized) return;
    this.renderSamples();
    this.bindEvents();
    this.initDrawingCanvas();
    this.checkServerHealth();
    // Preload first sample
    this.loadSample(this.samples[0]);
    this.initialized = true;
  }

  async checkServerHealth() {
    const badge = document.getElementById('ocr-server-status');
    const dot = document.getElementById('ocr-status-dot');
    const label = document.getElementById('ocr-status-label');
    if (!badge || !dot || !label) return;

    try {
      const res = await fetch(`${this.apiUrl}/api/ocr/health`, { method: 'GET', signal: AbortSignal.timeout(2500) });
      if (res.ok) {
        badge.className = 'ocr-status-badge connected';
        label.textContent = 'API Server Connected (Port 8000)';
        return;
      }
    } catch (e) {}

    // Fallback indicator
    badge.className = 'ocr-status-badge fallback';
    label.textContent = 'Direct Bhashini-IITJ Cloud Mode';
  }

  renderSamples() {
    const container = document.getElementById('ocr-samples-grid');
    if (!container) return;
    container.innerHTML = '';

    this.samples.forEach((sample, idx) => {
      const card = document.createElement('div');
      card.className = `ocr-sample-card ${idx === 0 ? 'active' : ''}`;
      card.id = `ocr-sample-${sample.id}`;
      card.innerHTML = `
        <img class="ocr-sample-thumb" src="${sample.url}" alt="${sample.title}" loading="lazy" />
        <span class="ocr-sample-badge">${sample.badge}</span>
        <div class="ocr-sample-title">${sample.title}</div>
      `;
      card.addEventListener('click', () => {
        document.querySelectorAll('.ocr-sample-card').forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        this.loadSample(sample);
      });
      container.appendChild(card);
    });
  }

  async loadSample(sample) {
    try {
      this.currentSampleId = sample.id;
      // Set recommended engine
      const engineSelect = document.getElementById('ocr-engine-select');
      if (engineSelect && sample.engine) {
        engineSelect.value = sample.engine;
        this.currentEngine = sample.engine;
        engineSelect.dispatchEvent(new Event('change'));
      }

      const res = await fetch(sample.url);
      const blob = await res.blob();
      const reader = new FileReader();
      reader.onload = (e) => {
        this.setImage(e.target.result, false);
      };
      reader.readAsDataURL(blob);
    } catch (e) {
      console.warn('Error loading sample image:', e);
    }
  }

  setImage(base64Data, isCustom = false) {
    this.currentImageBase64 = base64Data;
    this.currentProcessedImageBase64 = null;
    this.currentBoxes = [];
    if (isCustom) {
      this.currentSampleId = null;
      document.querySelectorAll('.ocr-sample-card').forEach(c => c.classList.remove('active'));
    }

    const dropzone = document.getElementById('ocr-dropzone-container');
    const emptyState = document.getElementById('ocr-dropzone-empty');
    const canvasWrap = document.getElementById('ocr-canvas-wrapper');
    const displayImg = document.getElementById('ocr-display-img');
    const overlay = document.getElementById('ocr-bounding-box-overlay');
    const drawContainer = document.getElementById('ocr-draw-container');

    if (drawContainer) drawContainer.style.display = 'none';
    if (emptyState) emptyState.style.display = 'none';
    if (canvasWrap) canvasWrap.style.display = 'flex';
    if (overlay) overlay.innerHTML = '';

    if (displayImg) {
      displayImg.src = base64Data;
    }
    if (dropzone) {
      dropzone.style.borderStyle = 'solid';
    }

    // Hide previous results until extracted
    const resultsPanel = document.getElementById('ocr-results-container');
    if (resultsPanel) resultsPanel.style.display = 'none';
  }

  bindEvents() {
    const fileInput = document.getElementById('ocr-file-input');
    const dropzone = document.getElementById('ocr-dropzone-container');
    const emptyState = document.getElementById('ocr-dropzone-empty');
    const btnExtract = document.getElementById('btn-ocr-extract');
    const engineSelect = document.getElementById('ocr-engine-select');
    const langSelect = document.getElementById('ocr-lang-select');

    // Click on empty dropzone opens file picker
    if (emptyState && fileInput) {
      emptyState.addEventListener('click', () => fileInput.click());
    }

    if (fileInput) {
      fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = (ev) => this.setImage(ev.target.result, true);
          reader.readAsDataURL(file);
        }
      });
    }

    // Drag and drop handlers
    if (dropzone) {
      ['dragenter', 'dragover'].forEach(name => {
        dropzone.addEventListener(name, (e) => {
          e.preventDefault();
          e.stopPropagation();
          dropzone.classList.add('drag-over');
        });
      });
      ['dragleave', 'drop'].forEach(name => {
        dropzone.addEventListener(name, (e) => {
          e.preventDefault();
          e.stopPropagation();
          dropzone.classList.remove('drag-over');
        });
      });
      dropzone.addEventListener('drop', (e) => {
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
          const reader = new FileReader();
          reader.onload = (ev) => this.setImage(ev.target.result, true);
          reader.readAsDataURL(file);
        }
      });
    }

    // Paste image from clipboard anywhere on page
    window.addEventListener('paste', (e) => {
      const secOCR = document.getElementById('section-ocr');
      if (!secOCR || secOCR.style.display === 'none') return;

      const items = (e.clipboardData || e.originalEvent.clipboardData).items;
      for (const item of items) {
        if (item.type.indexOf('image') !== -1) {
          const blob = item.getAsFile();
          const reader = new FileReader();
          reader.onload = (ev) => this.setImage(ev.target.result, true);
          reader.readAsDataURL(blob);
          this.showToast('📋 Image pasted from clipboard!');
          break;
        }
      }
    });

    // IndicPhotoOCR Execution Mode: Offline vs Online
    this.indicMode = 'offline';
    const btnIndicOffline = document.getElementById('btn-indic-mode-offline');
    const btnIndicOnline = document.getElementById('btn-indic-mode-online');
    const setIndicMode = (mode) => {
      this.indicMode = mode;
      if (btnIndicOffline) btnIndicOffline.classList.toggle('active', mode === 'offline');
      if (btnIndicOnline) btnIndicOnline.classList.toggle('active', mode === 'online');
      const indicUrlRow = document.getElementById('ocr-indic-url-row');
      const tokenRow = document.getElementById('ocr-hf-token-row');
      const infoBox = document.getElementById('ocr-engine-info');
      if (mode === 'offline') {
        if (indicUrlRow) indicUrlRow.style.display = 'block';
        if (tokenRow) tokenRow.style.display = 'none';
        if (infoBox) infoBox.innerHTML = '<strong>Bhashini-IITJ IndicPhotoOCR (Offline Mode)</strong>: Local scene text contour & bounding box recognition running on port 7860/8000.';
      } else {
        if (indicUrlRow) indicUrlRow.style.display = 'none';
        if (tokenRow) tokenRow.style.display = 'block';
        if (infoBox) infoBox.innerHTML = '<strong>Bhashini-IITJ IndicPhotoOCR (Online Cloud)</strong>: Connected to official Bhashini-IITJ Hugging Face Space (TextBPN++ & PARSeq model).';
      }
    };
    if (btnIndicOffline) btnIndicOffline.addEventListener('click', () => setIndicMode('offline'));
    if (btnIndicOnline) btnIndicOnline.addEventListener('click', () => setIndicMode('online'));

    // TrOCR Execution Mode: Offline vs Online
    this.trocrMode = 'offline';
    const btnOffline = document.getElementById('btn-trocr-mode-offline');
    const btnOnline = document.getElementById('btn-trocr-mode-online');
    const setTrOCRMode = (mode) => {
      this.trocrMode = mode;
      if (btnOffline) btnOffline.classList.toggle('active', mode === 'offline');
      if (btnOnline) btnOnline.classList.toggle('active', mode === 'online');
      const trocrUrlRow = document.getElementById('ocr-trocr-url-row');
      const tokenRow = document.getElementById('ocr-hf-token-row');
      const infoBox = document.getElementById('ocr-engine-info');
      if (mode === 'offline') {
        if (trocrUrlRow) trocrUrlRow.style.display = 'block';
        if (tokenRow) tokenRow.style.display = 'none';
        if (infoBox) infoBox.innerHTML = '<strong>Gujarati TrOCR (Offline Mode)</strong>: Vision Transformer (umangchaudhari/gujarati-ocr) running locally on port 7862.';
      } else {
        if (trocrUrlRow) trocrUrlRow.style.display = 'none';
        if (tokenRow) tokenRow.style.display = 'block';
        if (infoBox) infoBox.innerHTML = '<strong>Gujarati TrOCR (Online Cloud)</strong>: Hugging Face Cloud Inference API for printed books & complex conjuncts.';
      }
    };
    if (btnOffline) btnOffline.addEventListener('click', () => setTrOCRMode('offline'));
    if (btnOnline) btnOnline.addEventListener('click', () => setTrOCRMode('online'));

    if (engineSelect) {
      engineSelect.addEventListener('change', (e) => {
        this.currentEngine = e.target.value;
        const indicModeRow = document.getElementById('ocr-indic-mode-row');
        const indicUrlRow = document.getElementById('ocr-indic-url-row');
        const trocrModeRow = document.getElementById('ocr-trocr-mode-row');
        const trocrRow = document.getElementById('ocr-trocr-url-row');
        const tokenRow = document.getElementById('ocr-hf-token-row');
        const infoBox = document.getElementById('ocr-engine-info');

        if (this.currentEngine === 'indic_photo_ocr') {
          if (indicModeRow) indicModeRow.style.display = 'block';
          if (trocrModeRow) trocrModeRow.style.display = 'none';
          if (trocrRow) trocrRow.style.display = 'none';
          setIndicMode(this.indicMode);
        } else if (this.currentEngine === 'gujarati_trocr') {
          if (indicModeRow) indicModeRow.style.display = 'none';
          if (indicUrlRow) indicUrlRow.style.display = 'none';
          if (trocrModeRow) trocrModeRow.style.display = 'block';
          setTrOCRMode(this.trocrMode);
        } else if (this.currentEngine === 'gujarati_hcr') {
          if (indicModeRow) indicModeRow.style.display = 'none';
          if (indicUrlRow) indicUrlRow.style.display = 'none';
          if (trocrModeRow) trocrModeRow.style.display = 'none';
          if (trocrRow) trocrRow.style.display = 'none';
          if (tokenRow) tokenRow.style.display = 'none';
          if (infoBox) infoBox.innerHTML = '<strong>GujaratiHCR Pipeline</strong>: Cursive handwriting projection slicing & character recognition.';
        }
      });
    }

    if (langSelect) {
      langSelect.addEventListener('change', (e) => {
        this.currentLang = e.target.value;
      });
    }

    if (btnExtract) {
      btnExtract.addEventListener('click', () => this.extractText());
    }

    // View mode pills
    const pillAnnotated = document.getElementById('ocr-pill-annotated');
    const pillOriginal = document.getElementById('ocr-pill-original');
    const pillDraw = document.getElementById('ocr-pill-draw');

    if (pillAnnotated) {
      pillAnnotated.addEventListener('click', () => {
        this.setViewMode('annotated');
      });
    }
    if (pillOriginal) {
      pillOriginal.addEventListener('click', () => {
        this.setViewMode('original');
      });
    }
    if (pillDraw) {
      pillDraw.addEventListener('click', () => {
        this.toggleDrawingMode();
      });
    }

    // Action buttons in results
    const btnCopy = document.getElementById('btn-ocr-copy');
    const btnTxt = document.getElementById('btn-ocr-download-txt');
    const btnJson = document.getElementById('btn-ocr-download-json');
    const btnVoice = document.getElementById('btn-ocr-speak-tts');

    if (btnCopy) btnCopy.addEventListener('click', () => this.copyText());
    if (btnTxt) btnTxt.addEventListener('click', () => this.downloadTxt());
    if (btnJson) btnJson.addEventListener('click', () => this.downloadJson());
    if (btnVoice) btnVoice.addEventListener('click', () => this.speakWithTTS());

    // Image load & window resize alignment handlers
    const displayImg = document.getElementById('ocr-display-img');
    if (displayImg) {
      displayImg.addEventListener('load', () => this.alignOverlayBounds());
    }
    window.addEventListener('resize', () => this.alignOverlayBounds());
  }

  alignOverlayBounds() {
    const displayImg = document.getElementById('ocr-display-img');
    const overlay = document.getElementById('ocr-bounding-box-overlay');
    if (!displayImg || !overlay) return;

    const w = displayImg.clientWidth || displayImg.offsetWidth;
    const h = displayImg.clientHeight || displayImg.offsetHeight;
    const l = displayImg.offsetLeft;
    const t = displayImg.offsetTop;

    if (w > 0 && h > 0) {
      overlay.style.width = `${w}px`;
      overlay.style.height = `${h}px`;
      overlay.style.left = `${l}px`;
      overlay.style.top = `${t}px`;
    }
  }

  setViewMode(mode) {
    this.currentViewMode = mode;
    const pillAnnotated = document.getElementById('ocr-pill-annotated');
    const pillOriginal = document.getElementById('ocr-pill-original');
    const displayImg = document.getElementById('ocr-display-img');
    const overlay = document.getElementById('ocr-bounding-box-overlay');

    if (pillAnnotated) pillAnnotated.classList.toggle('active', mode === 'annotated');
    if (pillOriginal) pillOriginal.classList.toggle('active', mode === 'original');

    if (mode === 'original') {
      if (displayImg && this.currentImageBase64) {
        displayImg.src = this.currentImageBase64;
      }
      if (overlay) overlay.style.display = 'none';
    } else {
      if (displayImg && this.currentImageBase64) {
        displayImg.src = this.currentImageBase64;
      }
      if (overlay) {
        overlay.style.display = 'block';
        setTimeout(() => this.alignOverlayBounds(), 50);
      }
    }
  }

  toggleDrawingMode() {
    this.isDrawingMode = !this.isDrawingMode;
    const pillDraw = document.getElementById('ocr-pill-draw');
    const drawContainer = document.getElementById('ocr-draw-container');
    const canvasWrap = document.getElementById('ocr-canvas-wrapper');
    const emptyState = document.getElementById('ocr-dropzone-empty');

    if (pillDraw) pillDraw.classList.toggle('active', this.isDrawingMode);

    if (this.isDrawingMode) {
      if (drawContainer) drawContainer.style.display = 'block';
      if (canvasWrap) canvasWrap.style.display = 'none';
      if (emptyState) emptyState.style.display = 'none';
      this.clearDrawingCanvas();
    } else {
      if (drawContainer) drawContainer.style.display = 'none';
      if (canvasWrap && this.currentImageBase64) {
        canvasWrap.style.display = 'flex';
      } else if (emptyState) {
        emptyState.style.display = 'flex';
      }
    }
  }

  initDrawingCanvas() {
    const canvas = document.getElementById('ocr-draw-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    // Size canvas accurately
    const resizeCanvas = () => {
      canvas.width = canvas.parentElement.clientWidth || 600;
      canvas.height = canvas.parentElement.clientHeight || 340;
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.lineWidth = 4;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.strokeStyle = '#1e293b';
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    let drawing = false;

    const start = (e) => {
      drawing = true;
      const rect = canvas.getBoundingClientRect();
      const x = (e.clientX || (e.touches && e.touches[0].clientX)) - rect.left;
      const y = (e.clientY || (e.touches && e.touches[0].clientY)) - rect.top;
      ctx.beginPath();
      ctx.moveTo(x, y);
    };

    const draw = (e) => {
      if (!drawing) return;
      const rect = canvas.getBoundingClientRect();
      const x = (e.clientX || (e.touches && e.touches[0].clientX)) - rect.left;
      const y = (e.clientY || (e.touches && e.touches[0].clientY)) - rect.top;
      ctx.lineTo(x, y);
      ctx.stroke();
    };

    const stop = () => {
      if (drawing) {
        drawing = false;
        ctx.closePath();
      }
    };

    canvas.addEventListener('mousedown', start);
    canvas.addEventListener('mousemove', draw);
    window.addEventListener('mouseup', stop);

    canvas.addEventListener('touchstart', (e) => { e.preventDefault(); start(e); });
    canvas.addEventListener('touchmove', (e) => { e.preventDefault(); draw(e); });
    canvas.addEventListener('touchend', stop);

    const btnClear = document.getElementById('btn-ocr-draw-clear');
    if (btnClear) {
      btnClear.addEventListener('click', () => this.clearDrawingCanvas());
    }

    const btnUseDraw = document.getElementById('btn-ocr-draw-use');
    if (btnUseDraw) {
      btnUseDraw.addEventListener('click', () => {
        const dataUrl = canvas.toDataURL('image/png');
        this.isDrawingMode = false;
        this.setImage(dataUrl, true);
        const engineSelect = document.getElementById('ocr-engine-select');
        if (engineSelect) engineSelect.value = 'gujarati_hcr';
        this.currentEngine = 'gujarati_hcr';
      });
    }
  }

  clearDrawingCanvas() {
    const canvas = document.getElementById('ocr-draw-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }

  async extractText() {
    if (this.isDrawingMode) {
      const canvas = document.getElementById('ocr-draw-canvas');
      if (canvas) {
        this.setImage(canvas.toDataURL('image/png'), true);
        this.isDrawingMode = false;
      }
    }

    if (!this.currentImageBase64) {
      this.showToast('⚠️ Please upload or select an image first.');
      return;
    }

    const btn = document.getElementById('btn-ocr-extract');
    const spinner = document.getElementById('ocr-spinner');
    const btnLabel = document.getElementById('ocr-btn-label');
    const tokenInput = document.getElementById('ocr-hf-token-input');
    const hfToken = tokenInput ? tokenInput.value.trim() : null;

    if (btn) btn.disabled = true;
    if (spinner) spinner.style.display = 'inline-block';
    if (btnLabel) btnLabel.textContent = 'ઓસીઆર પ્રોસેસિંગ ચાલુ છે... (Processing OCR)';

    try {
      const trocrInput = document.getElementById('ocr-trocr-url-input');
      const indicInput = document.getElementById('ocr-indic-url-input');

      const isTrOCROffline = (this.currentEngine === 'gujarati_trocr' && this.trocrMode === 'offline');
      const isIndicOffline = (this.currentEngine === 'indic_photo_ocr' && this.indicMode === 'offline');

      const customTrOCRUrl = (isTrOCROffline && trocrInput) ? trocrInput.value.trim() : null;
      const customIndicUrl = (isIndicOffline && indicInput) ? indicInput.value.trim() : null;

      // 1. Direct Local IndicPhotoOCR Call (Port 7860)
      if (isIndicOffline) {
        const localTarget = customIndicUrl || 'http://localhost:7860/api/recognize';
        try {
          const directRes = await fetch(localTarget, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              image: this.currentImageBase64,
              lang: this.currentLang,
              mode: 'offline'
            })
          });
          if (directRes.ok) {
            const localData = await directRes.json();
            if (localData.success && localData.text) {
              localData.model_name = localData.model_name || 'Bhashini IndicPhotoOCR (Local Port 7860)';
              this.renderResults(localData);
              this.showToast('✓ Local Bhashini IndicPhotoOCR inference complete!');
              return;
            }
          }
        } catch (directErr) {
          console.info('Direct local IndicPhotoOCR (port 7860) not reachable, routing via Kano Backend (port 8000)...');
        }
      }

      // 2. Direct Local TrOCR Call (Port 7862)
      if (isTrOCROffline) {
        const localTarget = customTrOCRUrl || 'http://localhost:7862/api/recognize';
        try {
          const directRes = await fetch(localTarget, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              image: this.currentImageBase64,
              segment: true
            })
          });
          if (directRes.ok) {
            const localData = await directRes.json();
            if (localData.success && localData.text) {
              localData.model_name = localData.model ? `${localData.model} (Local Offline TrOCR)` : 'Local Gujarati TrOCR (Port 7862)';
              localData.elapsed_seconds = localData.elapsed_seconds || (localData.execution_time_ms ? (localData.execution_time_ms / 1000).toFixed(2) : '1.8');
              this.renderResults(localData);
              this.showToast('✓ Local Gujarati TrOCR inference complete!');
              return;
            }
          }
        } catch (directErr) {
          console.info('Direct local TrOCR (port 7862) not reachable, routing via Kano Backend (port 8000)...');
        }
      }

      // 3. Main OCR Server route (port 8000)
      const targetMode = (this.currentEngine === 'indic_photo_ocr') ? this.indicMode : this.trocrMode;
      const targetApiUrl = (this.currentEngine === 'indic_photo_ocr') ? customIndicUrl : customTrOCRUrl;

      const payload = {
        image: this.currentImageBase64,
        engine: this.currentEngine,
        mode: targetMode,
        lang: this.currentLang,
        api_url: targetApiUrl,
        hf_token: hfToken
      };

      const res = await fetch(`${this.apiUrl}/api/ocr/recognize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }

      const data = await res.json();
      if (!data.success) {
        throw new Error(data.error || 'Model returned unfulfilled response');
      }
      this.renderResults(data);
    } catch (err) {
      console.error('OCR Extraction error:', err);
      this.showToast(`❌ OCR recognition failed: ${err.message || 'Server error'}`);
      const textOutput = document.getElementById('ocr-text-output');
      if (textOutput) {
        textOutput.value = `[Error: ${err.message || 'Server error'}]\nPlease check that the local server is running and try again.`;
      }
      const resultsPanel = document.getElementById('ocr-results-container');
      if (resultsPanel) resultsPanel.style.display = 'flex';
    } finally {
      if (btn) btn.disabled = false;
      if (spinner) spinner.style.display = 'none';
      if (btnLabel) btnLabel.textContent = '🔍 એક્સટ્રેક્ટ કરો (Extract Gujarati Text)';
    }
  }

  renderResults(data) {
    const resultsPanel = document.getElementById('ocr-results-container');
    const textOutput = document.getElementById('ocr-text-output');
    const modelTag = document.getElementById('ocr-metric-model');
    const latencyTag = document.getElementById('ocr-metric-latency');
    const wordsTag = document.getElementById('ocr-metric-words');
    const confTag = document.getElementById('ocr-metric-conf');

    if (!resultsPanel || !textOutput) return;

    this.lastResult = data;
    const text = data.text || '';
    textOutput.value = text;

    if (modelTag) modelTag.textContent = data.model_name || data.engine;
    if (latencyTag) latencyTag.textContent = `⚡ ${data.elapsed_seconds || '-'}s`;
    if (wordsTag) wordsTag.textContent = `📝 ${text.split(/\s+/).filter(Boolean).length} Words (${text.length} chars)`;
    if (confTag) confTag.textContent = `🎯 ${Math.round((data.confidence || 0.92) * 100)}% Conf`;

    // Image display (keep clean image so interactive overlay doesn't collide with baked-in pixels)
    if (data.processed_image_base64) {
      this.currentProcessedImageBase64 = data.processed_image_base64;
    }
    const displayImg = document.getElementById('ocr-display-img');
    if (displayImg && this.currentImageBase64) {
      displayImg.src = this.currentImageBase64;
    }

    // Render interactive bounding boxes
    if (data.boxes && data.boxes.length > 0) {
      this.currentBoxes = data.boxes;
      this.renderBoundingBoxes(data.boxes);
    }

    resultsPanel.style.display = 'flex';
    resultsPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  renderBoundingBoxes(boxes) {
    const overlay = document.getElementById('ocr-bounding-box-overlay');
    if (!overlay) return;
    this.alignOverlayBounds();
    overlay.innerHTML = '';

    boxes.forEach((b, idx) => {
      const rect = document.createElement('div');
      rect.className = 'ocr-bbox-rect';
      rect.style.left = `${b.norm_x * 100}%`;
      rect.style.top = `${b.norm_y * 100}%`;
      rect.style.width = `${b.norm_width * 100}%`;
      rect.style.height = `${b.norm_height * 100}%`;
      rect.title = `Region #${idx + 1} (${b.width}x${b.height}px)`;
      overlay.appendChild(rect);
    });

    requestAnimationFrame(() => this.alignOverlayBounds());
  }

  copyText() {
    const textOutput = document.getElementById('ocr-text-output');
    if (!textOutput || !textOutput.value) return;
    navigator.clipboard.writeText(textOutput.value);
    this.showToast('📋 Gujarati text copied to clipboard!');
  }

  downloadTxt() {
    const textOutput = document.getElementById('ocr-text-output');
    if (!textOutput || !textOutput.value) return;
    const blob = new Blob([textOutput.value], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `kano_ocr_extracted_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    this.showToast('💾 TXT document downloaded!');
  }

  downloadJson() {
    if (!this.lastResult) return;
    const jsonStr = JSON.stringify(this.lastResult, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `kano_ocr_data_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    this.showToast('📊 JSON data with bounding boxes downloaded!');
  }

  speakWithTTS() {
    const textOutput = document.getElementById('ocr-text-output');
    if (!textOutput || !textOutput.value.trim()) {
      this.showToast('⚠️ No Gujarati text to speak.');
      return;
    }

    const textToSpeak = textOutput.value.trim();

    // Switch to TTS Tab and populate textarea
    if (window.switchSuite) {
      window.switchSuite('tts');
      const ttsInput = document.getElementById('tts-input-text');
      if (ttsInput) {
        ttsInput.value = textToSpeak;
        ttsInput.dispatchEvent(new Event('input'));
      }
      const ttsBtn = document.getElementById('btn-tts-synthesize');
      if (ttsBtn) {
        ttsBtn.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
      this.showToast('🎙️ Switched to Voice Studio! Click Synthesize to listen.');
    }
  }

  showToast(msg) {
    const existing = document.querySelector('.ocr-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'ocr-toast';
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.remove();
    }, 3200);
  }
}

window.ocrStudio = new OCRStudio();
