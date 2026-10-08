---
name: canvas-csv-format
description: CSV format used to generate show canvases (characters/locations + image URLs); files live in ~/Downloads as "<Show> Canvas (output).csv"
metadata:
  type: reference
---

Canvas CSV (v3, "one url per row"): `tag,entity_type,name,description,sheet_image_url,variant_of,variant_label`
- tag/entity_type: `char`/`character`, `loc`/`location`
- one image URL per row; extra images of the same place = variant rows (variant_of = base name, variant_label = e.g. "kitchen", "exterior")
- description: one sentence, visual + role
- Inputs usually arrive as xlsx (Canvas sheet: name + IMAGE URL col; Location sheet: Name + Image URL/Image URL 2). Reuse descriptions from a prior output CSV when one exists.
- Examples: ~/Downloads/MAFIA Canvas (output).csv, WOBM Dragon Canvas (output v2).csv

In-sheet images (no public link): `python3 -I ~/projects/canvas-images/extract.py <xlsx> <out>` pulls xl/media images + manifest (sheet,row,col). Host them in a public GitHub repo TequilaTejas/canvas-images (Tejas chose this over Drive, 2026-10-06), use raw URLs in sheet_image_url. Canvas image = "Looks" columns; "3 Panel"/inspiration columns are references.

Confirmed 2026-10-06: Morphic downloads raw.githubusercontent URLs fine (Bridgerton). Default rule: ONE image per character, prefer "3 Panel" column, else "Looks"; never the "Reference" (actor inspiration) column. Repo folders per show, files named char-<slug>.png / loc-<slug>.png.

Gotcha (2026-10-07, FAE KING'S): extract.py anchor rows can be off by one (images overlapping the row above). Always build a labeled contact sheet and match images to names/"About" text before writing the CSV. openpyxl isn't installed; PIL works only without `-I` (user site-packages), so run helper scripts from the scratchpad.
