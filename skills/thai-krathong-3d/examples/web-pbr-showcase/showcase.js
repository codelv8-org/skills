"use strict";
// Embedded data keeps the example functional when opened from a local file.
const cases = [
  {
    "id": "banana",
    "family": "banana_classic",
    "title": "กระทงใบตอง",
    "subtitle": "ทรงกลม · ใบตองพับ · ฐานหยวกกล้วย",
    "prompt": "ใช้ $thai-krathong-3d สร้างกระทงใบตองทรงกลมตาม preset banana_classic มีชั้นใบตองพับ ดอกไม้ เทียนและธูป ใช้สีเขียวธรรมชาติ เก็บลายเส้นใบตองให้ถูกทิศ ส่งออก GLB สำหรับเว็บ พร้อม Mesh/UV QA, baked PBR และภาพตรวจด้านหน้า ด้านบน และมุมเฉียง",
    "preset": "ref-banana-classic.json",
    "triangles": 9256,
    "islands": 1586,
    "resolution": 1024,
    "bytes": 5540352,
    "sha256": "b42d5218ddd5132766a1002efdf34ab8dd759f0779cba692996718717aa2414d"
  },
  {
    "id": "lotus",
    "family": "white_lotus",
    "title": "กระทงดอกบัว",
    "subtitle": "กลีบโค้ง · สีขาวนวล · ซ้อนหลายวง",
    "prompt": "ใช้ $thai-krathong-3d สร้างกระทงทรงดอกบัวสีขาวนวลตาม preset white_lotus กลีบกว้างมีความหนาและแอ่งโค้ง แยกชั้นกลีบชัดเจน ตรวจ silhouette และ UV overlap ก่อน bake Normal และ ORM ส่งออก GLB ฝัง texture พร้อมเปิดกลับตรวจและเรนเดอร์สามมุม",
    "preset": "ref-white-lotus.json",
    "triangles": 34928,
    "islands": 2486,
    "resolution": 2048,
    "bytes": 24294432,
    "sha256": "700f991c8c961880740e0a8fe65bfd8db2f3ea68d58dcf73592a024b2b69a5d9"
  },
  {
    "id": "clay",
    "family": "clay_bowl",
    "title": "กระทงดินเผา",
    "subtitle": "ภาชนะกลวง · ผนังหนา · ผิวดินด้าน",
    "prompt": "ใช้ $thai-krathong-3d สร้างกระทงดินเผาตาม preset clay_bowl ให้เห็นช่องภายใน ผนังและขอบภาชนะจริง ผิวสีดินเผาไม่เป็นโลหะ มีเทียนและธูป ส่งออก GLB สำหรับเว็บ พร้อม baked PBR, UV QA และรายงานตรวจไฟล์หลัง reimport",
    "preset": "ref-clay-bowl.json",
    "triangles": 6064,
    "islands": 85,
    "resolution": 1024,
    "bytes": 4552784,
    "sha256": "e8ed7251770fa6ebd632f1e9f404385fe88ca07d4b00088f8c6408e360aa9783"
  }
];
let selected = cases[0];
let view = "iso";
const views = {iso:"มุมเฉียง",front:"ด้านหน้า",top:"ด้านบน"};
const number = new Intl.NumberFormat("th-TH");
const size = new Intl.NumberFormat("th-TH", {maximumFractionDigits:2});
const image = document.getElementById("preview");
const error = document.getElementById("image-error");
function render(){
  error.hidden = true;
  image.src = `results/${selected.id}/${view}.png`;
  image.alt = `${selected.title} ${views[view]} เรนเดอร์จาก GLB`;
  document.getElementById("view-caption").textContent = `${views[view]}จาก GLB`;
  document.getElementById("model-title").textContent = selected.title;
  document.getElementById("model-subtitle").textContent = selected.subtitle;
  document.getElementById("triangles").textContent = number.format(selected.triangles);
  document.getElementById("islands").textContent = number.format(selected.islands);
  document.getElementById("resolution").textContent = number.format(selected.resolution) + " px";
  const download = document.getElementById("model-download");
  download.href = `results/${selected.id}/krathong.glb`;
  download.download = `krathong-${selected.id}.glb`;
  download.textContent = `ดาวน์โหลด GLB · ${size.format(selected.bytes/1000000)} MB`;
  document.getElementById("proof-link").href = `results/${selected.id}/verification.json`;
  document.getElementById("preset-link").href = `../../assets/${selected.preset}`;
  document.getElementById("prompt").value = selected.prompt;
  document.getElementById("copy-feedback").textContent = "";
  document.querySelectorAll("[data-case]").forEach(button => button.setAttribute("aria-pressed",String(button.dataset.case === selected.id)));
  document.querySelectorAll("[data-view]").forEach(button => button.setAttribute("aria-pressed",String(button.dataset.view === view)));
}
image.addEventListener("error",()=>{error.hidden=false;});
image.addEventListener("load",()=>{error.hidden=true;});
document.querySelectorAll("[data-case]").forEach(button=>button.addEventListener("click",()=>{
  selected=cases.find(item=>item.id===button.dataset.case);render();
}));
document.querySelectorAll("[data-view]").forEach(button=>button.addEventListener("click",()=>{view=button.dataset.view;render();}));
document.getElementById("copy-prompt").addEventListener("click",async()=>{
  const prompt=document.getElementById("prompt");
  const feedback=document.getElementById("copy-feedback");
  try{
    if(!navigator.clipboard) throw new Error("Clipboard unavailable");
    await navigator.clipboard.writeText(prompt.value);
    feedback.textContent="คัดลอก prompt แล้ว พร้อมนำไปใช้กับ skill";
  }catch{
    prompt.focus();prompt.select();
    feedback.textContent="เลือกข้อความให้แล้ว กด Ctrl+C หรือ Command+C เพื่อคัดลอก";
  }
});
render();
