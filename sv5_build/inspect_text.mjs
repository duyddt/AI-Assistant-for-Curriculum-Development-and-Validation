import { FileBlob, PresentationFile } from "@oai/artifact-tool";
const presentation = await PresentationFile.importPptx(await FileBlob.load("D:/Mega/SV5-De-Cuong-Chi-Tiet-Agent-v2.pptx"));
for (const i of [0, 1, 4, 6, 8, 12, 15]) {
  const slide = presentation.slides.items[i];
  console.log("===== SLIDE", i + 1, "=====");
  console.log("shape count", slide.shapes.items.length);
  for (const [j, shape] of slide.shapes.items.entries()) {
    let val = "";
    try { val = shape.text?.plainText ?? shape.text?.text ?? String(shape.text ?? ""); } catch {}
    if (val && val !== "[object Object]") console.log(j, shape.id, JSON.stringify(val));
  }
}
