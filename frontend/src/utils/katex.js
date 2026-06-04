/**
 * KaTeX 渲染工具函数
 * 在 ChatView、ErrorBookView、PracticeView 中共享
 */
import katex from 'katex'
import 'katex/dist/katex.min.css'

export function renderKaTeX(text) {
  if (!text) return ''
  let html = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  html = html.replace(/\$\$([\s\S]*?)\$\$/g, (_, f) => {
    try { return katex.renderToString(f.trim(), { displayMode: true, throwOnError: false }) }
    catch { return `<div class="formula-error">$${f}$$</div>` }
  })
  html = html.replace(/\$([^$\n]+?)\$/g, (_, f) => {
    try { return katex.renderToString(f.trim(), { displayMode: false, throwOnError: false }) }
    catch { return `<span class="formula-error">$${f}$</span>` }
  })
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\n/g, '<br />')
  return html
}
