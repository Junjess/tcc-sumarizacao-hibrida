// ----------------------------
// Estilo
// ----------------------------
const style = document.createElement("style");
style.innerHTML = `
  .highlighted-text { background-color: yellow; cursor: pointer; }
  #resumo-panel {
    position: fixed;
    top: 10px;
    right: 10px;
    width: 320px;
    max-height: 80vh;
    background: white;
    border: 2px solid black;
    padding: 10px;
    z-index: 99999;
    overflow-y: auto;
    font-family: sans-serif;
  }
  #resumo-panel button { margin: 5px 0; width: 100%; cursor: pointer; }
  #resumo-output { margin-top: 5px; font-size: 0.9em; }
  .section-title { font-weight: bold; margin-top: 10px; }
  .section-summary { margin-bottom: 10px; font-size: 0.9em; }
`;
document.head.appendChild(style);

// ----------------------------
// Painel
// ----------------------------
const panel = document.createElement("div");
panel.id = "resumo-panel";
panel.innerHTML = `
  <button id="pen-btn">🖊️ Ativar Caneta</button>
  <button id="resumo-btn">Gerar Resumo</button>
  <button id="clear-btn">Limpar Todas Marcações</button>
  <button id="close-btn">❌ Fechar Painel</button>
  <div id="resumo-output">Nenhum texto marcado.</div>
`;
document.body.appendChild(panel);

// ----------------------------
// Estado e referências
// ----------------------------
let penActive = false;
let highlights = [];

const penButton = document.getElementById("pen-btn");
const resumoButton = document.getElementById("resumo-btn");
const clearButton = document.getElementById("clear-btn");
const closeButton = document.getElementById("close-btn");
const output = document.getElementById("resumo-output");

// ----------------------------
// Botões
// ----------------------------
penButton.addEventListener("click", () => {
  penActive = !penActive;
  penButton.style.backgroundColor = penActive ? "yellow" : "";
  output.textContent = penActive ? "Caneta ativada. Selecione o texto." : "Caneta desativada.";
});

closeButton.addEventListener("click", () => {
  panel.remove();
  highlights = [];
});

// ----------------------------
// Função para destacar seleção
// ----------------------------
function highlightSelection() {
  const selection = window.getSelection();
  if (!selection || selection.isCollapsed) return;

  const ranges = [];
  for (let i = 0; i < selection.rangeCount; i++) {
    ranges.push(selection.getRangeAt(i));
  }

  ranges.forEach(range => {
    const textNodes = [];
    const walker = document.createTreeWalker(
      range.commonAncestorContainer,
      NodeFilter.SHOW_TEXT,
      { acceptNode: node => range.intersectsNode(node) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT }
    );

    while (walker.nextNode()) textNodes.push(walker.currentNode);

    textNodes.forEach(node => {
      const nodeRange = document.createRange();
      nodeRange.selectNodeContents(node);

      if (node === textNodes[0]) nodeRange.setStart(node, Math.max(0, range.startOffset));
      if (node === textNodes[textNodes.length - 1]) nodeRange.setEnd(node, Math.min(node.length, range.endOffset));

      const span = document.createElement("span");
      span.className = "highlighted-text";
      const highlightId = "h" + Date.now() + Math.random().toString(16).slice(2);
      span.dataset.id = highlightId;

      try {
        nodeRange.surroundContents(span);
        highlights.push({ id: highlightId, text: span.textContent });
      } catch (e) {
        console.warn("Não foi possível destacar este nó:", e);
      }
    });
  });

  selection.removeAllRanges();
  if (highlights.length > 0) {
    output.textContent = `Texto marcado! Total: ${highlights.length} trechos.`;
  }
}

// ----------------------------
// Detecta seleção
// ----------------------------
document.addEventListener("mouseup", () => {
  if (!penActive || !window.getSelection) return;
  const selection = window.getSelection();
  if (selection.isCollapsed) return;

  const panel = document.getElementById("resumo-panel");
  if (panel.contains(selection.anchorNode) || panel.contains(selection.focusNode)) return;

  highlightSelection();
});

// ----------------------------
// Limpar marcações
// ----------------------------
clearButton.addEventListener("click", () => {
  const spans = document.querySelectorAll(".highlighted-text");
  spans.forEach(span => {
    const parent = span.parentNode;
    parent.replaceChild(document.createTextNode(span.textContent), span);
  });
  highlights = [];
  output.textContent = "Todas as marcações foram removidas.";
});

// ----------------------------
// Remover highlight individual
// ----------------------------
document.addEventListener("click", e => {
  if (e.target.classList.contains("highlighted-text")) {
    const span = e.target;
    const id = span.dataset.id;

    highlights = highlights.filter(h => h.id !== id);

    const parent = span.parentNode;
    parent.replaceChild(document.createTextNode(span.textContent), span);

    output.textContent = `Marcação removida! Total: ${highlights.length} trechos restantes.`;
  }
});

// ----------------------------
// Gerar resumo
// ----------------------------
resumoButton.addEventListener("click", () => {
  const texto = highlights.map(h => h.text).join("\n");

  if (!texto) {
    output.textContent = "Nenhum texto marcado!";
    return;
  }

  output.innerHTML = "Gerando resumo...";
  fetch("http://127.0.0.1:5000/resumir", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ html: texto })
  })
    .then(res => res.json())
    .then(data => {
      if (!data || !data.resumo_coeso) {
        output.textContent = "Erro: resposta inesperada do servidor.";
        return;
      }

      output.innerHTML = "";

      // ----------------------------
      // Resumo coeso geral dividido em parágrafos
      // ----------------------------
      const coesoTitle = document.createElement("div");
      coesoTitle.className = "section-title";
      coesoTitle.textContent = "Resumo Geral";
      output.appendChild(coesoTitle);

      const resumo = data.resumo_coeso || "Resumo não disponível.";
      resumo.split(/(?<=\.)\s+/).forEach(paragrafo => {
        const p = document.createElement("div");
        p.className = "section-summary";
        p.textContent = paragrafo.trim();
        output.appendChild(p);
      });
    })
    .catch(err => {
      output.textContent = "Erro de conexão: " + err;
    });
});
