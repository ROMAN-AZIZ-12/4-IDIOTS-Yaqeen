import { useEffect, useState } from "react";
import { dictionary } from "./translations";
import { LanguageContext } from "./locale";

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(() => {
    try { return localStorage.getItem("yaqeen-language") === "ur" ? "ur" : "en"; }
    catch { return "en"; }
  });
  useEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dir = language === "ur" ? "rtl" : "ltr";
    try { localStorage.setItem("yaqeen-language", language); } catch { /* Storage may be disabled. */ }
  }, [language]);
  function t(text, values = {}) {
    const translated = language === "ur" ? dictionary[text] || text : text;
    return Object.entries(values).reduce((result, [key, value]) => result.replaceAll(`{${key}}`, String(value)), translated);
  }
  function message(text) {
    if (!text) return "";
    if (dictionary[text]) return t(text);
    const httpError = text.match(/^(\d{3}) error$/);
    if (httpError) return t("Request failed ({status}). Please try again.", { status: httpError[1] });
    // Only translate known validation messages; never rewrite user content.
    const validation = {
      "Field required": "This field is required.",
      "String should have at least 1 character": "This field is required.",
      "String should have at least 8 characters": "Use at least 8 characters.",
      "String should have at least 6 characters": "Enter a 6-digit code.",
      "String should have at most 6 characters": "Enter a 6-digit code.",
      "Input should be greater than 0": "Enter an amount greater than zero.",
      "Decimal input should have no more than 2 decimal places": "Use no more than two decimal places.",
      "value is not a valid email address: The part after the @-sign is a special-use or reserved name that cannot be used with email.": "Enter a valid email address.",
      "Failed to fetch": "Could not connect. Please try again.",
      "NetworkError when attempting to fetch resource.": "Could not connect. Please try again.",
    };
    if (validation[text]) return t(validation[text]);
    return text.split("; ").map((part) => {
      const match = part.match(/^(email|password|full_name|code|amount_pkr|purpose|business_type|bank_id): (.*)$/);
      if (!match) return validation[part] ? t(validation[part]) : part;
      const label = { email: "Email address", password: "Password", full_name: "Full name", code: "Verification code", amount_pkr: "Amount (PKR)", purpose: "Purpose", business_type: "Business type", bank_id: "Bank" }[match[1]];
      const knownMessage = match[1] === "email" && match[2].startsWith("value is not a valid email address:") ? "Enter a valid email address." : validation[match[2]] || match[2];
      return `${t(label)}: ${t(knownMessage)}`;
    }).join("; ");
  }
  return <LanguageContext.Provider value={{ language, setLanguage, t, message }}>{children}</LanguageContext.Provider>;
}


