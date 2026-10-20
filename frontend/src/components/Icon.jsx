const paths = {
  arrow: "M4 12h16M14 6l6 6-6 6",
  back: "M20 12H4m6-6-6 6 6 6",
  check: "m5 12 4 4L19 6",
  document: "M14 3H5v18h14V8l-5-5Zm0 0v5h5M8 12h8M8 16h6",
  identity: "M3 5h18v14H3zM7 9h3v3H7zM6 15h5M14 9h4m-4 4h4",
  bank: "m3 8 9-5 9 5H3Zm2 3v7m5-7v7m4-7v7m5-7v7M3 21h18",
  business: "M4 9h16v12H4zM3 9l2-6h14l2 6M9 21v-7h6v7",
  upload: "M12 16V3m-5 5 5-5 5 5M4 15v6h16v-6",
  clock: "M12 8v5l3 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0",
  shield: "m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3Zm-4 9 3 3 5-6",
  alert: "m12 3 10 18H2L12 3Zm0 6v5m0 3v1",
  close: "m6 6 12 12M18 6 6 18",
  globe: "M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0M3 12h18M12 3c5 5 5 13 0 18-5-5-5-13 0-18",
  logout: "M9 4H4v16h5m0-8h12m-5-5 5 5-5 5",
  plus: "M12 4v16M4 12h16",
  review: "M9 3H4v18h16v-7M9 7h4m-4 5h3m3-5 3 3 4-6",
};
export default function Icon({ name = "document", size = 20, className = "" }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false" className={className}><path d={paths[name] || paths.document} /></svg>;
}
