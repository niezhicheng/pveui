import { createApp } from 'vue'
import WidgetApp from './WidgetApp.vue'

const createWidget = () => {
  const existing = document.getElementById('cs-widget-container')
  if (existing) {
    existing.remove()
  }
  const container = document.createElement('div')
  container.id = 'cs-widget-container'
  document.body.appendChild(container)

  const scriptEl = document.currentScript
  const dataset = scriptEl?.dataset || {}
  const config = {
    appId: dataset.appId || 'default',
    theme: dataset.theme || '#165dff',
    position: dataset.position || 'right',
  }

  createApp(WidgetApp, { config }).mount(container)
}

if (document.readyState === 'complete' || document.readyState === 'interactive') {
  createWidget()
} else {
  window.addEventListener('DOMContentLoaded', createWidget)
}


