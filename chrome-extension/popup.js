document.getElementById("btnResumir").addEventListener("click", async () => {
    const loader = document.getElementById("loader");
    const resumoDiv = document.getElementById("resumo");
    resumoDiv.textContent = "";
    loader.style.display = "block";

    // Captura o texto da página ativa
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => document.body.innerText
    }, async (results) => {
        const textoPagina = results[0].result;

        // Envia para o backend Flask
        try {
            const response = await fetch("http://127.0.0.1:5000/resumir", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: textoPagina })
            });

            if (!response.ok) throw new Error("Erro ao gerar resumo");

            const data = await response.json();
            resumoDiv.textContent = data.resumo;
        } catch (err) {
            resumoDiv.textContent = "Erro: " + err.message;
        } finally {
            loader.style.display = "none";
        }
    });
});
