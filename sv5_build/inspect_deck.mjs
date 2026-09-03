import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const input = "D:/Mega/SV5-De-Cuong-Chi-Tiet-Agent-v2.pptx";
const presentation = await PresentationFile.importPptx(await FileBlob.load(input));
const snapshot = await presentation.inspect({
  kind: "deck,slide,textbox,shape,image,table,chart,notes,layout",
  maxChars: 30000,
});
console.log(snapshot.ndjson);
console.log("SLIDES", presentation.slides.items.length);
