const path = require("path");
const fs = require("fs");
const fetch = require("node-fetch");
const TextToSVG = require("text-to-svg");
const { createHarfBuzzShaper } = require("./harfbuzzSvg");
const {
  generateJodaksharInterpolateSvg: runJodaksharInterpolate,
  syncJodaksharFromKano: runSyncJodaksharFromKano,
} = require("./jodaksharInterpolate");

// Resolve directories relative to repository root
const ROOT_DIR = path.resolve(__dirname, "..");
const RESOURCES_DIR = path.resolve(ROOT_DIR, "resources");
const FONTS_DIR = path.resolve(ROOT_DIR, "fonts");

const barakhdi = require(path.join(RESOURCES_DIR, "barakhdi/barakhdi.json"));
const kakko = require(path.join(RESOURCES_DIR, "kakko/kakko.json"));
const numerals = require(path.join(RESOURCES_DIR, "numerals/numerals.json"));

// Kano React Native app paths & Jodakshar dataset
const KANO_APP_DIR = path.resolve(ROOT_DIR, "../Kano");
const KANO_JODAKSHAR_JSON = path.join(KANO_APP_DIR, "app/assets/lang/sections/jodakshar.json");
const KANO_JODAKSHAR_SVGS = path.join(KANO_APP_DIR, "assets/svgs/jodakshar");

const jodaksharJsonPath = fs.existsSync(path.join(RESOURCES_DIR, "jodakshar/jodakshar.json"))
  ? path.join(RESOURCES_DIR, "jodakshar/jodakshar.json")
  : KANO_JODAKSHAR_JSON;

const jodaksharRaw = fs.existsSync(jodaksharJsonPath)
  ? require(jodaksharJsonPath)
  : { items: [] };
const jodakshar = Array.isArray(jodaksharRaw) ? jodaksharRaw : jodaksharRaw.items || [];

const fontPath = path.join(FONTS_DIR, "Noto_Sans_Gujarati/NotoSansGujarati-Light.ttf");
const textToSVG = TextToSVG.loadSync(fontPath);
const shaper = createHarfBuzzShaper(fontPath, textToSVG.font);

const options = {
  x: 0,
  y: 0,
  fontSize: 100,
  anchor: "left top",
  attributes: {},
};

const toSlugName = (text) =>
  (text || "").replace(" / ", "_or_").replace(/[\s\/]+/g, "_").toLowerCase();

const ensureDir = (dir) => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  return dir;
};

const generateBarakhadiSvg = () => {
  for (let i = 0; i < barakhdi.length; i++) {
    const charConfig = barakhdi[i];
    const dir = ensureDir(
      path.join(RESOURCES_DIR, `barakhdi/svgs/${i}_${charConfig.en.toLocaleLowerCase()}`)
    );
    for (const char of charConfig.chars) {
      const svg = textToSVG.getSVG(char.gu, options);
      fs.writeFileSync(path.join(dir, `${char.id}_${toSlugName(char.en)}.svg`), svg);
    }
  }
};

const generateKakkoSvg = () => {
  const dir = ensureDir(path.join(RESOURCES_DIR, "kakko/svgs"));
  for (const char of kakko) {
    const svg = textToSVG.getSVG(char.gu, options);
    fs.writeFileSync(path.join(dir, `${char.id}_${toSlugName(char.en)}.svg`), svg);
  }
};

const generateNumeralsSvg = () => {
  const dir = ensureDir(path.join(RESOURCES_DIR, "numerals/svgs"));
  for (const char of numerals) {
    fs.writeFileSync(path.join(dir, `${char.en}.svg`), textToSVG.getSVG(char.gu, options));
  }
};

const generateJodaksharSvg = async () => {
  const dir = ensureDir(path.join(RESOURCES_DIR, "jodakshar/svgs"));
  for (const item of jodakshar) {
    const svg = await shaper.getShapedSVG(item.cluster || item.gu, options);
    const fileName = `${item.id}_${toSlugName(item.romanization || item.en)}.svg`;
    fs.writeFileSync(path.join(dir, fileName), svg);
  }
};

