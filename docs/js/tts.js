/**
 * tts.js: KanoAI Gujarati Text-to-Speech Studio
 * Integrates AI4Bharat IndicF5 & Indic-TTS / Bodhan-AI Indic-Speak.
 * Provides interactive playback, canvas waveform visualization, and side-by-side comparison.
 */

class TTSStudio {
  constructor() {
    this.apiBaseUrl = 'http://localhost:8000';
    this.isServerConnected = false;
    this.currentEngine = 'mms_tts'; // 'mms_tts', 'piper_tts', 'espeak_ng', 'indic_tts', 'indic_f5', or 'compare'
    this.audioContext = null;
    this.activeAudio = null;
    this.activeAudioBuffer = null;
    this.isPlaying = false;
    this.playbackRate = 1.0;
    this.history = [];

    // Presets fallback if offline
    this.presets = [
      { id: 'greeting', label: 'નમસ્તે (Greetings)', text: 'નમસ્તે! ગુજરાતી ભાષા KanoAI માં આપનું હાર્દિક સ્વાગત છે.' },
      { id: 'daily', label: 'રોજિંદી વાતચીત (Daily Life)', text: 'કેમ છો? આજે હવામાન ખૂબ જ સરસ છે અને અમે બહાર ફરવા જઈ રહ્યા છીએ.' },
      { id: 'literature', label: 'ગુજરાતી ભાષા (Literature)', text: 'ગુજરાતી ભાષા ખૂબ જ સમૃદ્ધ, મીઠી અને પ્રાચીન સાહિત્યિક પરંપરા ધરાવતી ભાષા છે.' },
      { id: 'numbers', label: 'આંકડા ૧-૧૦ (Numbers)', text: 'એક, બે, ત્રણ, ચાર, પાંચ, છ, સાત, આઠ, નવ, દસ.' },
      { id: 'alphabet', label: 'કક્કો વ્યંજન (Consonants)', text: 'ક ખ ગ ઘ ચ છ જ ઝ ટ ઠ ડ ઢ ણ ત થ દ ધ ન પ ફ બ ભ મ ય ર લ વ શ ષ સ હ ળ ક્ષ જ્ઞ.' }
    ];

    this.speakers = [
      { id: 'dhara', name: 'Dhara (ધરા)', gender: 'Female', desc: 'Warm, natural, and expressive female voice with clear Gujarati diction.' },
      { id: 'parth', name: 'Parth (પાર્થ)', gender: 'Male', desc: 'Deep, articulate, and confident male voice speaking standard Gujarati.' }
    ];
  }

  async init() {
    this.bindDOM();
    this.renderPresets();
    await this.checkServerConnection();
    this.updateEngineUI();
    this.loadHistory();
  }

