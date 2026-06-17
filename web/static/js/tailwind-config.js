/* Lumina Precision —— 7 屏共用的 Tailwind 主题（与原型 design 系统一致）。
   用法：CDN <script> 之后引入本文件。 */
tailwind.config = {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "surface": "#f8f9fa", "surface-dim": "#d9dadb", "surface-bright": "#f8f9fa",
        "surface-container-lowest": "#ffffff", "surface-container-low": "#f3f4f5",
        "surface-container": "#edeeef", "surface-container-high": "#e7e8e9",
        "surface-container-highest": "#e1e3e4", "on-surface": "#191c1d",
        "on-surface-variant": "#5a413a", "inverse-surface": "#2e3132",
        "inverse-on-surface": "#f0f1f2", "outline": "#8e7069", "outline-variant": "#e3beb6",
        "surface-tint": "#b32a03", "primary": "#b32a03", "on-primary": "#ffffff",
        "primary-container": "#ff5f38", "on-primary-container": "#5c0f00",
        "inverse-primary": "#ffb4a2", "secondary": "#5c5f62", "on-secondary": "#ffffff",
        "secondary-container": "#dee0e4", "on-secondary-container": "#606366",
        "tertiary": "#585f66", "on-tertiary": "#ffffff", "tertiary-container": "#8e959d",
        "on-tertiary-container": "#272e34", "error": "#ba1a1a", "on-error": "#ffffff",
        "error-container": "#ffdad6", "on-error-container": "#93000a",
        "primary-fixed": "#ffdad2", "primary-fixed-dim": "#ffb4a2", "on-primary-fixed": "#3c0700",
        "on-primary-fixed-variant": "#8a1c00", "secondary-fixed": "#e1e2e6",
        "secondary-fixed-dim": "#c5c6ca", "on-secondary-fixed": "#191c1f",
        "on-secondary-fixed-variant": "#44474a", "tertiary-fixed": "#dce3ec",
        "tertiary-fixed-dim": "#c0c7cf", "on-tertiary-fixed": "#151c22",
        "on-tertiary-fixed-variant": "#41484e", "background": "#f8f9fa",
        "on-background": "#191c1d", "surface-variant": "#e1e3e4",
        "success": "#1f7a3d", "warning": "#b06a00"
      },
      borderRadius: { "DEFAULT": "0.25rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px" },
      spacing: { "gutter": "16px", "margin-desktop": "32px", "container-padding-xl": "32px",
                 "margin-mobile": "16px", "unit": "4px", "container-padding-lg": "24px" },
      fontFamily: { "label-caps": ["Inter"], "body-base": ["Inter"], "body-bold": ["Inter"],
                    "display-lg": ["Inter"], "headline-md": ["Inter"],
                    "display-lg-mobile": ["Inter"], "code-mono": ["JetBrains Mono"] },
      fontSize: {
        "label-caps": ["11px", { "lineHeight": "16px", "letterSpacing": "0.05em", "fontWeight": "700" }],
        "body-base": ["15px", { "lineHeight": "22px", "letterSpacing": "0", "fontWeight": "400" }],
        "body-bold": ["15px", { "lineHeight": "22px", "letterSpacing": "0", "fontWeight": "600" }],
        "display-lg": ["40px", { "lineHeight": "48px", "letterSpacing": "-0.02em", "fontWeight": "800" }],
        "headline-md": ["24px", { "lineHeight": "32px", "letterSpacing": "-0.01em", "fontWeight": "600" }],
        "display-lg-mobile": ["32px", { "lineHeight": "40px", "letterSpacing": "-0.02em", "fontWeight": "800" }],
        "code-mono": ["13px", { "lineHeight": "18px", "letterSpacing": "0", "fontWeight": "400" }]
      }
    }
  }
};