const generateJodaksharInterpolateSvg = () =>
  runJodaksharInterpolate({
    rootDir: ROOT_DIR,
    resourcesDir: RESOURCES_DIR,
    jodakshar,
    barakhdi,
    shaper,
    fontSize: options.fontSize,
  });

const syncJodaksharFromKano = () => runSyncJodaksharFromKano(ROOT_DIR, KANO_JODAKSHAR_SVGS);

const generateBarakhdiCsv = () => {
  let csvString = "1,2,3,4,5,6,7,8,9,10,11,12,13\n";
  for (let i = 0; i < barakhdi.length; i++) {
    const enArray = barakhdi[i].chars.map((c) => c.en);
    const guArray = barakhdi[i].chars.map((c) => c.gu);
    csvString += `${i},${guArray.join(",")}\n${i},${enArray.join(",")}\n`;
  }
  fs.writeFileSync(path.join(RESOURCES_DIR, "barakhdi/barakhdi.csv"), csvString);
};

const generateKakkoCsv = () => {
  let csvString = "1,2,3\n";
  for (let i = 0; i < kakko.length; i++) {
    csvString += `${i},${kakko[i].gu},${kakko[i].en}\n`;
  }
  fs.writeFileSync(path.join(RESOURCES_DIR, "kakko/kakko.csv"), csvString);
};

const generateNumeralsCsv = () => {
  let csvString = "id,English,Gujarati,English Name,Gujarati Name\n";
  for (let i = 0; i < numerals.length; i++) {
    const char = numerals[i];
    csvString += `${i},${char.en},${char.gu},${char.name_en},${char.name_gu}\n`;
  }
  fs.writeFileSync(path.join(RESOURCES_DIR, "numerals/numerals.csv"), csvString);
};

const generateJodaksharCsv = () => {
  let csvString =
    "id,Cluster,Romanization,Components,Pattern,Level,Example Word,Example Sentence\n";
  for (const item of jodakshar) {
    const components = Array.isArray(item.components) ? item.components.join("+") : "";
    const firstEx = item.examples && item.examples[0];
    const exampleWord = firstEx ? firstEx.word : "";
    const exampleSentence =
      firstEx && firstEx.sentence_gu ? `"${firstEx.sentence_gu.replace(/"/g, '""')}"` : "";
    csvString += `${item.id},${item.cluster},${item.romanization},${components},${item.pattern || ""},${item.level || ""},${exampleWord},${exampleSentence}\n`;
  }
  const dir = ensureDir(path.join(RESOURCES_DIR, "jodakshar"));
  fs.writeFileSync(path.join(dir, "jodakshar.csv"), csvString);
};

const getAudioBase64 = async (char) => {
  const response = await fetch(
    "https://cxl-services.appspot.com/proxy?url=https://texttospeech.googleapis.com/v1beta1/text:synthesize&token=03AAYGu2Td5wXEpHc9QM67XZx756oCCcQmqvl0hHlz8Vf5n0D--kfAcaNh8_V_V3Jhu7vDbBRHnRLV3glVlenrGtHgMG9EEf3qpdLxorQqEK0g0YaWd5C9gGHqVWcX7yltoix4nMJFTkElcYYzuwHcI0EQzMZdzoPQdrUJvTMkkaspsw0kRvG6E0VYdMri5WquFDauwzIgJJDhAs4gJDX5mIEZAxgC3i78dGTbs3V4-szx291a_syzO2AsSE-NL0i6DlRzVxV2frXujgrLQQGBZ_LQf6UO4SLACka2_d6jrPB2-91kair_LH6CBoHmknYpvhU2WLnWoJYxCDtWYvUBij12MOXsw4tDIbD1Dofb8y1FGorpG73nHA7PFz2XgkMPQuLdpai5RwvtH2DrphkcJSR3t8i7f3zjl8u_vUhZfj2gC_Ymdz7_28s5OAcDdtx-lu7LNoDzKjnQ0Q-vMQAcNGd6i98PQeg5NCxuK7Q2XhgqEiGc05CLKkr7ZzE9GPKg5WvMnVbHGf69lZ7oJkB3eFmbc7hJe58LkC1y8sT2nzVL3iEiyZMe2_o",
    {
      headers: {
        accept: "*/*",
        "accept-language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,gu;q=0.6",
        "content-type": "text/plain;charset=UTF-8",
        "sec-ch-ua": '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        Referer: "https://www.gstatic.com/",
        "Referrer-Policy": "strict-origin-when-cross-origin",
      },
      body: `{"input":{"text":"${char}"},"voice":{"languageCode":"gu-IN","name":"gu-IN-Wavenet-A"},"audioConfig":{"audioEncoding":"LINEAR16","pitch":0,"speakingRate":0.55}}`,
      method: "POST",
    }
  );
  const jsonData = await response.json();
  return jsonData.audioContent;
};

