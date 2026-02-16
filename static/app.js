const btn = document.getElementById("btn");
const txt = document.getElementById("txt");
const out = document.getElementById("out");

btn.addEventListener("click", async () => {
  out.textContent = "جارٍ التحليل...";
  const res = await fetch("/api/analyze", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({ text: txt.value })
  });
  const data = await res.json();
  out.textContent = JSON.stringify(data, null, 2);
});
