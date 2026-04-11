// md-to-pdf configuration for Palantir documents (pitch + review).
// Usage: npx md-to-pdf --config-file pdf-config.js <input.md>

module.exports = {
  stylesheet: ["pdf-style.css"],
  pdf_options: {
    format: "A4",
    margin: {
      top: "22mm",
      bottom: "22mm",
      left: "22mm",
      right: "22mm",
    },
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: "<div></div>",
    footerTemplate:
      '<div style="font-size:9px;width:100%;text-align:center;color:#888;padding:0 10mm;">' +
      '<span class="pageNumber"></span> / <span class="totalPages"></span>' +
      "</div>",
  },
  stylesheet_encoding: "utf-8",
};