const writeTtsMp3 = async (text, destPath, delayMs = 0) => {
  const audioBase64 = await getAudioBase64(text);
  fs.writeFileSync(destPath, Buffer.from(audioBase64, "base64"));
  if (delayMs > 0) {
    await new Promise((r) => setTimeout(r, delayMs));
  }
};

const generateNumeralsAudio = async (section = 0) => {
  const dir = ensureDir(path.join(RESOURCES_DIR, "numerals/audio"));
  for (let i = section; i < numerals.length; i++) {
    await writeTtsMp3(numerals[i].gu, path.join(dir, `${numerals[i].en}.mp3`));
  }
};

const generateBarakhadiAudio = async (section = 0, row = 0) => {
  for (let i = section; i < barakhdi.length; i++) {
    const charConfig = barakhdi[i];
    const dir = ensureDir(
      path.join(RESOURCES_DIR, `barakhdi/audio/${i}_${charConfig.en.toLocaleLowerCase()}`)
    );
    const startRow = i === section ? row : 0;
    for (let j = startRow; j < charConfig.chars.length; j++) {
      const char = charConfig.chars[j];
      await writeTtsMp3(char.gu, path.join(dir, `${char.id}_${toSlugName(char.en)}.mp3`), 2000);
    }
  }
};

const generateKakkoAudio = async (section = 0) => {
  const dir = ensureDir(path.join(RESOURCES_DIR, "kakko/audio"));
  for (let i = section; i < kakko.length; i++) {
    const char = kakko[i];
    await writeTtsMp3(char.gu, path.join(dir, `${char.id}_${toSlugName(char.en)}.mp3`));
  }
};

const generateJodaksharAudio = async (section = 0) => {
  const dir = ensureDir(path.join(RESOURCES_DIR, "jodakshar/audio"));
  for (let i = section; i < jodakshar.length; i++) {
    const item = jodakshar[i];
    const fileName = `${item.id}_${toSlugName(item.romanization)}.mp3`;
    await writeTtsMp3(item.cluster || item.gu, path.join(dir, fileName), 1000);
  }
};

const generateAudio = async () => {
  await generateBarakhadiAudio(0, 0);
  await generateNumeralsAudio(0);
  await generateKakkoAudio(0);
  await generateJodaksharAudio(0);
};

const generateResources = async () => {
  generateBarakhadiSvg();
  generateBarakhdiCsv();
  generateNumeralsSvg();

  generateKakkoSvg();
  generateKakkoCsv();
  generateNumeralsCsv();

  await generateJodaksharSvg();
  await generateJodaksharInterpolateSvg();
  generateJodaksharCsv();
  syncJodaksharFromKano();
};

if (require.main === module) {
  generateResources().catch((err) => {
    console.error("Failed to generate resources:", err);
    process.exitCode = 1;
  });
}

module.exports = {
  generateBarakhadiSvg,
  generateKakkoSvg,
  generateNumeralsSvg,
  generateJodaksharSvg,
  generateJodaksharInterpolateSvg,
  generateBarakhdiCsv,
  generateKakkoCsv,
  generateNumeralsCsv,
  generateJodaksharCsv,
  syncJodaksharFromKano,
  generateBarakhadiAudio,
  generateNumeralsAudio,
  generateKakkoAudio,
  generateJodaksharAudio,
  generateResources,
  generateAudio,
};
