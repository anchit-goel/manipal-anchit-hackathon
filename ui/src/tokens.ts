/**
 * Design Tokens for Signal-to-Shock Institutional Risk Analytics Interface
 * Professional, calm, dense but legible financial data product.
 */

export const tokens = {
  colors: {
    // Surface & Layout
    bg: '#F5F6F8',
    card: '#FFFFFF',
    cardSubtle: '#F9FAFB',
    cardSelected: '#F0F5FD',
    border: '#E3E6EB',
    borderSubtle: '#EEF0F3',
    borderStrong: '#D0D5DD',

    // Typography
    textPrimary: '#0F1B2D',
    textSecondary: '#5B6676',
    textMuted: '#8A94A6',
    textInverse: '#FFFFFF',

    // Brand Accent
    brand: '#1F4E9C',
    brandHover: '#163A75',
    brandLight: '#EDF3FC',
    brandBorder: '#B2CCF2',

    // Semantic Intent
    loss: {
      text: '#B42318',
      bg: '#FEF3F2',
      border: '#FECDCA',
    },
    gain: {
      text: '#067647',
      bg: '#EDFDF5',
      border: '#A6F4C5',
    },
    caution: {
      text: '#B54708',
      bg: '#FFFAEB',
      border: '#FEDF89',
    },
    neutral: {
      text: '#475467',
      bg: '#F2F4F7',
      border: '#EAECF0',
    },
  },
  typography: {
    fontSans: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    fontMono: "'IBM Plex Mono', ui-monospace, SFMono-Regular, monospace",
  },
  radius: {
    sm: '4px',
    md: '6px',
    lg: '8px',
  },
  shadow: {
    overlay: '0 4px 12px rgba(15, 27, 45, 0.08)',
    dropdown: '0 8px 24px rgba(15, 27, 45, 0.12)',
  },
} as const

export type Tokens = typeof tokens
