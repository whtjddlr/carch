import { IS_DEMO_CHANNEL } from '@/services/channel'

export const CARD_IMAGES_ENABLED = IS_DEMO_CHANNEL

export const cardImageUrl = (value = '') => (CARD_IMAGES_ENABLED ? String(value || '') : '')

export const withoutServiceCardImages = (item = {}) => {
  if (CARD_IMAGES_ENABLED || !item || typeof item !== 'object') return item
  return {
    ...item,
    ...(Object.prototype.hasOwnProperty.call(item, 'imageUrl') ? { imageUrl: '' } : {}),
    ...(Object.prototype.hasOwnProperty.call(item, 'image_url') ? { image_url: '' } : {}),
    ...(Object.prototype.hasOwnProperty.call(item, 'toImageUrl') ? { toImageUrl: '' } : {}),
    ...(Object.prototype.hasOwnProperty.call(item, 'to_image_url') ? { to_image_url: '' } : {}),
    ...(Object.prototype.hasOwnProperty.call(item, 'cardImage') ? { cardImage: '' } : {}),
    ...(Object.prototype.hasOwnProperty.call(item, 'card_image') ? { card_image: '' } : {}),
    ...(Object.prototype.hasOwnProperty.call(item, 'image') ? { image: '' } : {}),
  }
}
