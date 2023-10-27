import puppeteer from "puppeteer-extra";
import StealthPlugin from "puppeteer-extra-plugin-stealth";

puppeteer.use(StealthPlugin());
const searchParams = {
  imageUrl: "https://cdn.britannica.com/16/234216-050-C66F8665/beagle-hound-dog.jpg", //Parameter defines the URL of an image to perform the Google Lens search
  hl: "en", //Parameter defines the language to use for the Google search
  gl: "US",
};
const URL = `https://lens.google.com/uploadbyurl?url=${searchParams.imageUrl}&hl=${searchParams.hl}&gl=${searchParams.gl}`;
async function getResultsFromPage(page) {
  const image = await page.$$(".bn6k9b");
  await Promise.all(image.map(async (t) => {await t.click();}));
  const knowledgeGraphItems = await page.$$(".DeMn2d");
  console.log(knowledgeGraphItems);
  const knowledgeGraph = [];
  for (const item of knowledgeGraphItems) {
    console.log(item);
    const label = await item.evaluate(x => x.textContent);
    console.log(label);
    const handles = await Promise.all(knowledgeGraphItems.map(handle => handle.getProperty("src")));
    console.log(handles);
    const label2 = handle.textContent;
    console.log(label2);
    await item.click();
    await page.waitForTimeout(2000);
    const thumbnail = await item.$eval(".FH8DCc", (node) => node.getAttribute("src"));
    knowledgeGraph.push(
      await page.evaluate(
        (thumbnail) => ({
          title: document.querySelector(".DeMn2d").textContent,
          subtitle: document.querySelector(".XNTym").textContent,
        }),
        thumbnail
      )
    );
  }
  return { knowledgeGraph };
}
async function getLensResults() {
  const browser = await puppeteer.launch({
    headless: true, // if you want to see what the browser is doing, you need to change this option to "false"
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
    executablePath: '/usr/bin/chromium-browser',
    headless: "new",
  });
  const page = await browser.newPage();
  await page.setDefaultNavigationTimeout(60000);
  await page.goto(URL);
  const results = await getResultsFromPage(page);
  await browser.close();
  return results;
}
getLensResults().then((result) => console.dir(result, { depth: null }));
