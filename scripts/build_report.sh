#!/bin/sh
# Build docs/GraphVOI_Round2_report.pdf from docs/REPORT.md (pandoc + tectonic).
set -e
cd "$(dirname "$0")/../docs"
pandoc REPORT.md --from markdown --pdf-engine=tectonic -H report/header.tex \
  -V fontsize=10pt -V mainfont=texgyretermes -V 'mainfontoptions=Extension=.otf,UprightFont=*-regular,BoldFont=*-bold,ItalicFont=*-italic,BoldItalicFont=*-bolditalic' -V papersize=a4 -V colorlinks=true \
  --resource-path=. -o GraphVOI_Round2_report.pdf
echo "wrote docs/GraphVOI_Round2_report.pdf"
