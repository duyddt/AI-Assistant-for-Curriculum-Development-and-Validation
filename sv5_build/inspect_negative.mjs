import { FileBlob, PresentationFile } from "@oai/artifact-tool";
const presentation = await PresentationFile.importPptx(await FileBlob.load("D:/Mega/SV5-De-Cuong-Chi-Tiet-Agent-v2.pptx"));
for (const [i, slide] of presentation.slides.items.entries()) {
  for (const [j, s] of slide.shapes.items.entries()) {
    const p = s.position;
    if (p && (p.width < 0 || p.height < 0)) {
      console.log(i + 1, j, s.id, s.geometry, JSON.stringify(p));
    }
  }
}
