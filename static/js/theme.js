import {
  argbFromHex,
  themeFromSourceColor,
  applyTheme,
} from '@material/material-color-utilities';

export function applyM3Theme(sourceColor, isDark) {
  const theme = themeFromSourceColor(argbFromHex(sourceColor));
  applyTheme(theme, { target: document.body, dark: isDark });
    }
