import { FileBlob, PresentationFile } from "@oai/artifact-tool";
const presentation = await PresentationFile.importPptx(await FileBlob.load("D:/Mega/files/SV5-Bao-Cao-Tuan-Nay-Final.pptx"));
for (const i of [0, 15]) {
  const slide = presentation.slides.items[i];
  console.log("slide", i + 1);
  for (const [j, item] of slide.shapes.items.entries()) {
    const p = item.position;
    if (p && (p.left < 0 || p.top < 0 || p.left + p.width > 1280 || p.top + p.height > 720)) {
      console.log(j, item.id, item.geometry, JSON.stringify(p));
    }
  }
}
