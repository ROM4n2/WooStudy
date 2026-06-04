/** 前端图片压缩——上传前压缩到 1920px 宽以内，减少 API 传输量 */

const MAX_WIDTH = 1920
const QUALITY = 0.8

/**
 * 压缩图片文件
 * @param {File} file - 原始图片文件
 * @returns {Promise<Blob>} 压缩后的 Blob
 */
export function compressImage(file) {
  return new Promise((resolve, reject) => {
    // 如果图片小于 1MB，直接返回不压缩
    if (file.size < 1024 * 1024) {
      resolve(file)
      return
    }

    const img = new Image()
    img.onload = () => {
      // 计算缩放比例
      let { width, height } = img
      if (width > MAX_WIDTH) {
        const ratio = MAX_WIDTH / width
        width = MAX_WIDTH
        height = height * ratio
      }

      // 用 Canvas 重绘
      const canvas = document.createElement('canvas')
      canvas.width = width
      canvas.height = height
      const ctx = canvas.getContext('2d')
      ctx.drawImage(img, 0, 0, width, height)

      // 输出为 Blob
      canvas.toBlob(
        (blob) => {
          if (blob) resolve(blob)
          else reject(new Error('压缩失败'))
        },
        'image/jpeg',
        QUALITY,
      )
    }
    img.onerror = () => reject(new Error('图片加载失败'))

    // 读取文件
    const reader = new FileReader()
    reader.onload = (e) => { img.src = e.target.result }
    reader.onerror = () => reject(new Error('文件读取失败'))
    reader.readAsDataURL(file)
  })
}
