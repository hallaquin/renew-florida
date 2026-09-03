/* ════════════════════════════════════════════════════════════
   Aplicación de Crédito — Renew Florida
   Máscaras de input, firma por canvas, validación y envío a la API propia.
════════════════════════════════════════════════════════════ */

function showToast(msg, type = "success", duration = 5000) {
    const toast = document.getElementById("toast");
    const text = document.getElementById("toast-message");
    text.textContent = msg;
    toast.className = type;
    toast.classList.add("show");
    clearTimeout(toast._hideTimer);
    toast._hideTimer = setTimeout(() => toast.classList.remove("show"), duration);
}

function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    input.type = input.type === "password" ? "text" : "password";
}

/* ── Máscaras ── */
function initDateMasks() {
    document.querySelectorAll(".date-mask").forEach((input) => {
        input.addEventListener("input", () => {
            let digits = input.value.replace(/\D/g, "").slice(0, 8);
            let out = digits;
            if (digits.length > 4) out = `${digits.slice(0, 2)}/${digits.slice(2, 4)}/${digits.slice(4)}`;
            else if (digits.length > 2) out = `${digits.slice(0, 2)}/${digits.slice(2)}`;
            input.value = out;
        });
    });
}

function initCurrencyMasks() {
    document.querySelectorAll(".currency-mask").forEach((input) => {
        input.addEventListener("input", () => {
            let digits = input.value.replace(/\D/g, "");
            if (!digits) { input.value = ""; return; }
            const number = (parseInt(digits, 10) / 100).toFixed(2);
            input.value = `$ ${Number(number).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        });
    });
}

/* ── Firma por canvas ── */
function createSignaturePad(canvasId, clearBtnId, placeholderId) {
    const canvas = document.getElementById(canvasId);
    const placeholder = document.getElementById(placeholderId);
    const clearBtn = document.getElementById(clearBtnId);
    const ctx = canvas.getContext("2d");
    ctx.strokeStyle = "#0f172a";
    ctx.lineWidth = 2.2;
    ctx.lineCap = "round";

    let drawing = false;
    let hasDrawn = false;

    function getPos(evt) {
        const rect = canvas.getBoundingClientRect();
        const point = evt.touches ? evt.touches[0] : evt;
        return {
            x: (point.clientX - rect.left) * (canvas.width / rect.width),
            y: (point.clientY - rect.top) * (canvas.height / rect.height),
        };
    }

    function start(evt) {
        evt.preventDefault();
        drawing = true;
        hasDrawn = true;
        if (placeholder) placeholder.style.display = "none";
        const pos = getPos(evt);
        ctx.beginPath();
        ctx.moveTo(pos.x, pos.y);
    }

    function move(evt) {
        if (!drawing) return;
        evt.preventDefault();
        const pos = getPos(evt);
        ctx.lineTo(pos.x, pos.y);
        ctx.stroke();
    }

    function end() { drawing = false; }

    canvas.addEventListener("mousedown", start);
    canvas.addEventListener("mousemove", move);
    window.addEventListener("mouseup", end);
    canvas.addEventListener("touchstart", start, { passive: false });
    canvas.addEventListener("touchmove", move, { passive: false });
    canvas.addEventListener("touchend", end);

    function clear() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        hasDrawn = false;
        if (placeholder) placeholder.style.display = "flex";
    }

    if (clearBtn) clearBtn.addEventListener("click", clear);

    return {
        isEmpty: () => !hasDrawn,
        clear,
        toBlob: () => new Promise((resolve) => canvas.toBlob(resolve, "image/png")),
    };
}

/* ── Foto de identificación: previsualización ── */
function handleFileSelect(input, previewId) {
    const preview = document.getElementById(previewId);
    const file = input.files[0];
    preview.innerHTML = "";
    if (!file) return;
    const img = document.createElement("img");
    img.src = URL.createObjectURL(file);
    preview.appendChild(img);
}

/* ── Envío del formulario ── */
async function handleCreditFormSubmit(e, sigApplicant, sigCoApplicant) {
    e.preventDefault();
    const form = e.target;

    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    if (sigApplicant.isEmpty()) {
        showToast("Falta la firma del aplicante principal.", "error");
        return;
    }

    const btn = form.querySelector(".btn-submit");
    const btnText = btn.querySelector(".btn-text");
    const originalLabel = btnText.textContent;
    btn.disabled = true;
    btnText.textContent = "Enviando...";
    showToast("Enviando Aplicación de Crédito…", "success", 8000);

    try {
        const formData = new FormData(form);

        const sigAppBlob = await sigApplicant.toBlob();
        formData.append("signatureApplicant", sigAppBlob, "signature_applicant.png");

        if (!sigCoApplicant.isEmpty()) {
            const sigCoBlob = await sigCoApplicant.toBlob();
            formData.append("signatureCoApplicant", sigCoBlob, "signature_coapplicant.png");
        }

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000);

        const response = await fetch(`${API_BASE_URL}/api/credit-applications`, {
            method: "POST",
            body: formData,
            signal: controller.signal,
        });
        clearTimeout(timeoutId);

        if (!response.ok) {
            const body = await response.json().catch(() => ({}));
            throw new Error(body.error || `Error ${response.status}`);
        }

        showToast("¡Aplicación enviada exitosamente! Nos pondremos en contacto pronto.", "success");
        form.reset();
        sigApplicant.clear();
        sigCoApplicant.clear();
        document.querySelectorAll(".file-preview").forEach((el) => (el.innerHTML = ""));
    } catch (err) {
        const msg = err.name === "AbortError"
            ? "La conexión tardó demasiado. Revisa tu internet e intenta de nuevo."
            : `No se pudo enviar la aplicación. (${err.message})`;
        showToast(msg, "error", 8000);
    } finally {
        btn.disabled = false;
        btnText.textContent = originalLabel;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    initDateMasks();
    initCurrencyMasks();

    const sigApplicant = createSignaturePad("firma-aplicante", "btn-limpiar-firma-aplicante", "placeholder-aplicante");
    const sigCoApplicant = createSignaturePad("firma-co-aplicante", "btn-limpiar-firma-co-aplicante", "placeholder-co-aplicante");

    const form = document.getElementById("form-credit");
    form.addEventListener("submit", (e) => handleCreditFormSubmit(e, sigApplicant, sigCoApplicant));
});
