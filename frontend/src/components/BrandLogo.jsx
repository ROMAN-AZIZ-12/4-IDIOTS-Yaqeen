// A shield surrounds the verified path. The paired dots below the check
// reference the Urdu letter ی without reducing the mark to a font glyph.
const shieldAndCheck = "M24 4 39 10v12.6c0 9.9-6.3 17.2-15 21.4C15.3 39.8 9 32.5 9 22.6V10L24 4ZM14.3 22.5l3.1-3.1 4 4 10-10 3.3 3.3L21.4 30l-7.1-7.5ZM17.7 35.3a2 2 0 1 0 4 0 2 2 0 1 0-4 0ZM24 35.3a2 2 0 1 0 4 0 2 2 0 1 0-4 0Z";

export function BrandMark({ size = 40, monochrome = false, label }) {
  return <svg
    className="brand-mark"
    width={size}
    height={size}
    viewBox="0 0 48 48"
    role={label ? "img" : undefined}
    aria-label={label}
    aria-hidden={label ? undefined : true}
    focusable="false"
  >
    <path d={shieldAndCheck} fill="currentColor" fillRule="evenodd" />
    {!monochrome && <g fill="#94D9B2"><circle cx="19.7" cy="35.3" r="1.65" /><circle cx="26" cy="35.3" r="1.65" /></g>}
  </svg>;
}

export default function BrandLogo({ monochrome = false, className = "" }) {
  return <span className={`brand-logo${monochrome ? " is-monochrome" : ""}${className ? ` ${className}` : ""}`} role="img" aria-label="Yaqeen — یقین">
    <BrandMark monochrome={monochrome} />
    <span className="brand-word" dir="ltr"><span lang="en">Yaqeen</span><span className="brand-urdu" lang="ur" dir="rtl">یقین</span></span>
  </span>;
}