  bindDOM() {
    // Engine selector cards
    document.querySelectorAll('.tts-engine-card').forEach(card => {
      card.addEventListener('click', () => {
        const engine = card.getAttribute('data-engine');
        this.setEngine(engine);
      });
    });

    // Engine selector dropdown inside Settings
    const engineSelect = document.getElementById('tts-engine-select');
    if (engineSelect) {
      engineSelect.addEventListener('change', (e) => {
        this.setEngine(e.target.value);
      });
    }

    // Meta MMS-TTS Model select listener
    const mmsModelSelect = document.getElementById('tts-mms-model-select');
    if (mmsModelSelect) {
      mmsModelSelect.addEventListener('change', () => {
        const preview = document.getElementById('tts-mms-preview');
        if (preview) {
          if (mmsModelSelect.value.includes('hin')) {
            preview.textContent = 'Hindi VITS model (facebook/mms-tts-hin). Variational inference running locally on CPU/MPS.';
          } else {
            preview.textContent = 'End-to-end Variational Inference TTS (facebook/mms-tts-guj) running 100% locally on CPU/MPS with zero cloud dependency.';
          }
        }
      });
    }

    // Text area live counter
    const textarea = document.getElementById('tts-input-text');
    if (textarea) {
      textarea.addEventListener('input', () => {
        const text = textarea.value.trim();
        const charCount = document.getElementById('tts-char-count');
        const wordCount = document.getElementById('tts-word-count');
        if (charCount) charCount.textContent = `${text.length} chars`;
        if (wordCount) wordCount.textContent = `${text ? text.split(/\s+/).length : 0} words`;
      });
    }

    // Synthesize button
    const synthBtn = document.getElementById('btn-tts-synthesize');
    if (synthBtn) {
      synthBtn.addEventListener('click', () => this.synthesize());
    }

    // Speaker change listener
    const speakerSelect = document.getElementById('tts-speaker-select');
    if (speakerSelect) {
      speakerSelect.addEventListener('change', (e) => {
        const spk = this.speakers.find(s => s.id === e.target.value);
        const preview = document.getElementById('tts-speaker-preview');
        if (preview && spk) {
          preview.textContent = spk.desc;
        }
      });
    }

    // Hugging Face Token input listener
    const tokenInput = document.getElementById('tts-hf-token-input');
    if (tokenInput) {
      const savedToken = localStorage.getItem('kano_hf_token') || '';
      tokenInput.value = savedToken;
      tokenInput.addEventListener('input', (e) => {
        localStorage.setItem('kano_hf_token', e.target.value.trim());
      });
    }

    // IndicF5 Endpoint selector
    const f5EndpointSelect = document.getElementById('tts-indicf5-endpoint-select');
    const f5CustomUrlInput = document.getElementById('tts-indicf5-custom-url');
    const f5TokenGroup = document.getElementById('tts-indicf5-token-group');
    const f5Hint = document.getElementById('tts-indicf5-endpoint-hint');
    if (f5EndpointSelect && f5CustomUrlInput) {
      const savedF5Endpoint = localStorage.getItem('kano_f5_api_mode') || 'local';
      let savedF5Url = localStorage.getItem('kano_f5_custom_url') || 'http://localhost:7865';
      if (savedF5Url.includes('7860')) {
        savedF5Url = savedF5Url.replace('7860', '7865');
        localStorage.setItem('kano_f5_custom_url', savedF5Url);
      }
      f5EndpointSelect.value = savedF5Endpoint;
      f5CustomUrlInput.value = savedF5Url;
      f5CustomUrlInput.style.display = savedF5Endpoint === 'custom' ? 'block' : 'none';
      if (f5Hint) f5Hint.style.display = savedF5Endpoint === 'local' ? 'block' : 'none';
      if (f5TokenGroup) f5TokenGroup.style.display = savedF5Endpoint === 'cloud' ? 'block' : 'none';

      f5EndpointSelect.addEventListener('change', (e) => {
        const mode = e.target.value;
        localStorage.setItem('kano_f5_api_mode', mode);
        f5CustomUrlInput.style.display = mode === 'custom' ? 'block' : 'none';
        if (f5Hint) f5Hint.style.display = mode === 'local' ? 'block' : 'none';
        if (f5TokenGroup) f5TokenGroup.style.display = mode === 'cloud' ? 'block' : 'none';
      });

      f5CustomUrlInput.addEventListener('input', (e) => {
        localStorage.setItem('kano_f5_custom_url', e.target.value.trim());
      });
    }

    // Indic-TTS Endpoint selector
    const ttsEndpointSelect = document.getElementById('tts-indictts-endpoint-select');
    const ttsCustomUrlInput = document.getElementById('tts-indictts-custom-url');
    const ttsHint = document.getElementById('tts-indictts-endpoint-hint');
    if (ttsEndpointSelect && ttsCustomUrlInput) {
      const savedTtsEndpoint = localStorage.getItem('kano_tts_api_mode') || 'local';
      const savedTtsUrl = localStorage.getItem('kano_tts_custom_url') || 'http://localhost:7861';
      ttsEndpointSelect.value = savedTtsEndpoint;
      ttsCustomUrlInput.value = savedTtsUrl;
      ttsCustomUrlInput.style.display = savedTtsEndpoint === 'custom' ? 'block' : 'none';
      if (ttsHint) ttsHint.style.display = savedTtsEndpoint === 'local' ? 'block' : 'none';

      ttsEndpointSelect.addEventListener('change', (e) => {
        const mode = e.target.value;
        localStorage.setItem('kano_tts_api_mode', mode);
        ttsCustomUrlInput.style.display = mode === 'custom' ? 'block' : 'none';
        if (ttsHint) ttsHint.style.display = mode === 'local' ? 'block' : 'none';
      });

      ttsCustomUrlInput.addEventListener('input', (e) => {
        localStorage.setItem('kano_tts_custom_url', e.target.value.trim());
      });
    }

    // Parler Endpoint selector
    const parlerEndpointSelect = document.getElementById('tts-parler-endpoint-select');
    const parlerCustomUrlInput = document.getElementById('tts-parler-custom-url');
    const parlerHint = document.getElementById('tts-parler-endpoint-hint');
    if (parlerEndpointSelect && parlerCustomUrlInput) {
      const savedParlerEndpoint = localStorage.getItem('kano_parler_api_mode') || 'cloud';
      const savedParlerUrl = localStorage.getItem('kano_parler_custom_url') || 'http://localhost:7861';
      parlerEndpointSelect.value = savedParlerEndpoint;
      parlerCustomUrlInput.value = savedParlerUrl;
      parlerCustomUrlInput.style.display = savedParlerEndpoint === 'custom' ? 'block' : 'none';
      const updateParlerHint = (mode) => {
        if (!parlerHint) return;
        if (mode === 'local') parlerHint.textContent = '💻 Local Indic-TTS / Parler server (http://localhost:7861 - Offline Fast).';
        else if (mode === 'cloud') parlerHint.textContent = '🌐 Cloud ZeroGPU backend on Hugging Face Spaces (ai4bharat-indic-parler-tts).';
        else parlerHint.textContent = '✏️ Custom Parler-TTS inference server URL.';
      };
      updateParlerHint(savedParlerEndpoint);
      parlerEndpointSelect.addEventListener('change', (e) => {
        const mode = e.target.value;
        localStorage.setItem('kano_parler_api_mode', mode);
        parlerCustomUrlInput.style.display = mode === 'custom' ? 'block' : 'none';
        updateParlerHint(mode);
      });
      parlerCustomUrlInput.addEventListener('input', (e) => {
        localStorage.setItem('kano_parler_custom_url', e.target.value.trim());
      });
    }

    // Bhashini Endpoint selector
    const bhashiniEndpointSelect = document.getElementById('tts-bhashini-endpoint-select');
    const bhashiniCustomUrlInput = document.getElementById('tts-bhashini-custom-url');
    const bhashiniHint = document.getElementById('tts-bhashini-endpoint-hint');
    const bhashiniKeyGroup = document.getElementById('tts-bhashini-key-group');
    if (bhashiniEndpointSelect && bhashiniCustomUrlInput) {
      const savedBhashiniEndpoint = localStorage.getItem('kano_bhashini_api_mode') || 'local';
      const savedBhashiniUrl = localStorage.getItem('kano_bhashini_custom_url') || 'https://dhruva-api.bhashini.gov.in/services/inference/pipeline';
      bhashiniEndpointSelect.value = savedBhashiniEndpoint;
      bhashiniCustomUrlInput.value = savedBhashiniUrl;
      bhashiniCustomUrlInput.style.display = savedBhashiniEndpoint === 'custom' ? 'block' : 'none';
      if (bhashiniKeyGroup) bhashiniKeyGroup.style.display = savedBhashiniEndpoint === 'local' ? 'none' : 'block';
      const updateBhashiniHint = (mode) => {
        if (!bhashiniHint) return;
        if (mode === 'local') bhashiniHint.textContent = '💻 100% Local Offline Neural Engine (Priyamvada female / MMS male). Zero cloud or external server connection needed.';
        else if (mode === 'cloud') bhashiniHint.textContent = '🌐 Official Digital India Bhashini Mission / IIT Madras cloud infrastructure. Requires ULCA API key.';
        else bhashiniHint.textContent = '✏️ Custom Bhashini inference pipeline endpoint URL.';
      };
      updateBhashiniHint(savedBhashiniEndpoint);
      bhashiniEndpointSelect.addEventListener('change', (e) => {
        const mode = e.target.value;
        localStorage.setItem('kano_bhashini_api_mode', mode);
        bhashiniCustomUrlInput.style.display = mode === 'custom' ? 'block' : 'none';
        if (bhashiniKeyGroup) bhashiniKeyGroup.style.display = mode === 'local' ? 'none' : 'block';
        updateBhashiniHint(mode);
      });
      bhashiniCustomUrlInput.addEventListener('input', (e) => {
        localStorage.setItem('kano_bhashini_custom_url', e.target.value.trim());
      });
    }

    // Google Cloud Endpoint selector
    const googleEndpointSelect = document.getElementById('tts-google-endpoint-select');
    const googleCustomUrlInput = document.getElementById('tts-google-custom-url');
    const googleHint = document.getElementById('tts-google-endpoint-hint');
    const googleKeyGroup = document.getElementById('tts-google-key-group');
    if (googleEndpointSelect && googleCustomUrlInput) {
      const savedGoogleEndpoint = localStorage.getItem('kano_google_api_mode') || 'cloud';
      const savedGoogleUrl = localStorage.getItem('kano_google_custom_url') || 'https://texttospeech.googleapis.com/v1/text:synthesize';
      googleEndpointSelect.value = savedGoogleEndpoint;
      googleCustomUrlInput.value = savedGoogleUrl;
      googleCustomUrlInput.style.display = savedGoogleEndpoint === 'custom' ? 'block' : 'none';
      if (googleKeyGroup) googleKeyGroup.style.display = savedGoogleEndpoint === 'local' ? 'none' : 'block';
      const updateGoogleHint = (mode) => {
        if (!googleHint) return;
        if (mode === 'local') googleHint.textContent = '💻 100% Local Offline Engine Fallback (Priyamvada / MMS). Runs completely offline without API key.';
        else if (mode === 'cloud') googleHint.textContent = '🌐 Official Google Cloud TTS API (texttospeech.googleapis.com). Requires API key.';
        else googleHint.textContent = '✏️ Custom Google TTS proxy or endpoint URL.';
      };
      updateGoogleHint(savedGoogleEndpoint);
      googleEndpointSelect.addEventListener('change', (e) => {
        const mode = e.target.value;
        localStorage.setItem('kano_google_api_mode', mode);
        googleCustomUrlInput.style.display = mode === 'custom' ? 'block' : 'none';
        if (googleKeyGroup) googleKeyGroup.style.display = mode === 'local' ? 'none' : 'block';
        updateGoogleHint(mode);
      });
      googleCustomUrlInput.addEventListener('input', (e) => {
        localStorage.setItem('kano_google_custom_url', e.target.value.trim());
      });
    }

    // MMS-TTS Endpoint selector
    const mmsEndpointSelect = document.getElementById('tts-mms-endpoint-select');
    const mmsCustomUrlInput = document.getElementById('tts-mms-custom-url');
    if (mmsEndpointSelect && mmsCustomUrlInput) {
      const savedMmsEndpoint = localStorage.getItem('kano_mms_api_mode') || 'local';
      const savedMmsUrl = localStorage.getItem('kano_mms_custom_url') || 'http://localhost:8000';
      mmsEndpointSelect.value = savedMmsEndpoint;
      mmsCustomUrlInput.value = savedMmsUrl;
      mmsCustomUrlInput.style.display = savedMmsEndpoint === 'custom' ? 'block' : 'none';
      mmsEndpointSelect.addEventListener('change', (e) => {
        const mode = e.target.value;
        localStorage.setItem('kano_mms_api_mode', mode);
        mmsCustomUrlInput.style.display = mode === 'custom' ? 'block' : 'none';
      });
      mmsCustomUrlInput.addEventListener('input', (e) => {
        localStorage.setItem('kano_mms_custom_url', e.target.value.trim());
      });
    }

    // Piper TTS Endpoint selector
    const piperEndpointSelect = document.getElementById('tts-piper-endpoint-select');
    const piperCustomUrlInput = document.getElementById('tts-piper-custom-url');
    if (piperEndpointSelect && piperCustomUrlInput) {
      const savedPiperEndpoint = localStorage.getItem('kano_piper_api_mode') || 'local';
      const savedPiperUrl = localStorage.getItem('kano_piper_custom_url') || 'http://localhost:8000';
      piperEndpointSelect.value = savedPiperEndpoint;
      piperCustomUrlInput.value = savedPiperUrl;
      piperCustomUrlInput.style.display = savedPiperEndpoint === 'custom' ? 'block' : 'none';
      piperEndpointSelect.addEventListener('change', (e) => {
        const mode = e.target.value;
        localStorage.setItem('kano_piper_api_mode', mode);
        piperCustomUrlInput.style.display = mode === 'custom' ? 'block' : 'none';
      });
      piperCustomUrlInput.addEventListener('input', (e) => {
        localStorage.setItem('kano_piper_custom_url', e.target.value.trim());
      });
    }

    // Speech Pacing selector
    const pacingSelect = document.getElementById('tts-pacing-select');
    if (pacingSelect) {
      const savedSpeed = localStorage.getItem('kano_tts_speed') || '0.75';
      pacingSelect.value = savedSpeed;
      this.playbackRate = parseFloat(savedSpeed);
      pacingSelect.addEventListener('change', (e) => {
        const val = e.target.value;
        localStorage.setItem('kano_tts_speed', val);
        this.playbackRate = parseFloat(val);
      });
    }

    // Parler-TTS Presets listener
    const parlerPresetSelect = document.getElementById('tts-parler-preset-select');
    const parlerPromptInput = document.getElementById('tts-parler-prompt-input');
    const parlerPresetsMap = {
      'warm_female': 'A female Gujarati speaker speaks in a calm, cheerful voice with natural pacing and studio quality audio.',
      'expressive_story': 'A female Gujarati storyteller speaks in an expressive, lively tone with clear diction and natural breath pauses.',
      'news_broadcast': 'A male Gujarati narrator speaks in a deep, articulate, and confident broadcast tone with steady pacing.',
      'gentle_whisper': 'A soft-spoken female Gujarati speaker speaks in a gentle, warm whisper with close microphone proximity.',
    };
    if (parlerPresetSelect && parlerPromptInput) {
      if (!parlerPromptInput.value.trim() && parlerPresetsMap[parlerPresetSelect.value]) {
        parlerPromptInput.value = parlerPresetsMap[parlerPresetSelect.value];
      }
      parlerPresetSelect.addEventListener('change', (e) => {
        if (parlerPresetsMap[e.target.value]) {
          parlerPromptInput.value = parlerPresetsMap[e.target.value];
        }
      });
    }

    // Initialize Web Speech API Voices
    this.initWebSpeechVoices();

    // Bhashini and Google Cloud API keys in localStorage
    const bhashiniKeyInput = document.getElementById('tts-bhashini-key-input');
    if (bhashiniKeyInput) {
      bhashiniKeyInput.value = localStorage.getItem('kano_bhashini_tts_key') || '';
      bhashiniKeyInput.addEventListener('input', (e) => {
        localStorage.setItem('kano_bhashini_tts_key', e.target.value.trim());
      });
    }

    const googleKeyInput = document.getElementById('tts-google-key-input');
    if (googleKeyInput) {
      googleKeyInput.value = localStorage.getItem('kano_google_tts_key') || '';
      googleKeyInput.addEventListener('input', (e) => {
        localStorage.setItem('kano_google_tts_key', e.target.value.trim());
      });
    }
  }

