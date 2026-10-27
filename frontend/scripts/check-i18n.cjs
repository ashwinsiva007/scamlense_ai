const fs = require("fs");
const path = require("path");

const enPath = path.join(__dirname, "..", "src", "i18n", "en.json");
const taPath = path.join(__dirname, "..", "src", "i18n", "ta.json");
const hiPath = path.join(__dirname, "..", "src", "i18n", "hi.json");

const en = JSON.parse(fs.readFileSync(enPath, "utf8"));
const ta = JSON.parse(fs.readFileSync(taPath, "utf8"));
const hi = JSON.parse(fs.readFileSync(hiPath, "utf8"));

function getLeafKeys(obj, prefix = "") {
  let keys = [];
  for (const k of Object.keys(obj)) {
    const full = prefix ? `${prefix}.${k}` : k;
    if (obj[k] && typeof obj[k] === "object" && !Array.isArray(obj[k])) {
      keys = keys.concat(getLeafKeys(obj[k], full));
    } else {
      keys.push(full);
    }
  }
  return keys;
}

const enKeys = new Set(getLeafKeys(en));
const taKeys = new Set(getLeafKeys(ta));
const hiKeys = new Set(getLeafKeys(hi));

const missingTa = [...enKeys].filter((k) => !taKeys.has(k));
const missingHi = [...enKeys].filter((k) => !hiKeys.has(k));

let hasErrors = false;

if (missingTa.length > 0) {
  console.error(`❌ Missing in ta.json (${missingTa.length} keys):`);
  missingTa.forEach((k) => console.error(`   - ${k}`));
  hasErrors = true;
} else {
  console.log("✅ ta.json has 100% key parity with en.json");
}

if (missingHi.length > 0) {
  console.error(`❌ Missing in hi.json (${missingHi.length} keys):`);
  missingHi.forEach((k) => console.error(`   - ${k}`));
  hasErrors = true;
} else {
  console.log("✅ hi.json has 100% key parity with en.json");
}

if (hasErrors) {
  process.exit(1);
} else {
  console.log(`🎉 All ${enKeys.size} translation keys are present in en.json, ta.json, and hi.json!`);
  process.exit(0);
}
