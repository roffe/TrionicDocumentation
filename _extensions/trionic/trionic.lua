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

-- A picture without a caption is centered, like in the originals, and a short
-- lead-in right above a picture stays on the picture's page.
local function is_bare_picture(b)
  return b and b.t == "Para" and #b.content == 1 and b.content[1].t == "Image"
end

local function is_picture(b)
  return b and (b.t == "Figure" or is_bare_picture(b))
end

local function wrap(open, b)
  return { pandoc.RawBlock("typst", open), b, pandoc.RawBlock("typst", "]") }
end

function Blocks(blocks)
  if not quarto.doc.is_format("typst") then return nil end
  local out = pandoc.Blocks({})
  for i, b in ipairs(blocks) do
    if is_bare_picture(b) then
      out:extend(wrap("#align(center)[", b))
    elseif b.t == "Para" and is_picture(blocks[i + 1]) and #pandoc.utils.stringify(b) < 200 then
      out:extend(wrap("#block(sticky: true)[", b))
    else
      out:insert(b)
    end
  end
  return out
end
