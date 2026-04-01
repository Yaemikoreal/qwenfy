/**
 * Popup Script
 */

document.addEventListener('DOMContentLoaded', () => {
  const inputText = document.getElementById('inputText');
  const translateBtn = document.getElementById('translateBtn');
  const resultArea = document.getElementById('resultArea');
  const resultText = document.getElementById('resultText');
  const copyBtn = document.getElementById('copyBtn');
  const clearBtn = document.getElementById('clearBtn');
  const statusText = document.getElementById('statusText');
  const settingsBtn = document.getElementById('settingsBtn');
  
  let isTranslating = false;
  
  translateBtn.addEventListener('click', async () => {
    const text = inputText.value.trim();
    if (!text || isTranslating) return;
    
    isTranslating = true;
    translateBtn.disabled = true;
    translateBtn.textContent = '翻译中...';
    
    resultArea.style.display = 'block';
    resultText.innerHTML = '<div class="loading"><div class="spinner"></div><span>正在翻译...</span></div>';
    statusText.textContent = '';
    
    try {
      const response = await chrome.runtime.sendMessage({
        action: 'translate',
        text,
        sourceLang: 'auto',
        targetLang: 'zh'
      });
      
      if (response && response.success) {
        resultText.textContent = response.text;
        statusText.textContent = response.cached ? '缓存' : `引擎: ${response.engine}`;
      } else {
        resultText.innerHTML = `<span class="error">翻译失败: ${response?.error || '未知错误'}</span>`;
      }
    } catch (error) {
      resultText.innerHTML = `<span class="error">错误: ${error.message}</span>`;
    } finally {
      isTranslating = false;
      translateBtn.disabled = false;
      translateBtn.textContent = '翻译';
    }
  });
  
  copyBtn.addEventListener('click', () => {
    const text = resultText.textContent;
    if (text && !text.includes('翻译失败') && !text.includes('错误')) {
      navigator.clipboard.writeText(text).then(() => {
        statusText.textContent = '已复制到剪贴板';
        setTimeout(() => {
          statusText.textContent = '';
        }, 2000);
      });
    }
  });
  
  clearBtn.addEventListener('click', () => {
    inputText.value = '';
    resultArea.style.display = 'none';
    statusText.textContent = '';
  });
  
  settingsBtn.addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
  });
  
  inputText.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      translateBtn.click();
    }
  });
  
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    chrome.tabs.sendMessage(tabs[0].id, { action: 'getSelection' }, (response) => {
      if (response && response.text) {
        inputText.value = response.text;
      }
    });
  });
});