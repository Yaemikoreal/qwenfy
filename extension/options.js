/**
 * Options Script
 */

document.addEventListener('DOMContentLoaded', async () => {
  const providerSelect = document.getElementById('provider');
  const apiKeyInput = document.getElementById('apiKey');
  const localModelInput = document.getElementById('localModel');
  const cacheEnabledInput = document.getElementById('cacheEnabled');
  const cacheSizeInput = document.getElementById('cacheSize');
  const apiKeyGroup = document.getElementById('apiKeyGroup');
  const localModelGroup = document.getElementById('localModelGroup');
  const saveBtn = document.getElementById('saveBtn');
  const clearCacheBtn = document.getElementById('clearCacheBtn');
  const statusEl = document.getElementById('status');
  
  const config = await chrome.runtime.sendMessage({ action: 'getConfig' });
  
  if (config) {
    providerSelect.value = config.provider || 'qwen';
    apiKeyInput.value = config.apiKey || '';
    localModelInput.value = config.localModel || 'qwen2:7b';
    cacheEnabledInput.checked = config.cacheEnabled !== false;
    cacheSizeInput.value = config.cacheSize || 1000;
  }
  
  function updateProviderUI() {
    const isLocal = providerSelect.value === 'local';
    apiKeyGroup.style.display = isLocal ? 'none' : 'block';
    localModelGroup.style.display = isLocal ? 'block' : 'none';
  }
  
  providerSelect.addEventListener('change', updateProviderUI);
  updateProviderUI();
  
  saveBtn.addEventListener('click', async () => {
    const newConfig = {
      provider: providerSelect.value,
      apiKey: apiKeyInput.value,
      localModel: localModelInput.value,
      cacheEnabled: cacheEnabledInput.checked,
      cacheSize: parseInt(cacheSizeInput.value, 10)
    };
    
    const response = await chrome.runtime.sendMessage({
      action: 'setConfig',
      config: newConfig
    });
    
    if (response && response.success) {
      showStatus('设置已保存', 'success');
    } else {
      showStatus('保存失败: ' + (response?.error || '未知错误'), 'error');
    }
  });
  
  clearCacheBtn.addEventListener('click', async () => {
    const response = await chrome.runtime.sendMessage({ action: 'clearCache' });
    
    if (response && response.success) {
      showStatus('缓存已清除', 'success');
    } else {
      showStatus('清除失败', 'error');
    }
  });
  
  function showStatus(message, type) {
    statusEl.textContent = message;
    statusEl.className = `status ${type}`;
    statusEl.style.display = 'block';
    
    setTimeout(() => {
      statusEl.style.display = 'none';
    }, 3000);
  }
});