  initWebSpeechVoices() {
    if (!('speechSynthesis' in window)) return;
    const voiceSelect = document.getElementById('tts-webspeech-voice-select');
    if (!voiceSelect) return;

    const populate = () => {
      const voices = window.speechSynthesis.getVoices();
      if (!voices || voices.length === 0) return;

      voiceSelect.innerHTML = '';
      const guVoices = voices.filter(v => v.lang && (v.lang.toLowerCase().startsWith('gu') || v.lang.toLowerCase().includes('guj')));
      const inVoices = voices.filter(v => v.lang && v.lang.toLowerCase().includes('in') && !guVoices.includes(v));
      const otherVoices = voices.filter(v => !guVoices.includes(v) && !inVoices.includes(v));

      const addGroup = (groupLabel, list) => {
        if (!list.length) return;
        const optgroup = document.createElement('optgroup');
        optgroup.label = groupLabel;
        list.forEach(v => {
          const opt = document.createElement('option');
          opt.value = v.name;
          opt.textContent = `${v.name} (${v.lang})`;
          optgroup.appendChild(opt);
        });
        voiceSelect.appendChild(optgroup);
      };

      if (guVoices.length > 0) {
        addGroup('🌟 Native Gujarati Voices (gu-IN)', guVoices);
      }
      if (inVoices.length > 0) {
        addGroup('🇮🇳 Other Indian Language Voices', inVoices);
      }
      addGroup('🌐 System Voices', otherVoices.slice(0, 15));

      if (guVoices.length > 0) {
        voiceSelect.value = guVoices[0].name;
      }
    };

    populate();
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = populate;
    }
  }

  async checkServerConnection() {
    const badge = document.getElementById('tts-server-status');
    const badgeText = document.getElementById('tts-status-text');
    
    try {
      const res = await fetch(`${this.apiBaseUrl}/api/health`, { method: 'GET', signal: AbortSignal.timeout(2000) });
      if (res.ok) {
        this.isServerConnected = true;
        if (badge) {
          badge.className = 'tts-status-badge connected';
          if (badgeText) badgeText.textContent = 'Local Python Engine: Online';
        }
        this.fetchServerPresets();
        return;
      }
    } catch (e) {
      // Offline fallback
    }

    this.isServerConnected = false;
    if (badge) {
      badge.className = 'tts-status-badge fallback';
      if (badgeText) badgeText.textContent = 'Server: Standby / Direct Cloud API';
    }
  }

  async fetchServerPresets() {
    try {
      const res = await fetch(`${this.apiBaseUrl}/api/presets`);
      if (res.ok) {
        const data = await res.json();
        if (data.samples && data.samples.length > 0) {
          this.presets = data.samples.map(s => ({ id: s.id, label: s.title, text: s.text }));
          this.renderPresets();
        }
      }
    } catch (e) {}
  }

  renderPresets() {
    const container = document.getElementById('tts-presets-list');
    if (!container) return;

    container.innerHTML = '';
    this.presets.forEach(p => {
      const chip = document.createElement('button');
      chip.className = 'tts-preset-chip';
      chip.textContent = p.label;
      chip.title = p.text;
      chip.addEventListener('click', () => {
        const textarea = document.getElementById('tts-input-text');
        if (textarea) {
          textarea.value = p.text;
          textarea.dispatchEvent(new Event('input'));
          textarea.focus();
        }
      });
      container.appendChild(chip);
    });
  }

  setEngine(engine) {
    this.currentEngine = engine;
    const engineSelect = document.getElementById('tts-engine-select');
    if (engineSelect && engineSelect.value !== engine) {
      engineSelect.value = engine;
    }
    this.updateEngineUI();
  }

  updateEngineUI() {
    const mmsSettings = document.getElementById('tts-mms-settings');
    const piperSettings = document.getElementById('tts-piper-settings');
    const parlerSettings = document.getElementById('tts-parler-settings');
    const webspeechSettings = document.getElementById('tts-webspeech-settings');
    const bhashiniSettings = document.getElementById('tts-bhashini-settings');
    const googleSettings = document.getElementById('tts-google-settings');
    const espeakSettings = document.getElementById('tts-espeak-settings');
    const indicTTSSettings = document.getElementById('tts-indictts-settings');
    const indicF5Settings = document.getElementById('tts-indicf5-settings');
    const badgePill = document.getElementById('tts-engine-badge-pill');
    const engineHint = document.getElementById('tts-engine-hint');

    const badges = {
      'mms_tts': '100% Offline VITS',
      'piper_tts': 'Ultra-Fast ONNX',
      'parler_tts': '🎙️ Prompt-Guided Codec',
      'web_speech': '⚡ 0ms Device Native Voice',
      'bhashini_tts': '🏛️ Digital India / IIT Madras Benchmark',
      'google_cloud_tts': '☁️ Wavenet / Neural2 Studio',
      'espeak_ng': '🤖 Robotic Formant (IPA Debugger)',
      'indic_tts': 'Natural Neural Voice',
      'indic_f5': 'Voice Clone & Flow-Matching',
      'compare': 'Side-by-Side Comparison'
    };
    if (badgePill && badges[this.currentEngine]) {
      badgePill.textContent = badges[this.currentEngine];
    }

    const hints = {
      'mms_tts': 'End-to-end Variational Inference TTS (facebook/mms-tts-guj) running 100% locally on CPU/MPS with zero cloud dependency. Warm, natural human voice.',
      'piper_tts': 'Ultra-fast neural text-to-speech running locally via ONNX Runtime with sub-100ms CPU inference and natural voices.',
      'parler_tts': 'Prompt-guided expressive audio codec synthesis (Parler-TTS Indic). Tailor mood, tone, room acoustics, and voice style through natural language prompts.',
      'web_speech': 'Direct hardware speech synthesis via your browser\'s native Web Speech API (gu-IN). Instant zero-latency synthesis directly on your device without server calls.',
      'bhashini_tts': 'Official government benchmark neural TTS from Digital India Bhashini Mission & IIT Madras. Features male and female formal academic diction.',
      'google_cloud_tts': 'High-fidelity commercial speech synthesis powered by Google Cloud Text-to-Speech (gu-IN Wavenet and Neural2 voices) with studio broadcast quality.',
      'espeak_ng': 'Rule-based formant synthesizer (<2 MB, zero neural weights) with classic mechanical timbre. Ideal for IPA & phoneme diagnostics. For human voice, use Meta MMS-TTS, Piper, or Parler-TTS.',
      'indic_tts': 'Multi-speaker neural TTS with crystal-clear native Gujarati pronunciation by Dhara & Parth.',
      'indic_f5': 'Zero-shot flow-matching voice conditioning and cloning with natural human prosody & rhythm.',
      'compare': '⚖️ Concurrent multi-engine evaluation across all models for side-by-side benchmarking.'
    };
    if (engineHint && hints[this.currentEngine]) {
      engineHint.textContent = hints[this.currentEngine];
    }

    if (mmsSettings) mmsSettings.style.display = (this.currentEngine === 'mms_tts') ? 'flex' : 'none';
    if (piperSettings) piperSettings.style.display = (this.currentEngine === 'piper_tts' || this.currentEngine === 'compare') ? 'flex' : 'none';
    if (parlerSettings) parlerSettings.style.display = (this.currentEngine === 'parler_tts' || this.currentEngine === 'compare') ? 'flex' : 'none';
    if (webspeechSettings) webspeechSettings.style.display = (this.currentEngine === 'web_speech') ? 'flex' : 'none';
    if (bhashiniSettings) bhashiniSettings.style.display = (this.currentEngine === 'bhashini_tts' || this.currentEngine === 'compare') ? 'flex' : 'none';
    if (googleSettings) googleSettings.style.display = (this.currentEngine === 'google_cloud_tts' || this.currentEngine === 'compare') ? 'flex' : 'none';
    if (espeakSettings) espeakSettings.style.display = (this.currentEngine === 'espeak_ng' || this.currentEngine === 'compare') ? 'flex' : 'none';
    if (indicTTSSettings) indicTTSSettings.style.display = (this.currentEngine === 'indic_tts' || this.currentEngine === 'compare') ? 'flex' : 'none';
    if (indicF5Settings) indicF5Settings.style.display = (this.currentEngine === 'indic_f5' || this.currentEngine === 'compare') ? 'flex' : 'none';
  }

  async synthesize() {
    const textarea = document.getElementById('tts-input-text');
    const text = textarea ? textarea.value.trim() : '';
    if (!text) {
      alert('કૃપા કરીને ગુજરાતી લખાણ દાખલ કરો (Please enter Gujarati text to synthesize).');
      if (textarea) textarea.focus();
      return;
    }

    if (this.currentEngine === 'web_speech') {
      return this.synthesizeWebSpeech(text);
    }

    const synthBtn = document.getElementById('btn-tts-synthesize');
    const synthBtnText = document.getElementById('tts-btn-label');
    const synthSpinner = document.getElementById('tts-spinner');
    
    // UI Loading state
    if (synthBtn) synthBtn.disabled = true;
    if (synthSpinner) synthSpinner.style.display = 'inline-block';
    
    const startTime = performance.now();
    let timerInterval = null;
    if (synthBtnText) {
      synthBtnText.textContent = 'સ્પીચ જનરેટ થઈ રહ્યું છે... (0.0s)';
      timerInterval = setInterval(() => {
        const secs = ((performance.now() - startTime) / 1000).toFixed(1);
        synthBtnText.textContent = `સ્પીચ જનરેટ થઈ રહ્યું છે... (${secs}s)`;
      }, 100);
    }

    try {
      const mmsModelSelect = document.getElementById('tts-mms-model-select');
      const mmsModel = mmsModelSelect ? mmsModelSelect.value : 'facebook/mms-tts-guj';
      const speakerSelect = document.getElementById('tts-speaker-select');
      const speakerId = speakerSelect ? speakerSelect.value : 'dhara';
      const piperVoiceSelect = document.getElementById('tts-piper-voice-select');
      const piperVoice = piperVoiceSelect ? piperVoiceSelect.value : 'rohan';
      const espeakLangSelect = document.getElementById('tts-espeak-lang-select');
      const espeakLang = espeakLangSelect ? espeakLangSelect.value : 'gu';
      const espeakVariantSelect = document.getElementById('tts-espeak-variant-select');
      const espeakVariant = espeakVariantSelect ? espeakVariantSelect.value : 'klatt';

      // Parler-TTS inputs
      const parlerPromptInput = document.getElementById('tts-parler-prompt-input');
      const parlerEndpointSelect = document.getElementById('tts-parler-endpoint-select');
      const parlerCustomUrlInput = document.getElementById('tts-parler-custom-url');
      const parlerPrompt = parlerPromptInput ? parlerPromptInput.value.trim() : '';
      let parlerApiUrl = 'https://ai4bharat-indic-parler-tts.hf.space';
      if (parlerEndpointSelect) {
        if (parlerEndpointSelect.value === 'local') parlerApiUrl = 'http://localhost:7861';
        else if (parlerEndpointSelect.value === 'cloud') parlerApiUrl = 'https://ai4bharat-indic-parler-tts.hf.space';
        else if (parlerEndpointSelect.value === 'custom' && parlerCustomUrlInput) {
          parlerApiUrl = parlerCustomUrlInput.value.trim() || 'http://localhost:7861';
        }
      }

      // Bhashini inputs
      const bhashiniVoiceSelect = document.getElementById('tts-bhashini-voice-select');
      const bhashiniEndpointSelect = document.getElementById('tts-bhashini-endpoint-select');
      const bhashiniCustomUrlInput = document.getElementById('tts-bhashini-custom-url');
      const bhashiniKeyInput = document.getElementById('tts-bhashini-key-input');
      const bhashiniVoice = bhashiniVoiceSelect ? bhashiniVoiceSelect.value : 'gu_female';
      const bhashiniEndpointMode = bhashiniEndpointSelect ? bhashiniEndpointSelect.value : 'local';
      let bhashiniUrl = 'https://dhruva-api.bhashini.gov.in/services/inference/pipeline';
      if (bhashiniEndpointMode === 'custom' && bhashiniCustomUrlInput) {
        bhashiniUrl = bhashiniCustomUrlInput.value.trim() || bhashiniUrl;
      }
      const bhashiniKey = (bhashiniEndpointMode === 'local') ? '' : (bhashiniKeyInput ? bhashiniKeyInput.value.trim() : (localStorage.getItem('kano_bhashini_tts_key') || ''));

      // Google Cloud inputs
      const googleVoiceSelect = document.getElementById('tts-google-voice-select');
      const googleEndpointSelect = document.getElementById('tts-google-endpoint-select');
      const googleCustomUrlInput = document.getElementById('tts-google-custom-url');
      const googleKeyInput = document.getElementById('tts-google-key-input');
      const googleVoice = googleVoiceSelect ? googleVoiceSelect.value : 'gu-IN-Wavenet-A';
      const googleEndpointMode = googleEndpointSelect ? googleEndpointSelect.value : 'cloud';
      let googleUrl = 'https://texttospeech.googleapis.com/v1/text:synthesize';
      if (googleEndpointMode === 'custom' && googleCustomUrlInput) {
        googleUrl = googleCustomUrlInput.value.trim() || googleUrl;
      }
      const googleKey = (googleEndpointMode === 'local') ? '' : (googleKeyInput ? googleKeyInput.value.trim() : (localStorage.getItem('kano_google_tts_key') || ''));

      const tokenInput = document.getElementById('tts-hf-token-input');
      const hfToken = (tokenInput && tokenInput.value.trim()) || localStorage.getItem('kano_hf_token') || '';

      // Resolve IndicF5 endpoint
      const f5Select = document.getElementById('tts-indicf5-endpoint-select');
      const f5Custom = document.getElementById('tts-indicf5-custom-url');
      let f5ApiUrl = 'http://localhost:7865';
      if (f5Select) {
        if (f5Select.value === 'local') f5ApiUrl = 'http://localhost:7865';
        else if (f5Select.value === 'cloud') f5ApiUrl = 'ai4bharat/IndicF5';
        else if (f5Select.value === 'custom' && f5Custom) {
          let customUrl = f5Custom.value.trim() || 'http://localhost:7865';
          if (customUrl.includes(':7860')) customUrl = customUrl.replace(':7860', ':7865');
          f5ApiUrl = customUrl;
        }
      }

      // Resolve Indic-TTS endpoint
      const ttsSelect = document.getElementById('tts-indictts-endpoint-select');
      const ttsCustom = document.getElementById('tts-indictts-custom-url');
      let ttsApiUrl = 'http://localhost:7861';
      if (ttsSelect) {
        if (ttsSelect.value === 'local') ttsApiUrl = 'http://localhost:7861';
        else if (ttsSelect.value === 'cloud') ttsApiUrl = 'https://ai4bharat-indic-parler-tts.hf.space';
        else if (ttsSelect.value === 'custom' && ttsCustom) ttsApiUrl = ttsCustom.value.trim() || 'http://localhost:7861';
      }

      // Resolve Pacing / Speed
      const pacingSelect = document.getElementById('tts-pacing-select');
      const speed = pacingSelect ? parseFloat(pacingSelect.value) || 0.75 : 0.75;
      this.playbackRate = speed;

      const parlerPresetSelect = document.getElementById('tts-parler-preset-select');
      const parlerPreset = parlerPresetSelect ? parlerPresetSelect.value : 'warm_female';

      // Infer gender across engines
      let gender = 'female';
      if (this.currentEngine === 'parler_tts') {
        const textToCheck = (parlerPrompt + ' ' + (parlerPreset || '')).toLowerCase();
        if (textToCheck.includes('female') || textToCheck.includes('woman') || textToCheck.includes('girl') || textToCheck.includes('warm_female') || textToCheck.includes('expressive_story') || textToCheck.includes('gentle_whisper')) {
          gender = 'female';
        } else if (textToCheck.includes('male') || textToCheck.includes('man') || textToCheck.includes('boy') || textToCheck.includes('news_broadcast')) {
          gender = 'male';
        }
      } else if (this.currentEngine === 'indic_tts') {
        gender = (speakerId === 'parth' || speakerId === 'male') ? 'male' : 'female';
      } else if (this.currentEngine === 'bhashini_tts') {
        gender = bhashiniVoice.includes('male') && !bhashiniVoice.includes('female') ? 'male' : 'female';
      } else if (this.currentEngine === 'piper_tts') {
        gender = piperVoice === 'priyamvada' ? 'female' : 'male';
      } else if (this.currentEngine === 'google_cloud_tts') {
        gender = (googleVoice.endsWith('B') || googleVoice.endsWith('D')) ? 'male' : 'female';
      }

      let pitchFactor = 1.0;
      if (this.currentEngine === 'parler_tts') {
        if (parlerPreset === 'warm_female') pitchFactor = 1.19;
        else if (parlerPreset === 'expressive_story') pitchFactor = 1.22;
        else if (parlerPreset === 'gentle_whisper') pitchFactor = 1.15;
        else if (parlerPreset === 'news_broadcast') pitchFactor = 1.0;
        else pitchFactor = (gender === 'female' ? 1.19 : 1.0);
      }

      let payload = {
        text: text,
        model_id: mmsModel,
        model: mmsModel,
        speaker_id: speakerId,
        voice_id: this.currentEngine === 'google_cloud_tts' ? googleVoice : (this.currentEngine === 'bhashini_tts' ? bhashiniVoice : piperVoice),
        voice: this.currentEngine === 'google_cloud_tts' ? googleVoice : (this.currentEngine === 'bhashini_tts' ? bhashiniVoice : piperVoice),
        lang: espeakLang,
        variant: espeakVariant,
        f5_api_url: f5ApiUrl,
        tts_api_url: ttsApiUrl,
        parler_api_url: parlerApiUrl,
        prompt: parlerPrompt,
        preset: parlerPreset,
        gender: gender,
        pitch_factor: pitchFactor,
        bhashini_key: bhashiniKey,
        bhashini_url: bhashiniUrl,
        bhashini_mode: bhashiniEndpointMode,
        bhashini_voice: bhashiniVoice,
        google_key: googleKey,
        google_url: googleUrl,
        google_mode: googleEndpointMode,
        google_voice_id: googleVoice,
        speed: speed,
      };
      if (hfToken && f5ApiUrl.includes('ai4bharat/IndicF5')) {
        payload.hf_token = hfToken;
      }

      let targetApiBase = this.apiBaseUrl;
      const mmsEndpointSelect = document.getElementById('tts-mms-endpoint-select');
      const mmsCustomUrlInput = document.getElementById('tts-mms-custom-url');
      if (this.currentEngine === 'mms_tts' && mmsEndpointSelect && mmsEndpointSelect.value === 'custom' && mmsCustomUrlInput && mmsCustomUrlInput.value.trim()) {
        targetApiBase = mmsCustomUrlInput.value.trim().replace(/\/+$/, '');
      }
      const piperEndpointSelect = document.getElementById('tts-piper-endpoint-select');
      const piperCustomUrlInput = document.getElementById('tts-piper-custom-url');
      if (this.currentEngine === 'piper_tts' && piperEndpointSelect && piperEndpointSelect.value === 'custom' && piperCustomUrlInput && piperCustomUrlInput.value.trim()) {
        targetApiBase = piperCustomUrlInput.value.trim().replace(/\/+$/, '');
      }

      let result = null;

      if (this.currentEngine === 'compare') {
        const res = await fetch(`${targetApiBase}/api/compare`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.error || `Server returned ${res.status}`);
        }
        result = await res.json();
        this.renderCompareResults(result, text);
      } else {
        payload.engine = this.currentEngine;
        const res = await fetch(`${targetApiBase}/api/synthesize`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.error || `Server returned ${res.status}`);
        }
        result = await res.json();
        this.renderSingleResult(result, text);
      }

      this.saveHistory(text, this.currentEngine, result);
    } catch (err) {
      console.error('TTS Synthesis Error:', err);
      alert(`Synthesis Error: ${err.message}\n\nPlease ensure 'python3 python/tts/server.py' is running in the background.`);
    } finally {
      if (timerInterval) clearInterval(timerInterval);
      if (synthBtn) synthBtn.disabled = false;
      if (synthSpinner) synthSpinner.style.display = 'none';
      if (synthBtnText) synthBtnText.textContent = '🎙️ ગુજરાતી સ્પીચ જનરેટ કરો (Synthesize Speech)';
    }
  }

  synthesizeWebSpeech(text) {
    if (!('speechSynthesis' in window)) {
      alert('Your browser does not support the Web Speech API (speechSynthesis). Please use Google Chrome, Edge, or Safari.');
      return;
    }

    const synthBtn = document.getElementById('btn-tts-synthesize');
    const synthBtnText = document.getElementById('tts-btn-label');
    const synthSpinner = document.getElementById('tts-spinner');
    
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'gu-IN';

    const voiceSelect = document.getElementById('tts-webspeech-voice-select');
    if (voiceSelect && voiceSelect.value && voiceSelect.value !== 'default') {
      const voices = window.speechSynthesis.getVoices();
      const match = voices.find(v => v.name === voiceSelect.value);
      if (match) utterance.voice = match;
    }

    const pitchSelect = document.getElementById('tts-webspeech-pitch-select');
    utterance.pitch = pitchSelect ? parseFloat(pitchSelect.value) || 1.0 : 1.0;

    const pacingSelect = document.getElementById('tts-pacing-select');
    const speed = pacingSelect ? parseFloat(pacingSelect.value) || 0.85 : 0.85;
    utterance.rate = speed;

    const startTime = performance.now();
    this.renderWebSpeechResult(text, utterance, startTime);

    if (synthBtn) synthBtn.disabled = true;
    if (synthSpinner) synthSpinner.style.display = 'inline-block';
    if (synthBtnText) synthBtnText.textContent = '🔊 સ્પીચ વાગી રહી છે (Playing via Device Voice)...';

    utterance.onend = () => {
      if (synthBtnText) synthBtnText.textContent = '🎙️ ગુજરાતી સ્પીચ જનરેટ કરો (Synthesize Speech)';
      if (synthBtn) synthBtn.disabled = false;
      if (synthSpinner) synthSpinner.style.display = 'none';
      const playBtn = document.getElementById('btn-play-webspeech');
      if (playBtn) playBtn.textContent = '▶';
    };

    utterance.onerror = (e) => {
      console.warn('Web Speech synthesis error/interrupted:', e);
      if (synthBtnText) synthBtnText.textContent = '🎙️ ગુજરાતી સ્પીચ જનરેટ કરો (Synthesize Speech)';
      if (synthBtn) synthBtn.disabled = false;
      if (synthSpinner) synthSpinner.style.display = 'none';
    };

    window.speechSynthesis.speak(utterance);
    this.saveHistory(text, 'web_speech', { text, engine: 'web_speech', voice: (utterance.voice && utterance.voice.name) || 'Native' });
  }

  renderWebSpeechResult(text, utterance, startTime) {
    const resultsContainer = document.getElementById('tts-results-container');
    if (!resultsContainer) return;

    resultsContainer.style.display = 'flex';
    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    const voiceName = (utterance.voice && utterance.voice.name) ? utterance.voice.name : 'Browser Device Native';
    const voiceLang = (utterance.voice && utterance.voice.lang) ? utterance.voice.lang : 'gu-IN';

    resultsContainer.innerHTML = `
      <div class="tts-player-card">
        <div class="tts-player-header">
          <div class="tts-player-meta-info">
            <div class="tts-player-title">
              <span>🌐 Browser Native Web Speech API</span>
              <span class="tts-metric-tag highlight">0ms Client-Side Synthesis</span>
            </div>
            <div class="tts-player-subtext">${this.escapeHtml(text)}</div>
          </div>
          <div class="tts-metrics-bar">
            <span class="tts-metric-tag">🎙️ Voice: ${voiceName}</span>
            <span class="tts-metric-tag">🌍 Lang: ${voiceLang}</span>
            <span class="tts-metric-tag">⚡ Latency: 0.0s (Zero-Server)</span>
            <span class="tts-metric-tag">🎵 Rate: ${utterance.rate}x | Pitch: ${utterance.pitch}x</span>
          </div>
        </div>

        <div class="tts-waveform-container" id="waveform-wrap-single" style="display: flex; align-items: center; justify-content: center; background: rgba(0, 229, 255, 0.03); border: 1px dashed var(--border-accent); border-radius: var(--radius-md); padding: 20px;">
          <div style="font-size: 13px; color: var(--accent-primary); font-weight: 600;">
            ⚡ Direct Hardware Audio Device Output (Zero Cloud Latency)
          </div>
        </div>

        <div class="tts-controls-bar">
          <div class="tts-controls-left">
            <button class="btn-tts-play" id="btn-play-webspeech" title="Replay / Pause">⏹</button>
            <span class="tts-time-display" id="time-display-webspeech">Live Playback</span>
          </div>

          <div class="tts-controls-right">
            <button class="btn-tts-download" id="btn-cancel-webspeech" style="background: rgba(255, 75, 75, 0.15); border-color: rgba(255, 75, 75, 0.4); color: #ff6b6b;">
              ⏹️ Stop Speech
            </button>
          </div>
        </div>
      </div>
    `;

    const playBtn = document.getElementById('btn-play-webspeech');
    if (playBtn) {
      playBtn.addEventListener('click', () => {
        if (window.speechSynthesis.speaking) {
          if (window.speechSynthesis.paused) {
            window.speechSynthesis.resume();
            playBtn.textContent = '⏸';
          } else {
            window.speechSynthesis.pause();
            playBtn.textContent = '▶';
          }
        } else {
          window.speechSynthesis.speak(utterance);
          playBtn.textContent = '⏸';
        }
      });
    }

    const cancelBtn = document.getElementById('btn-cancel-webspeech');
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => {
        window.speechSynthesis.cancel();
        if (playBtn) playBtn.textContent = '▶';
      });
    }
  }

  renderSingleResult(data, text) {
    const resultsContainer = document.getElementById('tts-results-container');
    if (!resultsContainer) return;

    resultsContainer.style.display = 'flex';
    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    const isMMS = data.engine === 'mms_tts';
    const isPiper = data.engine === 'piper_tts';
    const isParler = data.engine === 'parler_tts';
    const isBhashini = data.engine === 'bhashini_tts';
    const isGoogle = data.engine === 'google_cloud_tts';
    const isEspeak = data.engine === 'espeak_ng';
    const isF5 = data.engine === 'indic_f5';

    let engineTitle = 'KanoAI TTS';
    let engineBadge = 'Neural';
    if (isMMS) {
      engineTitle = 'Meta MMS-TTS (Offline VITS)';
      engineBadge = '100% Offline VITS';
    } else if (isPiper) {
      engineTitle = `Piper TTS (${data.voice_name || data.voice_id || 'Rohan'})`;
      engineBadge = data.is_mock ? 'Synthetic Fallback' : 'Ultra-Fast ONNX';
    } else if (isParler) {
      engineTitle = 'Parler-TTS Indic (Prompt-Guided)';
      engineBadge = data.is_fallback ? 'Local Neural Fallback' : 'Audio Codec';
    } else if (isBhashini) {
      engineTitle = `Bhashini Official (${data.voice_id === 'gu_male' ? 'Male' : 'Female'})`;
      engineBadge = data.is_fallback ? 'Local Neural Fallback' : 'Digital India Benchmark';
    } else if (isGoogle) {
      engineTitle = `Google Cloud TTS (${data.voice_id || 'Neural2'})`;
      engineBadge = data.is_fallback ? 'Local Neural Fallback' : 'Cloud Studio Quality';
    } else if (isEspeak) {
      engineTitle = `eSpeak-NG (${data.lang === 'hi' ? 'Hindi' : 'Gujarati'})`;
      engineBadge = 'Formant Synthesis (<10 MB)';
    } else if (isF5) {
      engineTitle = 'AI4Bharat IndicF5';
      engineBadge = 'Flow-Matching';
    } else {
      engineTitle = `AI4Bharat Indic-TTS (${data.speaker || 'Dhara'})`;
      engineBadge = 'Multi-Speaker';
    }

    const sampleRate = data.sample_rate ? `${(data.sample_rate / 1000).toFixed(1)} kHz` : '22.0 kHz';
    const duration = (data.duration || data.duration_seconds) ? `${data.duration || data.duration_seconds}s` : 'Audio';
    const latency = data.elapsed_seconds ? `${data.elapsed_seconds}s` : (data.inference_time_ms ? `${data.inference_time_ms} ms` : '');
    const audioSrc = `data:${data.mime_type || 'audio/wav'};base64,${data.audio_base64}`;

    let debugPhonemesHTML = '';
    if (data.debug && data.debug.ipa) {
      const tokensHTML = (data.debug.tokens || []).map(t => `
        <span class="tts-phoneme-chip" title="${t.name} (${t.type})">
          <strong>${t.char}</strong> → /${t.ipa || '-'}/
        </span>
      `).join('');

      debugPhonemesHTML = `
        <div class="tts-phoneme-debug-card" style="margin-top: 14px; padding: 12px 16px; background: rgba(0, 229, 255, 0.05); border: 1px dashed var(--border-accent); border-radius: var(--radius-md);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-weight: 700; font-size: 13px; color: var(--accent-primary);">🔬 IPA Phonetic Transcription:</span>
            <span style="font-family: monospace; font-size: 13px; color: var(--cyan-stroke); background: rgba(0,0,0,0.25); padding: 2px 8px; border-radius: 4px;">/${data.debug.ipa}/</span>
          </div>
          <div style="display: flex; flex-wrap: wrap; gap: 6px; font-size: 12px;">
            ${tokensHTML}
          </div>
        </div>
      `;
    }

    resultsContainer.innerHTML = `
      <div class="tts-player-card">
        <div class="tts-player-header">
          <div class="tts-player-meta-info">
            <div class="tts-player-title">
              <span>🔊 ${engineTitle}</span>
              <span class="tts-metric-tag highlight">${engineBadge}</span>
            </div>
            <div class="tts-player-subtext">${this.escapeHtml(text)}</div>
          </div>
          <div class="tts-metrics-bar">
            <span class="tts-metric-tag">⏱️ Duration: ${duration}</span>
            ${latency ? `<span class="tts-metric-tag">⚡ Latency: ${latency}</span>` : ''}
            <span class="tts-metric-tag">🎼 ${sampleRate}</span>
            ${data.file_size ? `<span class="tts-metric-tag">📦 ${(data.file_size / 1024).toFixed(1)} KB</span>` : ''}
          </div>
        </div>

        <div class="tts-waveform-container" id="waveform-wrap-single">
          <canvas class="tts-waveform-canvas" id="waveform-canvas-single"></canvas>
          <div class="tts-waveform-played-mask" id="waveform-played-single"></div>
          <div class="tts-waveform-progress-line" id="waveform-progress-single"></div>
        </div>

        <div class="tts-controls-bar">
          <div class="tts-controls-left">
            <button class="btn-tts-play" id="btn-play-single" title="Play / Pause">▶</button>
            <span class="tts-time-display" id="time-display-single">0:00 / 0:00</span>
          </div>

          <div class="tts-controls-right">
            <div class="tts-speed-selector">
              <button class="tts-speed-btn ${this.playbackRate === 0.65 ? 'active' : ''}" data-speed="0.65">0.65x</button>
              <button class="tts-speed-btn ${this.playbackRate === 0.75 ? 'active' : ''}" data-speed="0.75">0.75x</button>
              <button class="tts-speed-btn ${this.playbackRate === 0.85 ? 'active' : ''}" data-speed="0.85">0.85x</button>
              <button class="tts-speed-btn ${this.playbackRate === 1.0 ? 'active' : ''}" data-speed="1.0">1.0x</button>
            </div>
            <a href="${audioSrc}" download="gujarati_${data.engine}_${Date.now()}.wav" class="btn-tts-download" title="Download WAV Audio">
              ⬇️ Download WAV
            </a>
          </div>
        </div>

        ${debugPhonemesHTML}
      </div>
    `;

    this.attachAudioPlayer(audioSrc, 'single');
  }

  renderCompareResults(data, text) {
    const resultsContainer = document.getElementById('tts-results-container');
    if (!resultsContainer) return;

    resultsContainer.style.display = 'flex';
    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    const mmsData = data.mms_tts || (data.results && data.results.mms_tts) || null;
    const piperData = data.piper_tts || (data.results && data.results.piper_tts) || null;
    const parlerData = data.parler_tts || (data.results && data.results.parler_tts) || null;
    const bhashiniData = data.bhashini_tts || (data.results && data.results.bhashini_tts) || null;
    const googleData = data.google_cloud_tts || (data.results && data.results.google_cloud_tts) || null;
    const espeakData = data.espeak_ng || (data.results && data.results.espeak_ng) || null;
    const f5Data = data.indic_f5 || (data.results && data.results.indic_f5) || null;
    const ttsData = data.indic_tts || (data.results && data.results.indic_tts) || null;

    const mmsError = (data.errors && data.errors.mms_tts) || null;
    const piperError = (data.errors && data.errors.piper_tts) || null;
    const parlerError = (data.errors && data.errors.parler_tts) || null;
    const bhashiniError = (data.errors && data.errors.bhashini_tts) || null;
    const googleError = (data.errors && data.errors.google_cloud_tts) || null;
    const espeakError = (data.errors && data.errors.espeak_ng) || null;
    const f5Error = (data.errors && data.errors.indic_f5) || null;
    const ttsError = (data.errors && data.errors.indic_tts) || null;

    const mmsSrc = (mmsData && mmsData.audio_base64) ? `data:audio/wav;base64,${mmsData.audio_base64}` : null;
    const piperSrc = (piperData && piperData.audio_base64) ? `data:audio/wav;base64,${piperData.audio_base64}` : null;
    const parlerSrc = (parlerData && parlerData.audio_base64) ? `data:audio/wav;base64,${parlerData.audio_base64}` : null;
    const bhashiniSrc = (bhashiniData && bhashiniData.audio_base64) ? `data:audio/wav;base64,${bhashiniData.audio_base64}` : null;
    const googleSrc = (googleData && googleData.audio_base64) ? `data:audio/wav;base64,${googleData.audio_base64}` : null;
    const espeakSrc = (espeakData && espeakData.audio_base64) ? `data:audio/wav;base64,${espeakData.audio_base64}` : null;
    const f5Src = (f5Data && f5Data.audio_base64) ? `data:audio/wav;base64,${f5Data.audio_base64}` : null;
    const ttsSrc = (ttsData && ttsData.audio_base64) ? `data:audio/wav;base64,${ttsData.audio_base64}` : null;

    let mmsColHTML = '';
    if (mmsSrc) {
      mmsColHTML = `
        <div class="tts-waveform-container" id="waveform-wrap-mms">
          <canvas class="tts-waveform-canvas" id="waveform-canvas-mms"></canvas>
          <div class="tts-waveform-played-mask" id="waveform-played-mms"></div>
          <div class="tts-waveform-progress-line" id="waveform-progress-mms"></div>
        </div>
        <div class="tts-controls-bar">
          <div class="tts-controls-left">
            <button class="btn-tts-play" id="btn-play-mms" title="Play Meta MMS-TTS">▶</button>
            <span class="tts-time-display" id="time-display-mms">0:00</span>
          </div>
          <div class="tts-controls-right">
            <div class="tts-speed-selector">
              <button class="tts-speed-btn ${this.playbackRate === 0.75 ? 'active' : ''}" data-speed="0.75">0.75x</button>
              <button class="tts-speed-btn ${this.playbackRate === 1.0 ? 'active' : ''}" data-speed="1.0">1.0x</button>
            </div>
            <a href="${mmsSrc}" download="gujarati_mms_tts_${Date.now()}.wav" class="btn-tts-download">⬇️ WAV</a>
          </div>
        </div>
      `;
    } else {
      mmsColHTML = `
        <div style="background: rgba(255, 107, 53, 0.08); border: 1px dashed var(--border-accent); border-radius: var(--radius-md); padding: 16px; font-size: 13px; color: var(--text-secondary); line-height: 1.5;">
          <div style="color: var(--accent-primary); font-weight: 700; margin-bottom: 6px;">⚠️ Meta MMS-TTS Status</div>
          <div>${this.escapeHtml(mmsError || 'Speech synthesis pending or failed.')}</div>
        </div>
      `;
    }

    let piperColHTML = '';
    if (piperSrc) {
      piperColHTML = `
        <div class="tts-waveform-container" id="waveform-wrap-piper">
          <canvas class="tts-waveform-canvas" id="waveform-canvas-piper"></canvas>
          <div class="tts-waveform-played-mask" id="waveform-played-piper"></div>
          <div class="tts-waveform-progress-line" id="waveform-progress-piper"></div>
        </div>
        <div class="tts-controls-bar">
          <div class="tts-controls-left">
            <button class="btn-tts-play" id="btn-play-piper" title="Play Piper TTS">▶</button>
            <span class="tts-time-display" id="time-display-piper">0:00</span>
          </div>
          <div class="tts-controls-right">
            <div class="tts-speed-selector">
              <button class="tts-speed-btn ${this.playbackRate === 0.75 ? 'active' : ''}" data-speed="0.75">0.75x</button>
              <button class="tts-speed-btn ${this.playbackRate === 1.0 ? 'active' : ''}" data-speed="1.0">1.0x</button>
            </div>
            <a href="${piperSrc}" download="gujarati_piper_tts_${Date.now()}.wav" class="btn-tts-download">⬇️ WAV</a>
          </div>
        </div>
      `;
    } else {
      piperColHTML = `
        <div style="background: rgba(255, 107, 53, 0.08); border: 1px dashed var(--border-accent); border-radius: var(--radius-md); padding: 16px; font-size: 13px; color: var(--text-secondary); line-height: 1.5;">
          <div style="color: var(--accent-primary); font-weight: 700; margin-bottom: 6px;">⚠️ Piper TTS Status</div>
          <div>${this.escapeHtml(piperError || 'Speech synthesis pending or failed.')}</div>
        </div>
      `;
    }

    let espeakColHTML = '';
    if (espeakSrc) {
      espeakColHTML = `
        <div class="tts-waveform-container" id="waveform-wrap-espeak">
          <canvas class="tts-waveform-canvas" id="waveform-canvas-espeak"></canvas>
          <div class="tts-waveform-played-mask" id="waveform-played-espeak"></div>
          <div class="tts-waveform-progress-line" id="waveform-progress-espeak"></div>
        </div>
        <div class="tts-controls-bar">
          <div class="tts-controls-left">
            <button class="btn-tts-play" id="btn-play-espeak" title="Play eSpeak-NG">▶</button>
            <span class="tts-time-display" id="time-display-espeak">0:00</span>
          </div>
          <div class="tts-controls-right">
            <div class="tts-speed-selector">
              <button class="tts-speed-btn ${this.playbackRate === 0.75 ? 'active' : ''}" data-speed="0.75">0.75x</button>
              <button class="tts-speed-btn ${this.playbackRate === 1.0 ? 'active' : ''}" data-speed="1.0">1.0x</button>
            </div>
            <a href="${espeakSrc}" download="gujarati_espeak_ng_${Date.now()}.wav" class="btn-tts-download">⬇️ WAV</a>
          </div>
        </div>
      `;
    } else {
      espeakColHTML = `
        <div style="background: rgba(255, 107, 53, 0.08); border: 1px dashed var(--border-accent); border-radius: var(--radius-md); padding: 16px; font-size: 13px; color: var(--text-secondary); line-height: 1.5;">
          <div style="color: var(--accent-primary); font-weight: 700; margin-bottom: 6px;">⚠️ eSpeak-NG Status</div>
          <div>${this.escapeHtml(espeakError || 'Speech synthesis pending or failed.')}</div>
        </div>
      `;
    }

    let f5ColHTML = '';
    if (f5Src) {
      f5ColHTML = `
        <div class="tts-waveform-container" id="waveform-wrap-f5">
          <canvas class="tts-waveform-canvas" id="waveform-canvas-f5"></canvas>
          <div class="tts-waveform-played-mask" id="waveform-played-f5"></div>
          <div class="tts-waveform-progress-line" id="waveform-progress-f5"></div>
        </div>
        <div class="tts-controls-bar">
          <div class="tts-controls-left">
            <button class="btn-tts-play" id="btn-play-f5" title="Play IndicF5">▶</button>
            <span class="tts-time-display" id="time-display-f5">0:00</span>
          </div>
          <div class="tts-controls-right">
            <div class="tts-speed-selector">
              <button class="tts-speed-btn ${this.playbackRate === 0.75 ? 'active' : ''}" data-speed="0.75">0.75x</button>
              <button class="tts-speed-btn ${this.playbackRate === 1.0 ? 'active' : ''}" data-speed="1.0">1.0x</button>
            </div>
            <a href="${f5Src}" download="gujarati_indic_f5_${Date.now()}.wav" class="btn-tts-download">⬇️ WAV</a>
          </div>
        </div>
      `;
    } else {
      const isZeroGPU = f5Error && (f5Error.includes('ZeroGPU') || f5Error.includes('quota'));
      f5ColHTML = `
        <div style="background: rgba(255, 107, 53, 0.08); border: 1px dashed var(--border-accent); border-radius: var(--radius-md); padding: 16px; font-size: 13px; color: var(--text-secondary); line-height: 1.5;">
          <div style="color: var(--accent-primary); font-weight: 700; margin-bottom: 6px;">⚠️ IndicF5 Status</div>
          <div>${this.escapeHtml(f5Error || 'Speech synthesis pending or failed.')}</div>
          ${isZeroGPU ? `<div style="margin-top: 10px; font-size: 11px; color: var(--text-muted);">👉 Add a free Hugging Face token in the settings above to unlock personal GPU quota.</div>` : ''}
        </div>
      `;
    }

    let ttsColHTML = '';
    if (ttsSrc) {
      ttsColHTML = `
        <div class="tts-waveform-container" id="waveform-wrap-tts">
          <canvas class="tts-waveform-canvas" id="waveform-canvas-tts"></canvas>
          <div class="tts-waveform-played-mask" id="waveform-played-tts"></div>
          <div class="tts-waveform-progress-line" id="waveform-progress-tts"></div>
        </div>
        <div class="tts-controls-bar">
          <div class="tts-controls-left">
            <button class="btn-tts-play" id="btn-play-tts" title="Play Indic-TTS">▶</button>
            <span class="tts-time-display" id="time-display-tts">0:00</span>
          </div>
          <div class="tts-controls-right">
            <div class="tts-speed-selector">
              <button class="tts-speed-btn ${this.playbackRate === 0.75 ? 'active' : ''}" data-speed="0.75">0.75x</button>
              <button class="tts-speed-btn ${this.playbackRate === 1.0 ? 'active' : ''}" data-speed="1.0">1.0x</button>
            </div>
            <a href="${ttsSrc}" download="gujarati_indic_tts_${Date.now()}.wav" class="btn-tts-download">⬇️ WAV</a>
          </div>
        </div>
      `;
    } else {
      ttsColHTML = `
        <div style="background: rgba(255, 107, 53, 0.08); border: 1px dashed var(--border-accent); border-radius: var(--radius-md); padding: 16px; font-size: 13px; color: var(--text-secondary); line-height: 1.5;">
          <div style="color: var(--accent-primary); font-weight: 700; margin-bottom: 6px;">⚠️ Indic-TTS Status</div>
          <div>${this.escapeHtml(ttsError || 'Speech synthesis pending or failed.')}</div>
        </div>
      `;
    }

    let parlerColHTML = '';
    if (parlerSrc) {
      parlerColHTML = `
        <div class="tts-waveform-container" id="waveform-wrap-parler">
          <canvas class="tts-waveform-canvas" id="waveform-canvas-parler"></canvas>
          <div class="tts-waveform-played-mask" id="waveform-played-parler"></div>
          <div class="tts-waveform-progress-line" id="waveform-progress-parler"></div>
        </div>
        <div class="tts-controls-bar">
          <div class="tts-controls-left">
            <button class="btn-tts-play" id="btn-play-parler" title="Play Parler-TTS">▶</button>
            <span class="tts-time-display" id="time-display-parler">0:00</span>
          </div>
          <div class="tts-controls-right">
            <div class="tts-speed-selector">
              <button class="tts-speed-btn ${this.playbackRate === 0.75 ? 'active' : ''}" data-speed="0.75">0.75x</button>
              <button class="tts-speed-btn ${this.playbackRate === 1.0 ? 'active' : ''}" data-speed="1.0">1.0x</button>
            </div>
            <a href="${parlerSrc}" download="gujarati_parler_${Date.now()}.wav" class="btn-tts-download">⬇️ WAV</a>
          </div>
        </div>
      `;
    } else {
      parlerColHTML = `
        <div style="background: rgba(255, 107, 53, 0.08); border: 1px dashed var(--border-accent); border-radius: var(--radius-md); padding: 16px; font-size: 13px; color: var(--text-secondary); line-height: 1.5;">
          <div style="color: var(--accent-primary); font-weight: 700; margin-bottom: 6px;">⚠️ Parler-TTS Status</div>
          <div>${this.escapeHtml(parlerError || 'Speech synthesis pending or failed.')}</div>
        </div>
      `;
    }

    let bhashiniColHTML = '';
    if (bhashiniSrc) {
      bhashiniColHTML = `
        <div class="tts-waveform-container" id="waveform-wrap-bhashini">
          <canvas class="tts-waveform-canvas" id="waveform-canvas-bhashini"></canvas>
          <div class="tts-waveform-played-mask" id="waveform-played-bhashini"></div>
          <div class="tts-waveform-progress-line" id="waveform-progress-bhashini"></div>
        </div>
        <div class="tts-controls-bar">
          <div class="tts-controls-left">
            <button class="btn-tts-play" id="btn-play-bhashini" title="Play Bhashini">▶</button>
            <span class="tts-time-display" id="time-display-bhashini">0:00</span>
          </div>
          <div class="tts-controls-right">
            <div class="tts-speed-selector">
              <button class="tts-speed-btn ${this.playbackRate === 0.75 ? 'active' : ''}" data-speed="0.75">0.75x</button>
              <button class="tts-speed-btn ${this.playbackRate === 1.0 ? 'active' : ''}" data-speed="1.0">1.0x</button>
            </div>
            <a href="${bhashiniSrc}" download="gujarati_bhashini_${Date.now()}.wav" class="btn-tts-download">⬇️ WAV</a>
          </div>
        </div>
      `;
    } else {
      bhashiniColHTML = `
        <div style="background: rgba(255, 107, 53, 0.08); border: 1px dashed var(--border-accent); border-radius: var(--radius-md); padding: 16px; font-size: 13px; color: var(--text-secondary); line-height: 1.5;">
          <div style="color: var(--accent-primary); font-weight: 700; margin-bottom: 6px;">⚠️ Bhashini Status</div>
          <div>${this.escapeHtml(bhashiniError || 'Speech synthesis pending or failed.')}</div>
        </div>
      `;
    }

    let googleColHTML = '';
    if (googleSrc) {
      googleColHTML = `
        <div class="tts-waveform-container" id="waveform-wrap-google">
          <canvas class="tts-waveform-canvas" id="waveform-canvas-google"></canvas>
          <div class="tts-waveform-played-mask" id="waveform-played-google"></div>
          <div class="tts-waveform-progress-line" id="waveform-progress-google"></div>
        </div>
        <div class="tts-controls-bar">
          <div class="tts-controls-left">
            <button class="btn-tts-play" id="btn-play-google" title="Play Google Cloud">▶</button>
            <span class="tts-time-display" id="time-display-google">0:00</span>
          </div>
          <div class="tts-controls-right">
            <div class="tts-speed-selector">
              <button class="tts-speed-btn ${this.playbackRate === 0.75 ? 'active' : ''}" data-speed="0.75">0.75x</button>
              <button class="tts-speed-btn ${this.playbackRate === 1.0 ? 'active' : ''}" data-speed="1.0">1.0x</button>
            </div>
            <a href="${googleSrc}" download="gujarati_google_${Date.now()}.wav" class="btn-tts-download">⬇️ WAV</a>
          </div>
        </div>
      `;
    } else {
      googleColHTML = `
        <div style="background: rgba(255, 107, 53, 0.08); border: 1px dashed var(--border-accent); border-radius: var(--radius-md); padding: 16px; font-size: 13px; color: var(--text-secondary); line-height: 1.5;">
          <div style="color: var(--accent-primary); font-weight: 700; margin-bottom: 6px;">⚠️ Google Cloud TTS Status</div>
          <div>${this.escapeHtml(googleError || 'Speech synthesis pending or failed.')}</div>
        </div>
      `;
    }

    resultsContainer.innerHTML = `
      <div class="tts-player-card">
        <div class="tts-player-header">
          <div class="tts-player-meta-info">
            <div class="tts-player-title">
              <span>⚖️ Side-by-Side Multi-Engine Comparison</span>
              <span class="tts-metric-tag highlight">Multi-Engine Benchmarking</span>
            </div>
            <div class="tts-player-subtext">${this.escapeHtml(text)}</div>
          </div>
        </div>

        <div class="tts-comparison-grid">
          <!-- Col 1: Meta MMS-TTS -->
          <div class="tts-comparison-col">
            <div class="tts-comp-header">
              <span class="tts-comp-model-title">1️⃣ Meta MMS-TTS (Offline)</span>
              <div class="tts-metrics-bar">
                <span class="tts-metric-tag">⚡ ${mmsData && mmsData.elapsed_seconds ? mmsData.elapsed_seconds + 's' : '-'}</span>
                <span class="tts-metric-tag">🎼 16 kHz</span>
              </div>
            </div>
            ${mmsColHTML}
          </div>

          <!-- Col 2: Piper TTS -->
          <div class="tts-comparison-col">
            <div class="tts-comp-header">
              <span class="tts-comp-model-title">2️⃣ Piper TTS (${(piperData && piperData.voice_name) || 'Rohan'})</span>
              <div class="tts-metrics-bar">
                <span class="tts-metric-tag">⚡ ${piperData && piperData.inference_time_ms ? piperData.inference_time_ms + ' ms' : '-'}</span>
                <span class="tts-metric-tag">🎼 22 kHz</span>
              </div>
            </div>
            ${piperColHTML}
          </div>

          <!-- Col 3: Parler-TTS Indic -->
          <div class="tts-comparison-col">
            <div class="tts-comp-header">
              <span class="tts-comp-model-title">3️⃣ Parler-TTS Indic</span>
              <div class="tts-metrics-bar">
                <span class="tts-metric-tag">⚡ ${parlerData && parlerData.elapsed_seconds ? parlerData.elapsed_seconds + 's' : '-'}</span>
                <span class="tts-metric-tag">🎼 44.1 kHz</span>
              </div>
            </div>
            ${parlerColHTML}
          </div>

          <!-- Col 4: Bhashini Official -->
          <div class="tts-comparison-col">
            <div class="tts-comp-header">
              <span class="tts-comp-model-title">4️⃣ Bhashini Neural TTS</span>
              <div class="tts-metrics-bar">
                <span class="tts-metric-tag">⚡ ${bhashiniData && bhashiniData.elapsed_seconds ? bhashiniData.elapsed_seconds + 's' : '-'}</span>
                <span class="tts-metric-tag">🎼 22 kHz</span>
              </div>
            </div>
            ${bhashiniColHTML}
          </div>

          <!-- Col 5: Google Cloud TTS -->
          <div class="tts-comparison-col">
            <div class="tts-comp-header">
              <span class="tts-comp-model-title">5️⃣ Google Cloud (gu-IN)</span>
              <div class="tts-metrics-bar">
                <span class="tts-metric-tag">⚡ ${googleData && googleData.elapsed_seconds ? googleData.elapsed_seconds + 's' : '-'}</span>
                <span class="tts-metric-tag">🎼 24 kHz</span>
              </div>
            </div>
            ${googleColHTML}
          </div>

          <!-- Col 6: Indic-TTS -->
          <div class="tts-comparison-col">
            <div class="tts-comp-header">
              <span class="tts-comp-model-title">6️⃣ Indic-TTS (${(ttsData && ttsData.speaker) || 'Dhara'})</span>
              <div class="tts-metrics-bar">
                <span class="tts-metric-tag">⚡ ${ttsData && ttsData.elapsed_seconds ? ttsData.elapsed_seconds + 's' : '-'}</span>
                <span class="tts-metric-tag">🎼 44.1 kHz</span>
              </div>
            </div>
            ${ttsColHTML}
          </div>

          <!-- Col 7: IndicF5 -->
          <div class="tts-comparison-col">
            <div class="tts-comp-header">
              <span class="tts-comp-model-title">7️⃣ AI4Bharat IndicF5</span>
              <div class="tts-metrics-bar">
                <span class="tts-metric-tag">⚡ ${f5Data && f5Data.elapsed_seconds ? f5Data.elapsed_seconds + 's' : '-'}</span>
                <span class="tts-metric-tag">🎼 24 kHz</span>
              </div>
            </div>
            ${f5ColHTML}
          </div>

          <!-- Col 8: eSpeak-NG -->
          <div class="tts-comparison-col">
            <div class="tts-comp-header">
              <span class="tts-comp-model-title">8️⃣ eSpeak-NG (IPA Formants)</span>
              <div class="tts-metrics-bar">
                <span class="tts-metric-tag">⚡ ${espeakData && espeakData.inference_time_ms ? espeakData.inference_time_ms + ' ms' : '-'}</span>
                <span class="tts-metric-tag">🔬 IPA</span>
              </div>
            </div>
            ${espeakColHTML}
          </div>
        </div>
      </div>
    `;

    if (mmsSrc) this.attachAudioPlayer(mmsSrc, 'mms');
    if (piperSrc) this.attachAudioPlayer(piperSrc, 'piper');
    if (parlerSrc) this.attachAudioPlayer(parlerSrc, 'parler');
    if (bhashiniSrc) this.attachAudioPlayer(bhashiniSrc, 'bhashini');
    if (googleSrc) this.attachAudioPlayer(googleSrc, 'google');
    if (espeakSrc) this.attachAudioPlayer(espeakSrc, 'espeak');
    if (f5Src) this.attachAudioPlayer(f5Src, 'f5');
    if (ttsSrc) this.attachAudioPlayer(ttsSrc, 'tts');
  }

  attachAudioPlayer(audioSrc, prefix) {
    const audio = new Audio(audioSrc);
    const playBtn = document.getElementById(`btn-play-${prefix}`);
    const timeDisplay = document.getElementById(`time-display-${prefix}`);
    const progressLine = document.getElementById(`waveform-progress-${prefix}`);
    const playedMask = document.getElementById(`waveform-played-${prefix}`);
    const waveformWrap = document.getElementById(`waveform-wrap-${prefix}`);
    const canvas = document.getElementById(`waveform-canvas-${prefix}`);

    let animFrameId = null;

    const updateProgress = () => {
      if (audio.duration && !isNaN(audio.duration)) {
        const ratio = Math.min(1, Math.max(0, audio.currentTime / audio.duration));
        const percent = ratio * 100;
        if (progressLine) progressLine.style.left = `${percent}%`;
        if (playedMask) playedMask.style.width = `${percent}%`;
        if (timeDisplay) {
          timeDisplay.textContent = `${this.formatTime(audio.currentTime)} / ${this.formatTime(audio.duration)}`;
        }
      }
    };

    const startAnimation = () => {
      cancelAnimationFrame(animFrameId);
      const tick = () => {
        updateProgress();
        if (!audio.paused && !audio.ended) {
          animFrameId = requestAnimationFrame(tick);
        }
      };
      animFrameId = requestAnimationFrame(tick);
    };

    const stopAnimation = () => {
      cancelAnimationFrame(animFrameId);
      updateProgress();
    };

    // Decode audio for waveform visualization
    this.drawWaveform(audioSrc, canvas);

    audio.addEventListener('loadedmetadata', () => {
      if (timeDisplay) timeDisplay.textContent = `0:00 / ${this.formatTime(audio.duration)}`;
    });

    audio.addEventListener('ended', () => {
      stopAnimation();
      if (playBtn) playBtn.textContent = '▶';
      if (progressLine) progressLine.style.left = '0%';
      if (playedMask) playedMask.style.width = '0%';
      if (timeDisplay && audio.duration) {
        timeDisplay.textContent = `0:00 / ${this.formatTime(audio.duration)}`;
      }
    });

    audio.addEventListener('pause', () => {
      stopAnimation();
      if (playBtn) playBtn.textContent = '▶';
    });

    audio.addEventListener('play', () => {
      if (playBtn) playBtn.textContent = '⏸';
      startAnimation();
    });

    if (playBtn) {
      playBtn.addEventListener('click', () => {
        if (audio.paused) {
          // Pause currently playing if any
          if (this.activeAudio && this.activeAudio !== audio) {
            this.activeAudio.pause();
          }
          audio.playbackRate = this.playbackRate;
          audio.play().catch(e => console.warn('Play interrupted:', e));
          this.activeAudio = audio;
        } else {
          audio.pause();
        }
      });
    }

    if (waveformWrap) {
      let isSeeking = false;
      const seekFromEvent = (e) => {
        const rect = waveformWrap.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const ratio = Math.max(0, Math.min(1, clickX / rect.width));
        if (audio.duration && !isNaN(audio.duration)) {
          audio.currentTime = ratio * audio.duration;
          updateProgress();
        }
      };

      waveformWrap.addEventListener('mousedown', (e) => {
        isSeeking = true;
        seekFromEvent(e);
      });

      window.addEventListener('mousemove', (e) => {
        if (isSeeking) {
          seekFromEvent(e);
        }
      });

      window.addEventListener('mouseup', () => {
        if (isSeeking) {
          isSeeking = false;
        }
      });

      waveformWrap.addEventListener('click', (e) => {
        seekFromEvent(e);
        if (audio.paused) {
          if (this.activeAudio && this.activeAudio !== audio) {
            this.activeAudio.pause();
          }
          audio.playbackRate = this.playbackRate;
          audio.play().catch(e => console.warn('Play interrupted:', e));
          this.activeAudio = audio;
        }
      });
    }

    // Speed buttons scoped to this player
    const playerContext = playBtn ? playBtn.closest('.tts-player-card, .tts-comparison-col') : null;
    if (playerContext) {
      playerContext.querySelectorAll('.tts-speed-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
          playerContext.querySelectorAll('.tts-speed-btn').forEach(b => b.classList.remove('active'));
          e.target.classList.add('active');
          const rate = parseFloat(e.target.getAttribute('data-speed'));
          this.playbackRate = rate;
          if (audio) audio.playbackRate = rate;
        });
      });
    }
  }

  async drawWaveform(audioSrc, canvas) {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    try {
      const response = await fetch(audioSrc);
      const arrayBuffer = await response.arrayBuffer();
      
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      const actx = new AudioCtx();
      const audioBuffer = await actx.decodeAudioData(arrayBuffer);

      const dpr = window.devicePixelRatio || 1;
      const width = canvas.parentElement.clientWidth || 600;
      const height = canvas.parentElement.clientHeight || 80;

      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.scale(dpr, dpr);

      const rawData = audioBuffer.getChannelData(0);
      const samples = 100; // Number of bars
      const blockSize = Math.floor(rawData.length / samples);
      const filteredData = [];

      for (let i = 0; i < samples; i++) {
        let blockStart = blockSize * i;
        let sum = 0;
        for (let j = 0; j < blockSize; j++) {
          sum += Math.abs(rawData[blockStart + j]);
        }
        filteredData.push(sum / blockSize);
      }

      const multiplier = Math.pow(Math.max(...filteredData), -1);
      ctx.clearRect(0, 0, width, height);

      const barWidth = width / samples;
      for (let i = 0; i < samples; i++) {
        const barHeight = Math.max(4, filteredData[i] * multiplier * (height * 0.75));
        const x = i * barWidth;
        const y = (height - barHeight) / 2;

        const grad = ctx.createLinearGradient(0, y, 0, y + barHeight);
        grad.addColorStop(0, '#ff6b35');
        grad.addColorStop(1, '#00f2fe');

        ctx.fillStyle = grad;
        ctx.fillRect(x + 1, y, Math.max(1, barWidth - 2), barHeight);
      }
    } catch (e) {
      console.warn('Waveform draw fallback:', e);
    }
  }

  formatTime(secs) {
    if (isNaN(secs) || secs < 0) return '0:00';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  }

  escapeHtml(str) {
    const div = document.createElement('div');
    div.innerText = str;
    return div.innerHTML;
  }

  saveHistory(text, engine, data) {
    this.history.unshift({
      text: text,
      engine: engine,
      timestamp: Date.now(),
      data: data
    });
    if (this.history.length > 5) this.history.pop();
    this.renderHistory();
  }

  loadHistory() {
    this.renderHistory();
  }

  renderHistory() {
    const strip = document.getElementById('tts-history-items');
    const container = document.getElementById('tts-history-container');
    if (!strip || !container) return;

    if (this.history.length === 0) {
      container.style.display = 'none';
      return;
    }

    container.style.display = 'flex';
    strip.innerHTML = '';
    this.history.forEach((h, idx) => {
      const item = document.createElement('div');
      item.className = 'tts-history-item';
      item.title = `Click to re-listen: ${h.text}`;
      item.innerHTML = `
        <span>🔊</span>
        <span class="tts-history-text">${this.escapeHtml(h.text)}</span>
      `;
      item.addEventListener('click', () => {
        if (h.engine === 'compare') {
          this.renderCompareResults(h.data, h.text);
        } else {
          this.renderSingleResult(h.data, h.text);
        }
      });
      strip.appendChild(item);
    });
  }
}

window.ttsStudio = new TTSStudio();
