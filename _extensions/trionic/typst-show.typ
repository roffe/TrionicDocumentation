#show: doc => trionic(
$if(title)$
  title: [$title$],
$endif$
$if(subtitle)$
  subtitle: [$subtitle$],
$endif$
$if(trionic.running-title)$
  running-title: [$trionic.running-title$],
$endif$
$if(trionic.copyright)$
  copyright: [$trionic.copyright$],
$endif$
$if(trionic.revision)$
  revision: [$trionic.revision$],
$endif$
$if(trionic.cover)$
  cover: ($for(trionic.cover)$"$trionic.cover$",$endfor$),
$endif$
  toc-depth: $toc-depth$,
  doc,
)
