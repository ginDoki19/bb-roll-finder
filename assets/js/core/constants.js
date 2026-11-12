/* constants.js
 * Inert lookup data shared across features: the notice-kind taxonomy and the
 * post-name regex. No behaviour lives here.
 *
 * KIND carries the two badge labels (labEn/labBn) because they are part of the
 * taxonomy rather than prose; all other translatable copy is in
 * core/language.js under STR.
 */
const KIND = {
  seat:     { key:"seat",     cls:"b-seat",     en:"Centre & seat allocation",     labEn:"SEAT PLAN", labBn:"আসন বিন্যাস" },
  viva:     { key:"viva",     cls:"b-viva",     en:"Viva / interview schedule",    labEn:"VIVA",      labBn:"ভাইভা" },
  result:   { key:"result",   cls:"b-result",   en:"Written result",               labEn:"RESULT",    labBn:"ফলাফল" },
  selected: { key:"selected", cls:"b-selected", en:"Primarily selected list",      labEn:"SELECTED",  labBn:"নির্বাচিত" },
  circular: { key:"circular", cls:"b-circular", en:"Schedule / circular",          labEn:"CIRCULAR",  labBn:"বিজ্ঞপ্তি" },
  scanned:  { key:"scanned",  cls:"b-scanned",  en:"Scanned image — not searchable",labEn:"SCANNED",  labBn:"স্ক্যান করা" }
};
/* ------------------------------------------------------------- identity
   A roll number is only unique inside a job, so the job is what every card
   leads with. The post name is what the candidate actually remembers
   applying for, so it is the headline and the job ID is the hard key. */
const POST_RE = /\bposts?\s+of\s*["'\u201c\u2018]?\s*(.+?)\s*["'\u201d\u2019]?\s*(?:\s+(?:of|in)\s+(?:SPCBL|Bangladesh\s+Bank|\d+\s+Banks?)\b|\s*\((?:Job|Grade)|\s*,|\s*$)/i;
