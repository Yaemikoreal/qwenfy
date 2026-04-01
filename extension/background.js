/**
 * Background Service Worker
 * 处理翻译请求、缓存管理、消息路由
 */

const API_ENDPOINTS = {
  qwen: 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
  openai: 'https://api.openai.com/v1/chat/completions',
  deepseek: 'https://api.deepseek.com/v1/chat/completions',
  local: 'http://localhost:11434/api/chat'
};

let config = {
  provider: 'qwen',
  apiKey: '',
  localModel: 'qwen2:7b',
  cacheEnabled: true,
  cacheSize: 1000
};

let cache = new Map();
let cacheOrder = [];

async function loadConfig() {
  const stored = await chrome.storage.sync.get('config');
  if (stored.config) {
    config = { ...config, ...stored.config };
  }
}

async function saveConfig(newConfig) {
  config = { ...config, ...newConfig };
  await chrome.storage.sync.set({ config });
}

function getFromCache(key) {
  if (!config.cacheEnabled) return null;
  
  if (cache.has(key)) {
    const value = cache.get(key);
    cacheOrder = cacheOrder.filter(k => k !== key);
    cacheOrder.push(key);
    return value;
  }
  return null;
}

function setToCache(key, value) {
  if (!config.cacheEnabled) return;
  
  if (cache.size >= config.cacheSize) {
    const oldest = cacheOrder.shift();
    cache.delete(oldest);
  }
  
  cache.set(key, value);
  cacheOrder.push(key);
}

function generateCacheKey(text, sourceLang, targetLang) {
  return `${sourceLang}:${targetLang}:${text}`;
}

async function translateWithCloud(text, sourceLang = 'auto', targetLang = 'zh') {
  const endpoint = API_ENDPOINTS[config.provider];
  
  if (!config.apiKey && config.provider !== 'local') {
    throw new Error('请先配置 API Key');
  }
  
  const prompt = `Translate the following text from ${sourceLang} to ${targetLang}. Provide only the translation, without any explanation.\n\n${text}`;
  
  let requestBody;
  let headers = { 'Content-Type': 'application/json' };
  
  if (config.provider === 'qwen') {
    headers['Authorization'] = `Bearer ${config.apiKey}`;
    requestBody = {
      model: 'qwen-turbo',
      input: { messages: [{ role: 'user', content: prompt }] },
      parameters: { temperature: 0.3 }
    };
  } else if (config.provider === 'local') {
    requestBody = {
      model: config.localModel,
      messages: [{ role: 'user', content: prompt }],
      stream: false
    };
  } else {
    headers['Authorization'] = `Bearer ${config.apiKey}`;
    requestBody = {
      model: 'gpt-3.5-turbo',
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.3
    };
  }
  
  const response = await fetch(endpoint, {
    method: 'POST',
    headers,
    body: JSON.stringify(requestBody)
  });
  
  if (!response.ok) {
    throw new Error(`API 请求失败: ${response.status}`);
  }
  
  const data = await response.json();
  
  let translatedText;
  if (config.provider === 'qwen') {
    translatedText = data.output?.text || '';
  } else if (config.provider === 'local') {
    translatedText = data.message?.content || '';
  } else {
    translatedText = data.choices?.[0]?.message?.content || '';
  }
  
  return translatedText.trim();
}

async function translate(text, sourceLang = 'auto', targetLang = 'zh') {
  const cacheKey = generateCacheKey(text, sourceLang, targetLang);
  
  const cached = getFromCache(cacheKey);
  if (cached) {
    return { text: cached, cached: true, engine: 'cache' };
  }
  
  try {
    const translated = await translateWithCloud(text, sourceLang, targetLang);
    
    setToCache(cacheKey, translated);
    
    return { text: translated, cached: false, engine: config.provider };
  } catch (error) {
    console.error('Translation error:', error);
    throw error;
  }
}

chrome.runtime.onInstalled.addListener(() => {
  loadConfig();
  
  chrome.contextMenus.create({
    id: 'translate-selection',
    title: '翻译选中内容',
    contexts: ['selection']
  });
  
  chrome.contextMenus.create({
    id: 'translate-page',
    title: '翻译整页',
    contexts: ['page']
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'translate-selection') {
    chrome.tabs.sendMessage(tab.id, {
      action: 'translateSelection',
      text: info.selectionText
    });
  } else if (info.menuItemId === 'translate-page') {
    chrome.tabs.sendMessage(tab.id, {
      action: 'translatePage'
    });
  }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'translate') {
    translate(request.text, request.sourceLang, request.targetLang)
      .then(result => sendResponse({ success: true, ...result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
  
  if (request.action === 'getConfig') {
    sendResponse(config);
    return true;
  }
  
  if (request.action === 'setConfig') {
    saveConfig(request.config)
      .then(() => sendResponse({ success: true }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
  
  if (request.action === 'clearCache') {
    cache.clear();
    cacheOrder = [];
    sendResponse({ success: true });
    return true;
  }
});

chrome.commands.onCommand.addListener((command) => {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (command === 'translate-selection') {
      chrome.tabs.sendMessage(tabs[0].id, { action: 'translateSelection' });
    } else if (command === 'translate-page') {
      chrome.tabs.sendMessage(tabs[0].id, { action: 'translatePage' });
    }
  });
});

loadConfig();