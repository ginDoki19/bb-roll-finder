/* language.js
 * The interface language: the current LANG, the lookup helper t(), and STR —
 * the full English/Bengali copy. This is the file to edit for wording.
 *
 * Both dictionaries must stay at parity; tools/selftest.py enforces that and
 * allows exactly one deliberate exception ("job", which is fixed English).
 */
/* ------------------------------------------------------------- language */
/* Resolution order, strongest first:
     1. an explicit saved choice — never silently discarded;
     2. the browser's own language list, in the user's priority order, so a
        bn-BD phone opens in Bengali instead of making every visitor find the
        toggle. Most candidates reading these notices are Bengali-first;
     3. English.
   Only step 2 is new. A visitor who has ever touched the toggle keeps what
   they picked, in either direction. */
let LANG = (() => {
  try { const v = localStorage.getItem("bb-lang"); if (v === "en" || v === "bn") return v; } catch(e){}
  try {
    const list = (navigator.languages && navigator.languages.length)
      ? navigator.languages : [navigator.language];
    for (const raw of list){
      const tag = String(raw || "").toLowerCase();
      if (tag === "bn" || tag.indexOf("bn-") === 0) return "bn";
      if (tag === "en" || tag.indexOf("en-") === 0) return "en";
    }
  } catch(e){}
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

/* One notice can cover several job IDs at once: 20261029_bb_372 carries
   "280, 282, 289, 294, 295, 296, 299, 300". Printed whole it overflows a badge
   and buries the one number the candidate is looking for, so the badge shows
   the first plus a count and the full list moves to the tooltip. */
const JOB_LIST  = v => String(v ?? "").split(",").map(s => s.trim()).filter(Boolean);
const JOB_LABEL = v => { const p = JOB_LIST(v); return p.length > 1 ? `${p[0]} + ${p.length - 1}` : JOB(v); };
const jobAttr   = v => { const p = JOB_LIST(v);
  return p.length > 1 ? ` title="${esc(t("job"))} ${esc(p.join(", "))}"` : ""; };

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
  statNotices:"notices", statCentres:"centres", statRolls:"listed rolls",
  allNotices:"All notices", all:"All",
  lang:"Language", theme:"Theme", system:"Auto", light:"Light", dark:"Dark",
  examToday:"Exam today", daysLeft:d => `${d} day${+d===1?"":"s"} left`, upcoming:"Upcoming",
  completed:"Completed", ongoing:"Open",
  cdToday:"Your exam is today", cdTomorrow:"Your exam is tomorrow",
  cdDays:d => `Your exam is in ${d} days`, cdPast:d => `This took place ${d} days ago`,
  beThereBy:r => `Be at the centre by ${r}`,
  examDate:"Exam date", time:"Time", beThere:"Be there by", yourRoll:"Your roll",
  date:"Date", reportingTime:"Reporting time", yourSitting:"Your sitting",
  batch:"Batch", post:"Post",
  centre:"Centre", rolls:"Rolls", seats:"Seats", seatRange:"Seat range",
  stop:".",
  job:"Job ID", notice:"Notice", published:"Published", exam:"Exam", pages:n => `${n} page${n>1?"s":""}`,
  openMaps:"Open in Google Maps", showMap:"Show map here", hideMap:"Hide map",
  mapOffline:"The map needs an internet connection. Use the button above to open it in Google Maps.",
  officialPdf:"Official PDF", openPdf:"Open official PDF", checkPortal:"Check the official portal",
  share:"Share", shared:"Link copied",
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
  /* Shown only for a roll the OCR itself flagged as uncertain. This is the
     one place the site can actively mislead somebody into travelling, so it
     says plainly that the number may not be theirs. */
  lowConfTitle:"This roll number was hard to read",
  lowConfBody:"The scan is unclear at this number and repeated reads of it did not agree, so it may actually be a different roll. Before you rely on it, ",
  nextOffer:["Your offer letter has been issued — collect it and read the joining terms carefully.","Meet the joining deadline stated in the notice.","Keep your original certificates ready for verification."],
  nextPrimary:["This is a primary selection. The next step is document verification or the following phase of the process.","Watch the portal for the verification date and the document checklist.","Keep your originals and one set of photocopies ready."],
  nextSeat:["Bring your admit card and a photo ID.","Reach the centre at least one hour early.","Mobile phones, calculators, smart watches and bags are normally not allowed.","Read the official PDF for the full instructions."],
  nextViva:["Bring all original certificates and one set of photocopies.","Report at the time shown above — latecomers are usually not admitted.","Read the official PDF for the document checklist."],
  notFoundTitle:r => `Roll ${r} is not in the notices indexed here`,
  notFoundBody:n => `We checked all ${n} searchable notices. This usually means your notice has not been added yet — new notices appear on the official portal first, then here.`,
  notFoundList:"Currently indexed:",
  tooShort:r => `${r} is too short to be a roll number — enter the whole number.`,
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
  /* Bengali attaches the count to the thing counted, not to a possessive on
     the roll: "রোল ২০০৯৮৩ — ২টি ফলাফল", never "রোল ২০০৯৮৩-এর ২টি ফলাফল". */
  srFound:(n,r) => `রোল ${r} — ${n}টি ফলাফল পাওয়া গেছে`,
  srAmbig:(n,r,j) => `রোল ${r} — ${j}টি আলাদা পদে ${n}টি ফলাফল পাওয়া গেছে, আপনার পদটি বেছে নিন`,
  hintBase:n => `${n}টি নোটিশে খোঁজা হচ্ছে — আসন বিন্যাস, ভাইভার সূচি ও নির্বাচিত প্রার্থীদের তালিকা`,
  hintScanned:n => ` · স্ক্যান করা ${n}টি নোটিশে খোঁজা যায় না`,
  statNotices:"নোটিশ", statCentres:"কেন্দ্র", statRolls:"তালিকাভুক্ত রোল",
  allNotices:"সব নোটিশ", all:"সব",
  lang:"ভাষা", theme:"থিম", system:"অটো", light:"লাইট", dark:"ডার্ক",
  /* Status badges are noun phrases — আসন্ন, চলমান — so the finished state is
     সম্পন্ন, not the finite verb "শেষ হয়েছে". */
  examToday:"আজ পরীক্ষা", daysLeft:d => `${d} দিন বাকি`, upcoming:"আসন্ন",
  completed:"সম্পন্ন", ongoing:"চলমান",
  /* Bengali puts the time adverb first: আজ আপনার পরীক্ষা, not আপনার পরীক্ষা আজ. */
  cdToday:"আজ আপনার পরীক্ষা", cdTomorrow:"আগামীকাল আপনার পরীক্ষা",
  cdDays:d => `আর ${d} দিন পর আপনার পরীক্ষা`, cdPast:d => `${d} দিন আগে এই পরীক্ষা হয়ে গেছে`,
  beThereBy:r => `${r}-এর মধ্যে কেন্দ্রে পৌঁছান`,
  examDate:"পরীক্ষার তারিখ", time:"সময়", beThere:"কেন্দ্রে পৌঁছানোর সময়", yourRoll:"আপনার রোল",
  date:"তারিখ", reportingTime:"হাজির হওয়ার সময়", yourSitting:"আপনার সময়সূচি",
  batch:"ব্যাচ", post:"পদ",
  centre:"কেন্দ্র", rolls:"রোল", seats:"আসন", seatRange:"আসনের পরিসর",
  /* no `job` key on purpose — "Job ID" is a fixed English label in every
     locale and falls through to the English dictionary. */
  stop:"।",
  notice:"বিজ্ঞপ্তি", published:"প্রকাশিত", exam:"পরীক্ষা", pages:n => `${n} পৃষ্ঠা`,
  openMaps:"গুগল ম্যাপে দেখুন", showMap:"মানচিত্র দেখুন", hideMap:"মানচিত্র লুকান",
  mapOffline:"মানচিত্র দেখতে ইন্টারনেট সংযোগ লাগবে। উপরের বোতাম থেকে গুগল ম্যাপে খুলুন।",
  officialPdf:"অফিসিয়াল পিডিএফ", openPdf:"অফিসিয়াল পিডিএফ খুলুন", checkPortal:"অফিসিয়াল পোর্টালে দেখুন",
  share:"শেয়ার করুন", shared:"লিংক কপি হয়েছে",
  whatNext:"এরপর কী করবেন",
  yourCentre:"আপনার কেন্দ্র",
  yoursBadge:"আপনার পদ",
  disambigQ:(r,n) => `রোল ${r} ${n}টি আলাদা নোটিশে পাওয়া গেছে।`,
  disambigWhy:"প্রতিটি বিজ্ঞপ্তিতে রোল নম্বর আবার শুরু থেকে দেওয়া হয়, তাই একই নম্বর দুটি আলাদা পদের হতে পারে। আপনি যে পদে আবেদন করেছেন সেটি বেছে নিন — পছন্দটি মনে রাখা হবে।",
  showAll:"সব দেখান",
  congratsOffer:"অভিনন্দন! আপনার নিয়োগপত্র প্রদান করা হয়েছে",
  congratsPrimary:"অভিনন্দন! আপনি প্রাথমিকভাবে নির্বাচিত হয়েছেন",
  congratsGeneric:"এই তালিকায় আপনার রোল রয়েছে",
  selectedRef:"আপনার রোল নম্বর",
  lowConfTitle:"এই রোল নম্বরটি স্পষ্ট পড়া যায়নি",
  lowConfBody:"স্ক্যান করা ছবিতে এই নম্বরটি ঝাপসা ছিল, কয়েকবার পড়েও একই ফল আসেনি। এটি আসলে অন্য কোনো রোল নম্বরও হতে পারে। নির্ভর করার আগে ",
  nextOffer:["নিয়োগপত্র সংগ্রহ করে যোগদানের শর্তগুলো মন দিয়ে পড়ুন।","নোটিশে দেওয়া যোগদানের শেষ তারিখের মধ্যে যোগ দিন।","যাচাইয়ের জন্য মূল সনদগুলো গুছিয়ে রাখুন।"],
  nextPrimary:["এটি প্রাথমিক নির্বাচন। এরপর কাগজপত্র যাচাই বা নিয়োগ প্রক্রিয়ার পরবর্তী ধাপ রয়েছে।","যাচাইয়ের তারিখ ও কাগজপত্রের তালিকার জন্য পোর্টালে নজর রাখুন।","মূল কাগজপত্র আর এক সেট ফটোকপি তৈরি রাখুন।"],
  nextSeat:["প্রবেশপত্র আর ছবিসহ পরিচয়পত্র সঙ্গে নিন।","কমপক্ষে এক ঘণ্টা আগে কেন্দ্রে পৌঁছান।","মোবাইল ফোন, ক্যালকুলেটর, স্মার্টওয়াচ ও ব্যাগ সাধারণত ভেতরে নেওয়া যায় না।","বিস্তারিত নির্দেশনা অফিসিয়াল পিডিএফে দেখুন।"],
  nextViva:["সব মূল সনদ ও এক সেট ফটোকপি সঙ্গে নিন।","উপরে দেওয়া সময়ে হাজির থাকুন — দেরি করলে সাধারণত ঢুকতে দেওয়া হয় না।","কাগজপত্রের তালিকা অফিসিয়াল পিডিএফে দেখুন।"],
  notFoundTitle:r => `এই সাইটের কোনো নোটিশে রোল ${r} পাওয়া যায়নি`,
  notFoundBody:n => `এই সাইটে থাকা ${n}টি নোটিশেই খোঁজা হয়েছে। সম্ভবত আপনার নোটিশটি এখনো যোগ করা হয়নি — নতুন নোটিশ আগে অফিসিয়াল পোর্টালে আসে, তারপর এখানে।`,
  notFoundList:"এই সাইটে এখন যেসব নোটিশ আছে:",
  tooShort:r => `${r} রোল নম্বর হিসেবে খুব ছোট — পুরো নম্বরটি লিখুন।`,
  nRolls:n => `${n}টি রোল নম্বর`,
  nRollsIn:(r,p) => `${p}টি পদে মোট ${r}টি রোল নম্বর`,
  nCentres:(c,a,b) => `${c}টি কেন্দ্র · রোল ${a}–${b}`,
  nSittings:(s,r) => `${s}টি ব্যাচ · ${r}টি রোল`,
  filterList:"এই তালিকায় খুঁজুন…", copyAll:"সব কপি করুন", copied:"কপি হয়েছে", noMatchInList:"এই তালিকায় এমন কোনো রোল নেই।",
  showing:(a,b) => `${b}টির মধ্যে ${a}টি দেখানো হচ্ছে`,
  pastNotices:n => `${n}টি পুরোনো নোটিশ — শেষ হয়ে গেছে, তবে এখানে খোঁজা যায়`,
  /* "কম্পিউটার দিয়ে পড়া" is a calque that reads as a description of a
     machine rather than of the data; স্বয়ংক্রিয়ভাবে is the word a Bengali
     notice would use. The run-on is split into three short sentences. */
  ocrProv:(tot) => `<b>স্ক্যান করা নোটিশ থেকে স্বয়ংক্রিয়ভাবে পড়া।</b> এই পিডিএফটি একটি ছবি, তাই নম্বরগুলো ওসিআর দিয়ে পড়া হয়েছে। নোটিশে ছাপা মোট সংখ্যার${tot?` (${tot})`:""} সঙ্গে মিলেছে এবং কয়েকবার আলাদাভাবে পড়েও একই ফল এসেছে, তাই প্রকাশ করা হয়েছে। তবুও ভুল থাকতে পারে — `,
  manualProv:"<b>স্ক্যান করা নোটিশ থেকে হাতে টাইপ করা।</b> এই পিডিএফটি একটি ছবি। নম্বরগুলো হাতে টাইপ করে নোটিশে ছাপা মোট সংখ্যার সঙ্গে মিলিয়ে দেখা হয়েছে। তবুও সবসময় ",
  confirmPdf:"অফিসিয়াল পিডিএফে মিলিয়ে নিন",
  scannedWarn:"<b>এই নোটিশটি স্ক্যান করা ছবি।</b> এর রোল নম্বর স্বয়ংক্রিয়ভাবে পড়া যায়নি, তাই এখানে খুঁজে পাওয়া যাবে না। ",
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
