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
  examToday:"Exam today", daysLeft:d => `${d} days left`, upcoming:"Upcoming",
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
  tagline:"বাংলাদেশ ব্যাংক নোটিশ · আসন বিন্যাস · ফলাফল — এক জায়গায়",
  placeholder:"আপনার রোল নম্বর লিখুন — যেমন ১০৫৪৩২",
  rollLabel:"রোল নম্বর",
  srFound:(n,r) => `রোল ${r} এর জন্য ${n}টি ফলাফল`,
  srAmbig:(n,r,j) => `রোল ${r} এর জন্য ${n}টি ফলাফল, ${j}টি জবে — একটি জব বেছে নিন`,
  hintBase:n => `${n}টি নোটিশে খোঁজা হচ্ছে · আসন বিন্যাস, মৌখিক পরীক্ষার সময়সূচি ও নির্বাচিত প্রার্থীর তালিকা`,
  hintScanned:n => ` · ${n}টি স্ক্যান করা নোটিশ খোঁজা যায় না`,
  statNotices:"নোটিশ", statCentres:"কেন্দ্র", statRolls:"রোল",
  allNotices:"সব নোটিশ", all:"সব",
  lang:"ভাষা", theme:"থিম", system:"সিস্টেম", light:"দিন", dark:"রাত",
  examToday:"আজ পরীক্ষা", daysLeft:d => `${d} দিন বাকি`, upcoming:"আসন্ন",
  completed:"সম্পন্ন", ongoing:"চলমান",
  cdToday:"আপনার পরীক্ষা আজ", cdTomorrow:"আপনার পরীক্ষা আগামীকাল",
  cdDays:d => `আপনার পরীক্ষা ${d} দিন পরে`, cdPast:d => `এটি ${d} দিন আগে হয়ে গেছে`,
  beThereBy:r => `কেন্দ্রে পৌঁছান ${r}-এর মধ্যে`,
  examDate:"পরীক্ষার তারিখ", time:"সময়", beThere:"পৌঁছাতে হবে", yourRoll:"আপনার রোল",
  date:"তারিখ", reportingTime:"রিপোর্টিং সময়", batch:"ব্যাচ", post:"পদ",
  centre:"কেন্দ্র", rolls:"রোল", seats:"আসন", seatRange:"আসন সীমা",
  /* no `job` key on purpose — "Job ID" is a fixed English label in every
     locale and falls through to the English dictionary. */
  notice:"বিজ্ঞপ্তি", published:"প্রকাশিত", exam:"পরীক্ষা", pages:n => `${n} পৃষ্ঠা`,
  openMaps:"গুগল ম্যাপসে খুলুন", showMap:"এখানে মানচিত্র দেখুন", hideMap:"মানচিত্র লুকান",
  officialPdf:"মূল পিডিএফ", openPdf:"মূল পিডিএফ খুলুন", checkPortal:"অফিসিয়াল পোর্টাল দেখুন",
  whatNext:"এরপর কী করবেন",
  yourCentre:"আপনার কেন্দ্র",
  yoursBadge:"আপনার পদ",
  disambigQ:(r,n) => `রোল ${r} ${n}টি আলাদা নোটিশে রয়েছে।`,
  disambigWhy:"প্রতিটি নতুন বিজ্ঞপ্তিতে রোল নম্বর আবার শুরু হয়, তাই একই নম্বর দুটি ভিন্ন পদের হতে পারে। আপনি যে পদে আবেদন করেছেন সেটি বেছে নিন — আমরা মনে রাখব।",
  showAll:"সব দেখান",
  congratsOffer:"অভিনন্দন! আপনার নিয়োগপত্র ইস্যু হয়েছে",
  congratsPrimary:"অভিনন্দন! আপনি প্রাথমিকভাবে নির্বাচিত হয়েছেন",
  congratsGeneric:"আপনার রোল এই তালিকায় রয়েছে",
  selectedRef:"আপনার রোল নম্বর",
  nextOffer:["আপনার নিয়োগপত্র ইস্যু হয়েছে — সংগ্রহ করে যোগদানের শর্তগুলো ভালোভাবে পড়ুন।","নোটিশে উল্লিখিত যোগদানের সময়সীমা মেনে চলুন।","যাচাইয়ের জন্য মূল সনদপত্রগুলো প্রস্তুত রাখুন।"],
  nextPrimary:["এটি প্রাথমিক নির্বাচন। পরবর্তী ধাপ কাগজপত্র যাচাই অথবা নিয়োগ প্রক্রিয়ার পরের পর্ব।","যাচাইয়ের তারিখ ও কাগজপত্রের তালিকার জন্য পোর্টালে নজর রাখুন।","মূল কাগজপত্র ও এক সেট ফটোকপি প্রস্তুত রাখুন।"],
  nextSeat:["প্রবেশপত্র ও ছবিযুক্ত পরিচয়পত্র সঙ্গে আনুন।","অন্তত এক ঘণ্টা আগে কেন্দ্রে পৌঁছান।","মোবাইল ফোন, ক্যালকুলেটর, স্মার্টওয়াচ ও ব্যাগ সাধারণত নিষিদ্ধ।","বিস্তারিত নির্দেশনার জন্য মূল পিডিএফ পড়ুন।"],
  nextViva:["সব মূল সনদপত্র ও এক সেট ফটোকপি সঙ্গে আনুন।","উপরে উল্লিখিত সময়ে উপস্থিত হন — দেরি করলে সাধারণত প্রবেশ করতে দেওয়া হয় না।","কাগজপত্রের তালিকার জন্য মূল পিডিএফ পড়ুন।"],
  notFoundTitle:r => `রোল ${r} এখানে সূচিভুক্ত নোটিশগুলোতে নেই`,
  notFoundBody:n => `আমরা ${n}টি খোঁজযোগ্য নোটিশ দেখেছি। সাধারণত এর অর্থ আপনার নোটিশটি এখনো যুক্ত হয়নি — নতুন নোটিশ আগে অফিসিয়াল পোর্টালে আসে, তারপর এখানে।`,
  notFoundList:"এখন যা সূচিভুক্ত:",
  tooShort:r => `আরও লিখুন — ${r} মেলানোর জন্য খুব ছোট।`,
  nRolls:n => `${n}টি রোল নম্বর`,
  nRollsIn:(r,p) => `${p}টি পদে মোট ${r}টি রোল নম্বর`,
  nCentres:(c,a,b) => `${c}টি কেন্দ্র · রোল ${a}–${b}`,
  nSittings:(s,r) => `${s}টি ব্যাচ · ${r}টি রোল`,
  filterList:"এই তালিকায় খুঁজুন…", copyAll:"সব কপি করুন", copied:"কপি হয়েছে", noMatchInList:"এই তালিকায় সেরকম কোনো রোল নেই।",
  showing:(a,b) => `${b}টির মধ্যে ${a}টি দেখানো হচ্ছে`,
  pastNotices:n => `${n}টি পুরোনো নোটিশ — শেষ হয়েছে, তবু খোঁজা যায়`,
  ocrProv:(tot) => `<b>স্ক্যান করা নোটিশ থেকে স্বয়ংক্রিয়ভাবে পড়া।</b> এই পিডিএফটি একটি ছবি। নম্বরগুলো ওসিআর দিয়ে পড়া হয়েছে এবং শুধু তখনই প্রকাশ করা হয়েছে যখন সংখ্যা নোটিশে ছাপা মোটের সঙ্গে মিলেছে${tot?` (${tot})`:""} এবং একাধিক স্বাধীন পাঠ একমত হয়েছে। তবুও ভুল হতে পারে — `,
  manualProv:"<b>স্ক্যান করা নোটিশ থেকে হাতে টাইপ করা।</b> এই পিডিএফটি একটি ছবি, তাই নম্বরগুলো হাতে লেখা হয়েছে এবং নোটিশে ছাপা মোটের সঙ্গে মিলিয়ে দেখা হয়েছে। সবসময় ",
  confirmPdf:"মূল পিডিএফে মিলিয়ে নিন",
  scannedWarn:"<b>এই নোটিশটি একটি স্ক্যান করা ছবি।</b> এর রোল নম্বর স্বয়ংক্রিয়ভাবে পড়া যায় না, তাই খুঁজলে এখানে পাওয়া যাবে না। ",
  openPdfCheck:"মূল পিডিএফ খুলে নিজে দেখে নিন।",
  fData:"তথ্য:", fDataRest:"· অফিসিয়াল বিবি/বিএসসিএস নোটিশ পিডিএফ থেকে সংগৃহীত · বাংলাদেশ ব্যাংকের সঙ্গে সম্পৃক্ত নয়।",
  fConfirm:"রওনা হওয়ার আগে সবসময় মূল পিডিএফে মিলিয়ে নিন — এটি একটি সহায়ক মাধ্যম, কর্তৃপক্ষ নয়।",
  fStatic:"স্ট্যাটিক সাইট · কোনো সার্ভার নেই · কোনো ট্র্যাকিং নেই · অফলাইনেও চলে।",
  updToday:"আজ হালনাগাদ", updYesterday:"গতকাল হালনাগাদ",
  updDays:d => `${d} দিন আগে হালনাগাদ`, upd:"হালনাগাদ",
  builtFrom:(d,n) => `· ${n}টি নোটিশ পিডিএফ থেকে ${d} তারিখে তৈরি`,
  multiPost:"এক নোটিশে একাধিক পদ"
}};

const kindLabel = k => LANG === "bn" ? (KIND[k]||KIND.circular).labBn : (KIND[k]||KIND.circular).labEn;
