-- Headings marked {.advanced} or {.references} get the icon from the original documents
-- next to them. The heading itself stays plain so the TOC and running header don't show it.
-- The empty root index.qmd (Quarto books need one) would leave an empty chapter, drop it.
function Header(el)
  if not quarto.doc.is_format("typst") then return nil end
  if el.level == 1 and #el.content == 0 then return {} end
  for _, icon in ipairs({ "advanced", "references" }) do
    if el.classes:includes(icon) then
      return {
        pandoc.RawBlock("typst", '#heading-icon.update("' .. icon .. '")'),
        el,
        pandoc.RawBlock("typst", "#heading-icon.update(none)"),
      }
    end
  end
end

-- A picture on its own without a caption is centered, like in the originals.
function Para(el)
  if not quarto.doc.is_format("typst") then return nil end
  if #el.content == 1 and el.content[1].t == "Image" then
    return { pandoc.RawBlock("typst", "#align(center)["), el, pandoc.RawBlock("typst", "]") }
  end
end

-- Typst books get Quarto's rule that restarts figure numbers at every chapter,
-- the originals number them straight through the book.
function Meta(meta)
  if not quarto.doc.is_format("typst") or not meta["include-before"] then return nil end
  local keep = pandoc.List()
  for _, item in ipairs(meta["include-before"]) do
    local b = item[1]
    if not (b and b.t == "RawBlock" and b.text:find("Reset Quarto's custom figure counters", 1, true)) then
      keep:insert(item)
    end
  end
  meta["include-before"] = keep
  return meta
end

-- Header rows in bold (a Typst show rule can't reach table.header's cells).
function Table(el)
  if not quarto.doc.is_format("typst") then return nil end
  local bold = {
    Plain = function(b) return pandoc.Plain(pandoc.Strong(b.content)) end,
    Para = function(b) return pandoc.Para(pandoc.Strong(b.content)) end,
  }
  for _, row in ipairs(el.head.rows) do
    for _, cell in ipairs(row.cells) do
      cell.contents = cell.contents:walk(bold)
    end
  end
  return el
end
