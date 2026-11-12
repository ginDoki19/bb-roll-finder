/* language.js
 * The interface language: the current LANG, the lookup helper t(), and STR —
 * the full English/Bengali copy. This is the file to edit for wording.
 *
 * Both dictionaries must stay at parity; tools/selftest.py enforces that and
 * allows exactly one deliberate exception ("job", which is fixed English).
 */
/* ------------------------------------------------------------- language */
/* English is the default for a first-time visitor. Bengali is used only when
   the visitor has explicitly chosen it before — an existing saved preference
   is never silently discarded. */
let LANG = (() => {
  try { const v = localStorage.getItem("bb-lang"); if (v === "en" || v === "bn") return v; } catch(e){}
  return "en";
})();
/* Digits follow the interface language — Bengali UI gets ০-৯, English gets 0-9 */
const NUM = v => LANG === "bn" ? BN(v) : String(v);

/* A Job ID is a system identifier that the candidate cross-references against
   the official portal, so it is never translated and never converted to
   Bengali digits — "Job ID 307" reads the same in both languages. Roll numbers
   deliberately do NOT use this; they follow the interface language, because
   candidates read them off Bengali notices. */
const JOB = v => String(v ?? "—");

/* Missing Bengali copy falls back to English rather than showing a raw key. */
const t = k => (STR[LANG] && STR[LANG][k]) ?? STR.en[k] ?? k;

