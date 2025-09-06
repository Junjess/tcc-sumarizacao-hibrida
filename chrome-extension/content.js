// Captura todo o texto visível da página
function getPageText() {
  return document.body.innerText;
}

// Escuta mensagem da popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "resumirPagina") {
    const textoPagina = getPageText();
    sendResponse({ texto: textoPagina });
  }
});
