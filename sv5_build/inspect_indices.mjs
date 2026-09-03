import { FileBlob, PresentationFile } from "@oai/artifact-tool";
const presentation = await PresentationFile.importPptx(await FileBlob.load("D:/Mega/SV5-De-Cuong-Chi-Tiet-Agent-v2.pptx"));
for (const i of [2, 3, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15]) {
  const slide = presentation.slides.items[i];
  console.log("===== SLIDE", i + 1, "=====");
  for (const [j, shape] of slide.shapes.items.entries()) {
    let val = "";
    try { val = shape.text?.plainText ?? shape.text?.text ?? String(shape.text ?? ""); } catch {}
    if (val && val !== "[object Object]") console.log("idx",j,"|",JSON.stringify(val));
  }
}