const STR = {
en:{
  tagline:"Bangladesh Bank notices · seat plans · results — in one place",
  placeholder:"Enter your roll number — e.g. 105432",
  /* Label for the search field. Visually hidden — the placeholder already
     says this on screen — but a placeholder is not an accessible name. */
  rollLabel:"Roll number",
  /* Spoken summaries for #srstatus. Deliberately short: the result cards
     themselves are reachable by browsing, so the live region only needs to
     report that the outcome changed and how many matches there are. */
  srFound:(n,r) => `${n} result${n>1?"s":""} for roll ${r}`,
  srAmbig:(n,r,j) => `${n} result${n>1?"s":""} for roll ${r} across ${j} jobs — choose a job`,
  hintBase:n => `Searching ${n} notices · seat plans, viva schedules and selected-candidate lists`,
  hintScanned:n => ` · ${n} scanned notice${n>1?"s":""} cannot be searched`,
  statNotices:"notices", statCentres:"centres", statRolls:"rolls",
  allNotices:"All notices", all:"All",
  lang:"Language", theme:"Theme", system:"System", light:"Light", dark:"Dark",
  examToday:"Exam today", daysLeft:d => `${d} day${+d===1?"":"s"} left`, upcoming:"Upcoming",
  completed:"Completed", ongoing:"Open",
  cdToday:"Your exam is today", cdTomorrow:"Your exam is tomorrow",
  cdDays:d => `Your exam is in ${d} days`, cdPast:d => `This took place ${d} days ago`,
  beThereBy:r => `Be at the centre by ${r}`,
  examDate:"Exam date", time:"Time", beThere:"Be there by", yourRoll:"Your roll",
  date:"Date", reportingTime:"Reporting time", batch:"Batch", post:"Post",
  centre:"Centre", rolls:"Rolls", seats:"Seats", seatRange:"Seat range",
  job:"Job ID", notice:"Notice", published:"Published", exam:"Exam", pages:n => `${n} page${n>1?"s":""}`,
  openMaps:"Open in Google Maps", showMap:"Show map here", hideMap:"Hide map",
  officialPdf:"Official PDF", openPdf:"Open official PDF", checkPortal:"Check the official portal",
  whatNext:"What happens next",
  yourCentre:"Your centre",
  yoursBadge:"YOUR POST",
  disambigQ:(r,n) => `Roll ${r} appears in ${n} different notices.`,
  disambigWhy:"Roll numbers restart with every circular, so the same number can belong to two unrelated jobs. Pick the post you applied for — we will remember it.",
  showAll:"Show all",
  congratsOffer:"Congratulations — your offer letter has been issued",
  congratsPrimary:"Congratulations — you are on the primarily selected list",
  congratsGeneric:"Your roll is on this list",
  selectedRef:"Your roll number",
  nextOffer:["Your offer letter has been issued — collect it and read the joining terms carefully.","Meet the joining deadline stated in the notice.","Keep your original certificates ready for verification."],
  nextPrimary:["This is a primary selection. The next step is document verification or the following phase of the process.","Watch the portal for the verification date and the document checklist.","Keep your originals and one set of photocopies ready."],
  nextSeat:["Bring your admit card and a photo ID.","Reach the centre at least one hour early.","Mobile phones, calculators, smart watches and bags are normally not allowed.","Read the official PDF for the full instructions."],
  nextViva:["Bring all original certificates and one set of photocopies.","Report at the time shown above — latecomers are usually not admitted.","Read the official PDF for the document checklist."],
  notFoundTitle:r => `Roll ${r} is not in the notices indexed here`,
  notFoundBody:n => `We checked all ${n} searchable notices. This usually means your notice has not been added yet — new notices appear on the official portal first, then here.`,
  notFoundList:"Currently indexed:",
  tooShort:r => `Keep typing — ${r} is too short to match anything.`,
  nRolls:n => `${n} roll numbers`,
  nRollsIn:(r,p) => `${r} roll numbers across ${p} post${p>1?"s":""}`,
  nCentres:(c,a,b) => `${c} centres · rolls ${a}–${b}`,
  nSittings:(s,r) => `${s} sittings · ${r} rolls`,
  filterList:"Filter this list…", copyAll:"Copy all", copied:"Copied", noMatchInList:"No roll in this list matches that.",
  showing:(a,b) => `showing ${a} of ${b}`,
  pastNotices:n => `${n} past notice${n>1?"s":""} — closed, still searchable`,
  ocrProv:(tot) => `<b>Read automatically from a scanned notice.</b> This PDF is an image. The numbers were read by OCR and published only because the count matched the total printed on the notice${tot?` (${tot})`:""} and several independent reads agreed. Mistakes are still possible — `,
  manualProv:"<b>Typed by hand from a scanned notice.</b> This PDF is an image, so the numbers were transcribed manually and checked against the total the notice states. Always confirm on the ",
  confirmPdf:"confirm on the official PDF",
  scannedWarn:"<b>This notice is a scanned image.</b> Its roll numbers cannot be read automatically, so searching will not find them here. ",
  openPdfCheck:"Open the official PDF and check it by eye.",
  fData:"Data:", fDataRest:"· parsed from the official BB/BSCS notice PDFs · not affiliated with Bangladesh Bank.",
  fConfirm:"Always confirm against the official PDF before travelling — this is a convenience layer, not an authority.",
  fStatic:"Static site · no server · no tracking · works offline.",
  updToday:"updated today", updYesterday:"updated yesterday",
  updDays:d => `updated ${d} days ago`, upd:"updated",
  builtFrom:(d,n) => `· built ${d} from ${n} notice PDFs`,
  multiPost:"Multiple posts in one notice"
},
bn:{
  tagline:"বাংলাদেশ ব্যাংকের নোটিশ, আসন বিন্যাস ও ফলাফল — সব এক জায়গায়",
  placeholder:"রোল নম্বর লিখুন, যেমন ১০৫৪৩২",
  rollLabel:"রোল নম্বর",
  srFound:(n,r) => `রোল ${r}-এর ${n}টি ফলাফল পাওয়া গেছে`,
  srAmbig:(n,r,j) => `রোল ${r}-এর ${n}টি ফলাফল ${j}টি আলাদা পদে মিলেছে — আপনার পদটি বেছে নিন`,
  hintBase:n => `${n}টি নোটিশে খোঁজা হচ্ছে — আসন বিন্যাস, মৌখিক পরীক্ষার সূচি ও নির্বাচিত প্রার্থীদের তালিকা`,
  hintScanned:n => ` · স্ক্যান করা ${n}টি নোটিশে খোঁজা যায় না`,
  statNotices:"নোটিশ", statCentres:"কেন্দ্র", statRolls:"রোল",
  allNotices:"সব নোটিশ", all:"সব",
  lang:"ভাষা", theme:"থিম", system:"অটো", light:"লাইট", dark:"ডার্ক",
  examToday:"আজ পরীক্ষা", daysLeft:d => `${d} দিন বাকি`, upcoming:"আসন্ন",
  completed:"শেষ হয়েছে", ongoing:"চলমান",
  cdToday:"আপনার পরীক্ষা আজ", cdTomorrow:"আপনার পরীক্ষা আগামীকাল",
  cdDays:d => `আপনার পরীক্ষা ${d} দিন পরে`, cdPast:d => `এই পরীক্ষা ${d} দিন আগে হয়ে গেছে`,
  beThereBy:r => `${r}-এর মধ্যে কেন্দ্রে পৌঁছান`,
  examDate:"পরীক্ষার তারিখ", time:"সময়", beThere:"কেন্দ্রে পৌঁছানোর সময়", yourRoll:"আপনার রোল",
  date:"তারিখ", reportingTime:"হাজির হওয়ার সময়", batch:"ব্যাচ", post:"পদ",
  centre:"কেন্দ্র", rolls:"রোল", seats:"আসন", seatRange:"আসনের পরিসর",
  /* no `job` key on purpose — "Job ID" is a fixed English label in every
     locale and falls through to the English dictionary. */
  notice:"বিজ্ঞপ্তি", published:"প্রকাশিত", exam:"পরীক্ষা", pages:n => `${n} পৃষ্ঠা`,
  openMaps:"গুগল ম্যাপে দেখুন", showMap:"মানচিত্র দেখুন", hideMap:"মানচিত্র বন্ধ করুন",
  officialPdf:"অফিসিয়াল পিডিএফ", openPdf:"অফিসিয়াল পিডিএফ খুলুন", checkPortal:"অফিসিয়াল পোর্টালে দেখুন",
  whatNext:"এরপর কী করবেন",
  yourCentre:"আপনার কেন্দ্র",
  yoursBadge:"আপনার পদ",
  disambigQ:(r,n) => `রোল ${r} ${n}টি আলাদা নোটিশে পাওয়া গেছে।`,
  disambigWhy:"প্রতিটি নতুন বিজ্ঞপ্তিতে রোল নম্বর নতুন করে শুরু হয়, তাই একই নম্বর আলাদা আলাদা পদে থাকতে পারে। যে পদে আবেদন করেছেন সেটি বেছে নিন — পছন্দটি মনে রাখা হবে।",
  showAll:"সব দেখান",
  congratsOffer:"অভিনন্দন! আপনার নিয়োগপত্র ইস্যু হয়েছে",
  congratsPrimary:"অভিনন্দন! আপনি প্রাথমিকভাবে নির্বাচিত হয়েছেন",
  congratsGeneric:"আপনার রোল এই তালিকায় আছে",
  selectedRef:"আপনার রোল নম্বর",
  nextOffer:["নিয়োগপত্র সংগ্রহ করে যোগদানের শর্তগুলো মন দিয়ে পড়ুন।","নোটিশে দেওয়া যোগদানের শেষ তারিখের মধ্যে যোগ দিন।","যাচাইয়ের জন্য মূল সনদগুলো গুছিয়ে রাখুন।"],
  nextPrimary:["এটি প্রাথমিক নির্বাচন। এরপর কাগজপত্র যাচাই বা নিয়োগ প্রক্রিয়ার পরের ধাপ থাকতে পারে।","যাচাইয়ের তারিখ ও কাগজপত্রের তালিকার জন্য পোর্টালে নজর রাখুন।","মূল কাগজপত্র আর এক সেট ফটোকপি তৈরি রাখুন।"],
  nextSeat:["প্রবেশপত্র আর ছবিসহ পরিচয়পত্র সঙ্গে নিন।","কমপক্ষে এক ঘণ্টা আগে কেন্দ্রে পৌঁছান।","মোবাইল ফোন, ক্যালকুলেটর, স্মার্টওয়াচ ও ব্যাগ সাধারণত ভেতরে নেওয়া যায় না।","পুরো নির্দেশনা অফিসিয়াল পিডিএফে দেখুন।"],
  nextViva:["সব মূল সনদ ও এক সেট ফটোকপি সঙ্গে নিন।","উপরের সময়ে হাজির থাকুন — দেরি করলে সাধারণত ঢুকতে দেওয়া হয় না।","কাগজপত্রের তালিকা অফিসিয়াল পিডিএফে দেখুন।"],
  notFoundTitle:r => `রোল ${r} এখানকার কোনো নোটিশে পাওয়া যায়নি`,
  notFoundBody:n => `এখানকার ${n}টি নোটিশেই খোঁজা হয়েছে। সম্ভবত আপনার নোটিশটি এখনো যোগ করা হয়নি — নতুন নোটিশ আগে অফিসিয়াল পোর্টালে আসে, তারপর এখানে।`,
  notFoundList:"এখানে এখন যেসব নোটিশ আছে:",
  tooShort:r => `লিখতে থাকুন — ${r} দিয়ে কিছু মিলবে না, আরও সংখ্যা দিন।`,
  nRolls:n => `${n}টি রোল নম্বর`,
  nRollsIn:(r,p) => `${p}টি পদে মোট ${r}টি রোল নম্বর`,
  nCentres:(c,a,b) => `${c}টি কেন্দ্র · রোল ${a}–${b}`,
  nSittings:(s,r) => `${s}টি ব্যাচ · ${r}টি রোল`,
  filterList:"এই তালিকায় খুঁজুন…", copyAll:"সব কপি করুন", copied:"কপি হয়েছে", noMatchInList:"এই তালিকায় এমন কোনো রোল নেই।",
  showing:(a,b) => `${b}টির মধ্যে ${a}টি দেখানো হচ্ছে`,
  pastNotices:n => `${n}টি পুরোনো নোটিশ — শেষ হলেও এখানে খোঁজা যায়`,
  ocrProv:(tot) => `<b>স্ক্যান করা নোটিশ থেকে কম্পিউটার দিয়ে পড়া।</b> এই পিডিএফটি আসলে একটি ছবি। নম্বরগুলো ওসিআর দিয়ে পড়া হয়েছে, আর নোটিশে ছাপা মোট সংখ্যার${tot?` (${tot})`:""} সঙ্গে মিললে এবং কয়েকবার আলাদাভাবে পড়েও একই ফল এলেই কেবল প্রকাশ করা হয়েছে। তবু ভুল থাকতে পারে — `,
  manualProv:"<b>স্ক্যান করা নোটিশ থেকে হাতে টাইপ করা।</b> এই পিডিএফটি আসলে একটি ছবি, তাই নম্বরগুলো হাতে টাইপ করে নোটিশে ছাপা মোট সংখ্যার সঙ্গে মিলিয়ে দেখা হয়েছে। তবু সবসময় ",
  confirmPdf:"অফিসিয়াল পিডিএফে মিলিয়ে নিন",
  scannedWarn:"<b>এই নোটিশটি স্ক্যান করা ছবি।</b> এর রোল নম্বর কম্পিউটার দিয়ে পড়া যায়নি, তাই এখানে খুঁজে পাওয়া যাবে না। ",
  openPdfCheck:"অফিসিয়াল পিডিএফ খুলে নিজে মিলিয়ে দেখুন।",
  fData:"তথ্য:", fDataRest:"· বাংলাদেশ ব্যাংক ও বিএসসিএসের অফিসিয়াল নোটিশের পিডিএফ থেকে নেওয়া · বাংলাদেশ ব্যাংকের সঙ্গে এই সাইটের কোনো সম্পর্ক নেই।",
  fConfirm:"রওনা দেওয়ার আগে অবশ্যই অফিসিয়াল পিডিএফে মিলিয়ে নিন — এটি শুধু সহায়ক একটি সাইট, অফিসিয়াল উৎস নয়।",
  fStatic:"কোনো সার্ভার নেই · কোনো ট্র্যাকিং নেই · ইন্টারনেট ছাড়াও চলে।",
  updToday:"আজ আপডেট হয়েছে", updYesterday:"গতকাল আপডেট হয়েছে",
  updDays:d => `${d} দিন আগে আপডেট হয়েছে`, upd:"আপডেট",
  builtFrom:(d,n) => `· ${d} তারিখে ${n}টি নোটিশের পিডিএফ থেকে তৈরি`,
  multiPost:"এক নোটিশে একাধিক পদ"
}};

const kindLabel = k => LANG === "bn" ? (KIND[k]||KIND.circular).labBn : (KIND[k]||KIND.circular).labEn;
