/**
 * Content Script
 * 处理页面内翻译、划词翻译、整页翻译
 */

class QwenfyContent {
  constructor() {
    this.popup = null;
    this.isTranslating = false;
    this.init();
  }
  
  init() {
    this.createStyles();
    this.bindEvents();
  }
  
  createStyles() {
    if (document.getElementById('qwenfy-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'qwenfy-styles';
    style.textContent = `
      .qwenfy-popup {
        position: fixed;
        z-index: 2147483647;
        background: #ffffff;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 14px;
        max-width: 400px;
        min-width: 200px;
        overflow: hidden;
      }
      
      .qwenfy-popup-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 12px;
        background: #f8f9fa;
        border-bottom: 1px solid #e9ecef;
      }
      
      .qwenfy-popup-title {
        font-weight: 600;
        color: #333;
      }
      
      .qwenfy-popup-close {
        background: none;
        border: none;
        font-size: 18px;
        color: #999;
        cursor: pointer;
        padding: 0;
        line-height: 1;
      }
      
      .qwenfy-popup-close:hover {
        color: #333;
      }
      
      .qwenfy-popup-content {
        padding: 12px;
      }
      
      .qwenfy-source {
        color: #666;
        font-size: 13px;
        margin-bottom: 8px;
        padding-bottom: 8px;
        border-bottom: 1px solid #eee;
      }
      
      .qwenfy-target {
        color: #333;
        line-height: 1.6;
      }
      
      .qwenfy-popup-footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 12px;
        background: #f8f9fa;
        border-top: 1px solid #e9ecef;
        font-size: 12px;
        color: #999;
      }
      
      .qwenfy-popup-actions {
        display: flex;
        gap: 8px;
      }
      
      .qwenfy-btn {
        background: #3498db;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 4px 10px;
        font-size: 12px;
        cursor: pointer;
        transition: background 0.2s;
      }
      
      .qwenfy-btn:hover {
        background: #2980b9;
      }
      
      .qwenfy-btn-secondary {
        background: #ecf0f1;
        color: #333;
      }
      
      .qwenfy-btn-secondary:hover {
        background: #bdc3c7;
      }
      
      .qwenfy-loading {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #999;
      }
      
      .qwenfy-spinner {
        width: 16px;
        height: 16px;
        border: 2px solid #e9ecef;
        border-top-color: #3498db;
        border-radius: 50%;
        animation: qwenfy-spin 0.8s linear infinite;
      }
      
      @keyframes qwenfy-spin {
        to { transform: rotate(360deg); }
      }
      
      .qwenfy-float-btn {
        position: absolute;
        z-index: 2147483646;
        background: #3498db;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 6px 12px;
        font-size: 12px;
        cursor: pointer;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        transition: all 0.2s;
      }
      
      .qwenfy-float-btn:hover {
        background: #2980b9;
        transform: translateY(-1px);
      }
      
      .qwenfy-highlight {
        background-color: #fff3cd;
        transition: background-color 0.3s;
      }
      
      .qwenfy-translated {
        background-color: #d4edda;
        border-bottom: 2px solid #28a745;
      }
    `;
    document.head.appendChild(style);
  }
  
  bindEvents() {
    document.addEventListener('mouseup', (e) => this.handleMouseUp(e));
    document.addEventListener('mousedown', (e) => this.handleMouseDown(e));
    
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      if (request.action === 'translateSelection') {
        const selection = window.getSelection().toString().trim();
        if (selection) {
          this.translateText(selection);
        }
      } else if (request.action === 'translatePage') {
        this.translatePage();
      }
      return true;
    });
  }
  
  handleMouseUp(e) {
    if (e.target.closest('.qwenfy-popup')) return;
    
    setTimeout(() => {
      const selection = window.getSelection().toString().trim();
      if (selection && selection.length > 0) {
        this.showFloatButton(e.clientX, e.clientY, selection);
      } else {
        this.hideFloatButton();
      }
    }, 10);
  }
  
  handleMouseDown(e) {
    if (!e.target.closest('.qwenfy-popup') && !e.target.closest('.qwenfy-float-btn')) {
      this.hidePopup();
    }
  }
  
