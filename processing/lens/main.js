import puppeteer from "puppeteer-extra";
import StealthPlugin from "puppeteer-extra-plugin-stealth";

puppeteer.use(StealthPlugin());

const searchParams = {
  imageUrl: "http://raw.githubusercontent.com/tylerbisk/cv-birdfeeder/master/img/lens.png", //Parameter defines the URL of an image to perform the Google Lens search
  hl: "en", //Parameter defines the language to use for the Google search
  gl: "US",
};

const URL = `https://lens.google.com/uploadbyurl?url=${searchParams.imageUrl}&hl=${searchParams.hl}&gl=${searchParams.gl}`;


async function getResultsFromPage(page) {
  const labels = await page.$$(".DeMn2d");

  let label = await Promise.all(labels.map(async (t) => {
    return await t.evaluate(x => x.textContent);
  }))

  // let sublabels = await page.$$(".XNTym");

  // let sublabel = await Promise.all(sublabels.map(async (t) => {
  //   return await t.evaluate(x => x.textContent);
  // }))

  //await page.waitForTimeout(2000);
  if (label.length === 0) {
    return "";
  }
  return label[0];
}


async function getLensResults() {
  const browser = await puppeteer.launch({
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
    executablePath: '/usr/bin/chromium-browser',
    headless: "new", // false for debuggung to see what is going on
  });
  const page = await browser.newPage();
  await page.setDefaultNavigationTimeout(90000);
  await page.goto(URL);
  const results = await getResultsFromPage(page);
  await browser.close();
  return results;
}


getLensResults().then((result) => console.dir(result, { depth: null }));
