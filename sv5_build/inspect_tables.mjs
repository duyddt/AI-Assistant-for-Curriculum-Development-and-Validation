import { FileBlob, PresentationFile } from "@oai/artifact-tool";
const presentation = await PresentationFile.importPptx(await FileBlob.load("D:/Mega/SV5-De-Cuong-Chi-Tiet-Agent-v2.pptx"));
for (const [i, slide] of presentation.slides.items.entries()) {
  for (const [j, table] of slide.tables.items.entries()) {
    console.log("===== slide", i + 1, "table", j, "=====");
    console.log("rows", table.rows, "cols", table.cols, "id", table.id);
    for (let r = 0; r < table.rows; r++) {
      const vals = [];
      for (let c = 0; c < table.cols; c++) {
        const cell = table.getCell(r, c);
        let val = "";
        try { val = cell.text?.plainText ?? cell.text?.text ?? String(cell.text ?? ""); } catch {}
        vals.push(val);
      }
      console.log(r, JSON.stringify(vals));
    }
  }
}
