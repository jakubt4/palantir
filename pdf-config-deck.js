// md-to-pdf configuration for the Spaceport_SK application deck.
// Separate from pdf-config.js (which targets A4 portrait document PDFs)
// to render a professional 16:9 landscape presentation deck suitable
// for both ESA/space industry and academic audiences.
//
// Usage: npx md-to-pdf --config-file pdf-config-deck.js SPACEPORT_SK_APPLICATION_DECK.en.md

module.exports = {
  stylesheet: ["pdf-style-deck.css"],
  pdf_options: {
    width: "338mm",              // 16:9 landscape, ~13.31 inches wide
    height: "190mm",             // ~7.48 inches tall
    preferCSSPageSize: true,     // respect @page size from pdf-style-deck.css
    margin: {
      top: "18mm",
      bottom: "20mm",            // extra room for footer
      left: "22mm",
      right: "22mm",
    },
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: "<div></div>",  // no header
    footerTemplate:
      '<div style="font-size:8px; width:100%; padding:0 22mm; display:flex; justify-content:space-between; align-items:center; color:#64748b; font-family:-apple-system,Segoe UI,Roboto,sans-serif;">' +
      '<span style="letter-spacing:0.05em;">PALANTIR  ·  SPACEPORT_SK 2026</span>' +
      '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span>' +
      "</div>",
  },
  stylesheet_encoding: "utf-8",
};
