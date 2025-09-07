chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.id) return;

  try {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["content.js"]
    });
    console.log("Content script injetado!");
  } catch (err) {
    console.error("Erro ao injetar content script:", err);
  }
});
