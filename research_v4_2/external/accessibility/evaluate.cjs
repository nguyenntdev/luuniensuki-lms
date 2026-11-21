// Compare released ACT outcomes to the rules declared by axe-core for each ACT ID.
const fs = require("node:fs");
const path = require("node:path");
const { createRequire } = require("node:module");
const fromFrontend = createRequire(path.resolve("frontend/package.json"));
const axe = fromFrontend("axe-core");
const { chromium } = fromFrontend("playwright");
const root = path.resolve(process.argv[2]);
const ids = ["23a2a8", "97a4e1", "e086e5", "6a7281", "b5c3f8"];

async function main() {
  const browser = await chromium.launch({executablePath: process.env.CHROME_BIN || "/opt/google/chrome/chrome"});
  const cases = [];
  try {
    for (const id of ids) {
      const rules = axe.getRules().filter(r => r.actIds?.includes(id)).map(r => r.ruleId);
      if (!rules.length) throw Error("Missing declared axe mapping for " + id);
      const file = fs.readdirSync(path.join(root, "_rules")).find(f => f.endsWith(id + ".md"));
      const doc = fs.readFileSync(path.join(root, "_rules", file), "utf8");
      const sections = doc.split(/^#### /m).slice(1);
      for (const section of sections) {
        const title = section.match(/^(Passed|Failed|Inapplicable) Example (\d+)/i);
        if (!title) continue;
        const record = {id, example: title[0], gold: title[1].toLowerCase(), rules};
        const blocks = Array.from(section.matchAll(/^```html[^\n]*\n([\s\S]*?)^```/gm));
        if (blocks.length !== 1) {
          cases.push({...record, output:"unexecuted"});
          continue;
        }
        const page = await browser.newPage();
        await page.route("**/*", async route => {
          const url = new URL(route.request().url());
          if (url.origin === "http://fixture.invalid" && url.pathname === "/case.html")
            return route.fulfill({contentType:"text/html", body: blocks[0][1]});
          if (url.origin === "http://fixture.invalid" && url.pathname.startsWith("/test-assets/")) {
            const asset = path.resolve(root, "." + decodeURIComponent(url.pathname));
            if (asset.startsWith(path.join(root, "test-assets") + path.sep) && fs.existsSync(asset) && fs.statSync(asset).isFile())
              return route.fulfill({path:asset});
          }
          return route.abort();
        });
        await page.goto("http://fixture.invalid/case.html");
        await page.addScriptTag({path:fromFrontend.resolve("axe-core/axe.min.js")});
        const output = await page.evaluate(async rules => {
          const r = await window.axe.run(document,{runOnly:{type:"rule",values:rules}});
          if (r.violations.length) return "failed";
          if (r.incomplete.length) return "incomplete";
          return r.passes.length ? "passed" : "inapplicable";
        }, rules);
        cases.push({...record, output});
        await page.close();
      }
    }
    process.stdout.write(JSON.stringify({version:axe.version,browser:browser.version(),cases},null,2)+"\n");
  } finally {
    await browser.close();
  }
}
main().catch(e => { console.error(e); process.exitCode = 1; });
