// The look of Dilemma's Word originals: Tahoma-like sans, running header
// "title | Chapter : Section", footer "copyright | revision | page".

#let heading-icon = state("heading-icon", none)

#let trionic(
  title: none,
  subtitle: none,
  running-title: none,
  copyright: none,
  revision: none,
  cover: (),
  toc-depth: 3,
  body,
) = {
  set document(title: title)
  // DejaVu Sans Condensed stands in for Tahoma (bundled in fonts/)
  set text(font: "DejaVu Sans", stretch: 87.5%, size: 9.5pt, lang: "en")
  set par(leading: 0.5em, spacing: 0.9em)
  show raw: set text(font: "DejaVu Sans Mono", size: 7.5pt)
  show link: set text(fill: rgb("#1f4e9c"))

  let small = text.with(size: 7pt)
  set page(
    paper: "us-letter",
    margin: (x: 92pt, top: 68pt, bottom: 76pt),
    header-ascent: 40%,
    footer-descent: 40%,
    header: context {
      if here().page() == 1 { return }
      // current chapter and the last section started on or before this page
      let p = here().page()
      let hs = query(heading.where(level: 1).or(heading.where(level: 2))).filter(h => h.location().page() <= p)
      let r = hs.rev().position(h => h.level == 1)
      let where = if r != none {
        let i = hs.len() - 1 - r
        let sec = hs.slice(i + 1).filter(h => h.level == 2)
        [#hs.at(i).body#if sec.len() > 0 [ : _#sec.last().body;_]]
      }
      small[#running-title #h(1fr) #where]
      v(-0.6em)
      line(length: 100%, stroke: 0.4pt)
    },
    footer: context {
      if here().page() == 1 { return }
      line(length: 100%, stroke: 0.4pt)
      v(-0.6em)
      small[#copyright #h(1fr) #revision #h(1fr) _#counter(page).display()_]
    },
  )

  show heading: set block(above: 1.6em, below: 0.9em, sticky: true)
  show heading.where(level: 1): set text(size: 15pt, weight: "bold")
  show heading.where(level: 2): set text(size: 13pt, weight: "bold", style: "italic")
  show heading.where(level: 3): set text(size: 10.5pt, weight: "regular", style: "italic")
  show heading.where(level: 4): set text(size: 10pt, weight: "bold", style: "italic")
  // one rule for chapters starting a page and the icon, a second rule would never see an icon heading
  show heading: it => context {
    if it.level == 1 { pagebreak(weak: true) }
    let icon = heading-icon.get()
    if icon == none { it } else {
      block(it.body + h(0.5em) + box(baseline: 15%, image("_extensions/trionic/icons/" + icon + ".png", height: 1.1em)))
    }
  }

  show figure.caption: set text(weight: "bold")
  set figure.caption(separator: [:])   // Quarto puts a space in front of the caption text
  set table(stroke: 0.5pt + luma(90), inset: 4pt)
  show table: set text(size: 8.5pt)

  // title page
  page(header: none, footer: none, {
    align(center, text(size: 22pt, weight: "bold", underline(title)))
    if subtitle != none { align(center, text(size: 12pt, subtitle)) }
    v(2em)
    for c in cover {
      align(center, block(stroke: 0.5pt, image(c, width: 75%)))
      v(1.5em)
    }
  })

  outline(title: "Table of contents", depth: toc-depth, indent: 1.2em)
  pagebreak()

  body
}