  showFloatButton(x, y, text) {
    this.hideFloatButton();
    
    const btn = document.createElement('button');
    btn.className = 'qwenfy-float-btn';
    btn.textContent = '翻译';
    btn.style.left = `${x + 10}px`;
    btn.style.top = `${y + 10}px`;
    
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      this.translateText(text, x, y);
      this.hideFloatButton();
    });
    
    document.body.appendChild(btn);
    this.floatBtn = btn;
  }
  
  hideFloatButton() {
    if (this.floatBtn) {
      this.floatBtn.remove();
      this.floatBtn = null;
    }
  }
  
  translateText(text, x, y) {
    if (this.isTranslating) return;
    
    const selection = window.getSelection();
    let rect = { left: x || 100, top: y || 100, width: 0, height: 0 };
    
    if (selection.rangeCount > 0) {
      const range = selection.getRangeAt(0);
      rect = range.getBoundingClientRect();
    }
    
    this.showPopup(rect.left, rect.bottom + 10, text);
    this.isTranslating = true;
    
    chrome.runtime.sendMessage(
      { action: 'translate', text, sourceLang: 'auto', targetLang: 'zh' },
      (response) => {
        this.isTranslating = false;
        
        if (response && response.success) {
          this.updatePopup(response.text, response.cached, response.engine);
        } else {
          this.updatePopup('翻译失败: ' + (response?.error || '未知错误'), false, 'error');
        }
      }
    );
  }
  
  showPopup(x, y, sourceText) {
    this.hidePopup();
    
    const popup = document.createElement('div');
    popup.className = 'qwenfy-popup';
    popup.innerHTML = `
      <div class="qwenfy-popup-header">
        <span class="qwenfy-popup-title">Qwenfy</span>
        <button class="qwenfy-popup-close">&times;</button>
      </div>
      <div class="qwenfy-popup-content">
        <div class="qwenfy-source">${this.escapeHtml(sourceText)}</div>
        <div class="qwenfy-target">
          <div class="qwenfy-loading">
            <div class="qwenfy-spinner"></div>
            <span>翻译中...</span>
          </div>
        </div>
      </div>
      <div class="qwenfy-popup-footer">
        <span class="qwenfy-status"></span>
        <div class="qwenfy-popup-actions">
          <button class="qwenfy-btn qwenfy-btn-secondary qwenfy-copy-btn">复制</button>
        </div>
      </div>
    `;
    
    const maxX = window.innerWidth - 420;
    const maxY = window.innerHeight - 300;
    popup.style.left = `${Math.min(x, maxX)}px`;
    popup.style.top = `${Math.min(y, maxY)}px`;
    
    popup.querySelector('.qwenfy-popup-close').addEventListener('click', () => {
      this.hidePopup();
    });
    
    document.body.appendChild(popup);
    this.popup = popup;
  }
  
  updatePopup(translatedText, cached, engine) {
    if (!this.popup) return;
    
    const targetEl = this.popup.querySelector('.qwenfy-target');
    targetEl.textContent = translatedText;
    
    const statusEl = this.popup.querySelector('.qwenfy-status');
    const statusText = cached ? '缓存' : engine;
    statusEl.textContent = statusText;
    
    this.popup.querySelector('.qwenfy-copy-btn').addEventListener('click', () => {
      navigator.clipboard.writeText(translatedText);
      statusEl.textContent = '已复制';
      setTimeout(() => {
        statusEl.textContent = statusText;
      }, 2000);
    });
  }
  
  hidePopup() {
    if (this.popup) {
      this.popup.remove();
      this.popup = null;
    }
  }
  
  async translatePage() {
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: (node) => {
          if (node.parentElement.closest('script, style, noscript, iframe, canvas, svg')) {
            return NodeFilter.FILTER_REJECT;
          }
          if (node.textContent.trim().length < 5) {
            return NodeFilter.FILTER_REJECT;
          }
          return NodeFilter.FILTER_ACCEPT;
        }
      }
    );
    
    const textNodes = [];
    while (walker.nextNode()) {
      textNodes.push(walker.currentNode);
    }
    
    const batchSize = 10;
    for (let i = 0; i < textNodes.length; i += batchSize) {
      const batch = textNodes.slice(i, i + batchSize);
      
      for (const node of batch) {
        const text = node.textContent.trim();
        if (text) {
          try {
            const response = await new Promise((resolve) => {
              chrome.runtime.sendMessage(
                { action: 'translate', text, sourceLang: 'auto', targetLang: 'zh' },
                resolve
              );
            });
            
            if (response && response.success) {
              node.parentElement.classList.add('qwenfy-translated');
              node.textContent = response.text;
            }
          } catch (error) {
            console.error('Translation error:', error);
          }
        }
      }
      
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }
  
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

new QwenfyContent();