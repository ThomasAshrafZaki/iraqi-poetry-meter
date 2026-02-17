const input = document.getElementById("poemInput");
const analyzeBtn = document.getElementById("analyzeBtn");
const clearBtn = document.getElementById("clearBtn");
const resultBox = document.getElementById("result");

function showResult(html) {
  resultBox.innerHTML = html;
  resultBox.classList.remove("hidden");
}

function hideResult() {
  resultBox.classList.add("hidden");
  resultBox.innerHTML = "";
}

clearBtn.addEventListener("click", () => {
  input.value = "";
  hideResult();
  input.focus();
});

analyzeBtn.addEventListener("click", async () => {
  const text = (input.value || "").trim();
  if (!text) {
    showResult(`<b>اكتب بيت أولاً.</b>`);
    return;
  }

  analyzeBtn.disabled = true;
  analyzeBtn.textContent = "جاري التحليل...";

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ text })
    });

    const data = await res.json();

    if (!data.ok) {
      showResult(`<b>خطأ:</b> ${data.message || "غير معروف"}`);
      return;
    }

    if (!data.matched) {
      showResult(`
        <div><b>غير مطابق</b></div>
        <div>الثقة: <b>${data.confidence}</b></div>
        <div style="margin-top:8px;color:#555">${data.message || ""}</div>
      `);
      return;
    }

    showResult(`
      <div><b>الوزن:</b> ${data.weight}</div>
      <div><b>التفعيلات:</b> ${data.taf3eelat || "-"}</div>
      <div><b>الثقة:</b> ${data.confidence}</div>
      <hr />
      <div><b>أقرب مثال:</b></div>
      <div style="color:#333">${data.closest_example}</div>
    `);

  } catch (e) {
    showResult(`<b>حدث خطأ في الاتصال بالسيرفر.</b><br/>${String(e)}`);
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = "تحليل الوزن";
  }
});
