/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './src/**/*.{html,js,svelte,ts}',
    './node_modules/@tremor/**/*.{js,ts,jsx,tsx}', // Tremor content
  ],
  theme: {
    extend: {
      colors: {
        // Custom IBKR colors
        'ibkr': {
          'primary': '#0088cc',      // IBKR Blue
          'secondary': '#005a8b',    // Darker Blue
          'background': '#1a1a1a',   // Dark Background
          'surface': '#2a2a2a',      // Card/Surface Background
          'border': '#3a3a3a',       // Border Color
          'text': '#e0e0e0',         // Primary Text
          'text-secondary': '#a0a0a0', // Secondary Text
          'success': '#00b050',      // Green for profits
          'danger': '#dc3545',       // Red for losses
          'warning': '#ffc107',      // Yellow for warnings
          'info': '#17a2b8',         // Info blue
        },
        // Tremor colors
        tremor: {
          brand: {
            faint: '#0B1929',
            muted: '#172554',
            subtle: '#1e40af',
            DEFAULT: '#3b82f6',
            emphasis: '#60a5fa',
            inverted: '#ffffff',
          },
          background: {
            muted: '#131A2B',
            subtle: '#1A2332',
            DEFAULT: '#0B1929',
            emphasis: '#d1d5db',
          },
          border: {
            DEFAULT: '#1f2937',
          },
          ring: {
            DEFAULT: '#1f2937',
          },
          content: {
            subtle: '#4b5563',
            DEFAULT: '#6b7280',
            emphasis: '#e5e7eb',
            strong: '#f9fafb',
            inverted: '#000000',
          },
        },
      },
      fontFamily: {
        'mono': ['JetBrains Mono', 'Consolas', 'Monaco', 'monospace'],
        'sans': ['Inter', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      fontSize: {
        'xxs': '0.625rem',  // 10px - for tiny labels
        'xs': '0.75rem',    // 12px
        'sm': '0.875rem',   // 14px
        'base': '1rem',     // 16px
      },
      boxShadow: {
        'ibkr': '0 2px 4px rgba(0, 0, 0, 0.2)',
        'ibkr-hover': '0 4px 8px rgba(0, 0, 0, 0.3)',
        // Tremor shadows
        'tremor-input': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        'tremor-card': '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        'tremor-dropdown': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
      },
      borderRadius: {
        'tremor-small': '0.375rem',
        'tremor-default': '0.5rem',
        'tremor-full': '9999px',
      },
    },
  },
  plugins: [],
}