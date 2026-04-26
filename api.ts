
// URL бэкенда — Railway задеплоишь отдельным сервисом
// После деплоя бэкенда замени на реальный URL
const BASE = import.meta.env.VITE_BACKEND_URL || "https://YOUR-BACKEND.up.railway.app";
async function req<T>(path: string, body: object): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Ошибка сервера");
  return data as T;
}
export const api = {
  sendCode: (phone: string) =>
    req<{ ok: boolean; message: string }>("/send-code", { phone }),
  verifyCode: (phone: string, code: string) =>
    req<{ ok: boolean; need_password: boolean }>("/verify-code", { phone, code }),
  verifyPassword: (phone: string, password: string) =>
    req<{ ok: boolean }>("/verify-password", { phone, password }),
};
